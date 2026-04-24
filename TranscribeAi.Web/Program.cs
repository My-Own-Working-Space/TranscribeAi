using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.RateLimiting;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Diagnostics.HealthChecks;
using Serilog;
using System.Threading.RateLimiting;
using TranscribeAi.DataAccessLayer.Data;
using TranscribeAi.Web.Configuration;
using TranscribeAi.Web.Hubs;
using TranscribeAi.Web.Middleware;
using TranscribeAi.Worker.Workers;

var builder = WebApplication.CreateBuilder(args);

// ── Serilog ──
Log.Logger = new LoggerConfiguration()
    .ReadFrom.Configuration(builder.Configuration)
    .Enrich.FromLogContext()
    .WriteTo.Console(outputTemplate: "[{Timestamp:HH:mm:ss} {Level:u3}] {Message:lj}{NewLine}{Exception}")
    .WriteTo.File("logs/transcribeai-.log", rollingInterval: RollingInterval.Day, retainedFileCountLimit: 14)
    .CreateLogger();

builder.Host.UseSerilog();

// ── Database + Identity + Application Services ──
// Map legacy DATABASE_URL if present (Supabase/Render style)
var databaseUrl = builder.Configuration["DATABASE_URL"];
var connectionString = !string.IsNullOrWhiteSpace(databaseUrl) 
                      ? databaseUrl 
                      : builder.Configuration.GetConnectionString("DefaultConnection");

if (!string.IsNullOrEmpty(connectionString) && connectionString.StartsWith("postgres://"))
{
    // Convert postgres://user:pass@host:port/db to Npgsql format
    var uri = new Uri(connectionString);
    var userInfo = uri.UserInfo.Split(':');
    connectionString = $"Host={uri.Host};Port={uri.Port};Database={uri.AbsolutePath.TrimStart('/')};Username={userInfo[0]};Password={userInfo[1]};SSL Mode=Require;Trust Server Certificate=true";
}

builder.Services.AddDatabase(builder.Configuration, connectionString);
builder.Services.AddIdentityServices();

// Map legacy GROQ_API_KEY
var groqApiKey = builder.Configuration["GROQ_API_KEY"] ?? builder.Configuration["Groq:ApiKey"];
builder.Services.AddApplicationServices(builder.Configuration, groqApiKey);

// ── Razor Pages + SignalR ──
builder.Services.AddRazorPages(options =>
{
    options.Conventions.AuthorizeFolder("/Jobs");
    options.Conventions.AuthorizeFolder("/Admin", "AdminPolicy");
    options.Conventions.AllowAnonymousToPage("/Index");
    options.Conventions.AllowAnonymousToPage("/Account/Login");
    options.Conventions.AllowAnonymousToPage("/Account/Register");
    options.Conventions.AllowAnonymousToPage("/Privacy");
    options.Conventions.AllowAnonymousToPage("/Error");
});

builder.Services.AddSignalR();

// ── Authorization Policies ──
builder.Services.AddAuthorizationBuilder()
    .AddPolicy("AdminPolicy", policy => policy.RequireRole("Admin"));

// ── Rate Limiting ──
builder.Services.AddRateLimiter(options =>
{
    options.RejectionStatusCode = StatusCodes.Status429TooManyRequests;

    options.AddFixedWindowLimiter("UploadLimit", opt =>
    {
        opt.PermitLimit = 10;
        opt.Window = TimeSpan.FromMinutes(1);
        opt.QueueLimit = 2;
        opt.QueueProcessingOrder = QueueProcessingOrder.OldestFirst;
    });

    options.AddFixedWindowLimiter("ApiLimit", opt =>
    {
        opt.PermitLimit = 60;
        opt.Window = TimeSpan.FromMinutes(1);
    });
});

// ── Health Checks ──
builder.Services.AddHealthChecks()
    .AddCheck("Self", () => HealthCheckResult.Healthy());

// ── Background Worker (in-process hosted service) ──
builder.Services.AddHostedService<TranscriptionWorker>();

// ── Antiforgery ──
builder.Services.AddAntiforgery(options =>
{
    options.HeaderName = "X-CSRF-TOKEN";
});

// ── Startup & Migration ──
var port = Environment.GetEnvironmentVariable("PORT") ?? "10000";
builder.WebHost.UseUrls($"http://*:{port}");

var app = builder.Build();

if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Error");
    app.UseHsts();
}

app.UseMiddleware<SecurityHeadersMiddleware>();
app.UseMiddleware<RequestLoggingMiddleware>();

app.UseStaticFiles();
app.UseRouting();
app.UseRateLimiter();

app.UseAuthentication();
app.UseAuthorization();

app.MapRazorPages();
app.MapHub<TranscriptionHub>("/hubs/transcription");
app.MapHealthChecks("/health");

// Run migration in a BACKGROUND task to unblock Render port scan
_ = Task.Run(async () =>
{
    using (var scope = app.Services.CreateScope())
    {
        var services = scope.ServiceProvider;
        var logger = services.GetRequiredService<ILogger<Program>>();
        
        try
        {
            var db = services.GetRequiredService<TranscribeDbContext>();
            logger.LogInformation("Background: Starting database migration at {Time}", DateTime.UtcNow);
            await db.Database.MigrateAsync();
            logger.LogInformation("Background: Database migration completed.");

            // Seeds
            var roleManager = services.GetRequiredService<RoleManager<IdentityRole>>();
            foreach (var role in new[] { "User", "Admin" })
            {
                if (!await roleManager.RoleExistsAsync(role))
                    await roleManager.CreateAsync(new IdentityRole(role));
            }

            var userManager = services.GetRequiredService<UserManager<ApplicationUser>>();
            var testUser = await userManager.FindByEmailAsync("user@example.com");
            if (testUser == null)
            {
                testUser = new ApplicationUser { UserName = "user@example.com", Email = "user@example.com", EmailConfirmed = true, FullName = "System Test User" };
                await userManager.CreateAsync(testUser, "Password123!");
                await userManager.AddToRoleAsync(testUser, "User");
            }
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "Background: An error occurred during startup migration/seeding.");
        }
    }
});

app.Run();
