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

// ═══════════════════════════════════════════════════════════════
//  TranscribeAI — ASP.NET Core 9 Razor Pages Composition Root
// ═══════════════════════════════════════════════════════════════

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
builder.Services.AddDatabase(builder.Configuration);
builder.Services.AddIdentityServices();
builder.Services.AddApplicationServices(builder.Configuration);

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

var app = builder.Build();

// ═══════════════════════════════════════════════════════════════
//  Middleware Pipeline
// ═══════════════════════════════════════════════════════════════

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

// ═══════════════════════════════════════════════════════════════
//  Database Initialization + Seed Admin
// ═══════════════════════════════════════════════════════════════

using (var scope = app.Services.CreateScope())
{
    var db = scope.ServiceProvider.GetRequiredService<TranscribeDbContext>();
    await db.Database.EnsureCreatedAsync();

    // Seed roles
    var roleManager = scope.ServiceProvider.GetRequiredService<RoleManager<IdentityRole>>();
    foreach (var role in new[] { "User", "Admin" })
    {
        if (!await roleManager.RoleExistsAsync(role))
            await roleManager.CreateAsync(new IdentityRole(role));
    }

    Log.Information("🚀 TranscribeAI v3.0.0 ready");
}

app.Run();
