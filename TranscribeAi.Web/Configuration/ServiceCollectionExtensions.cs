using System.Net.Http.Headers;
using Microsoft.EntityFrameworkCore;
using Polly;
using Polly.Extensions.Http;
using TranscribeAi.DataAccessLayer.Data;
using TranscribeAi.DataAccessLayer.Repositories;
using TranscribeAi.DataAccessLayer.Repositories.Interfaces;
using TranscribeAi.Services.Implementations;
using TranscribeAi.Services.Interfaces;
using TranscribeAi.Web.Services;

namespace TranscribeAi.Web.Configuration;

/// <summary>
/// Extension methods for clean DI registration — keeps Program.cs readable.
/// </summary>
public static class ServiceCollectionExtensions
{
    /// <summary>Register EF Core with SQLite (dev) or PostgreSQL (prod).</summary>
    public static IServiceCollection AddDatabase(this IServiceCollection services, IConfiguration config, string? connectionString = null)
    {
        connectionString ??= config.GetConnectionString("DefaultConnection")
            ?? "Data Source=transcribe.db";

        if (connectionString.Contains("Host=") || connectionString.Contains("postgresql"))
        {
            services.AddDbContext<TranscribeDbContext>(options =>
                options.UseNpgsql(connectionString, npgsql =>
                    npgsql.MigrationsAssembly("TranscribeAi.DataAccessLayer")));
        }
        else
        {
            services.AddDbContext<TranscribeDbContext>(options =>
                options.UseSqlite(connectionString, sqlite =>
                    sqlite.MigrationsAssembly("TranscribeAi.DataAccessLayer")));
        }

        return services;
    }

    /// <summary>Register ASP.NET Core Identity with role support.</summary>
    public static IServiceCollection AddIdentityServices(this IServiceCollection services)
    {
        services.AddIdentity<ApplicationUser, IdentityRole>(options =>
            {
                options.Password.RequireDigit = true;
                options.Password.RequireLowercase = true;
                options.Password.RequireUppercase = true;
                options.Password.RequireNonAlphanumeric = false;
                options.Password.RequiredLength = 8;

                options.Lockout.DefaultLockoutTimeSpan = TimeSpan.FromMinutes(5);
                options.Lockout.MaxFailedAccessAttempts = 5;

                options.User.RequireUniqueEmail = true;
            })
            .AddEntityFrameworkStores<TranscribeDbContext>()
            .AddDefaultTokenProviders()
            .AddClaimsPrincipalFactory<AppUserClaimsPrincipalFactory>();

        services.Configure<IdentityOptions>(options =>
        {
            options.SignIn.RequireConfirmedAccount = true;
        });

        services.ConfigureApplicationCookie(options =>
        {
            options.LoginPath = "/Account/Login";
            options.LogoutPath = "/Account/Logout";
            options.AccessDeniedPath = "/Account/Login";
            options.ExpireTimeSpan = TimeSpan.FromDays(7);
            options.SlidingExpiration = true;
            options.Cookie.HttpOnly = true;
            options.Cookie.SameSite = SameSiteMode.Lax;
            options.Cookie.SecurePolicy = CookieSecurePolicy.SameAsRequest;
        });

        return services;
    }

    /// <summary>Register all repository and service layer dependencies.</summary>
    public static IServiceCollection AddApplicationServices(this IServiceCollection services,
        IConfiguration config, string? groqApiKey = null)
    {
        // Options
        services.Configure<TranscribeAiOptions>(config.GetSection(TranscribeAiOptions.SectionName));
        services.Configure<GroqOptions>(config.GetSection(GroqOptions.SectionName));

        // Repositories
        services.AddScoped<IUnitOfWork, UnitOfWork>();

        // HTTP Client for Groq API with retry policy
        groqApiKey ??= config.GetSection("Groq:ApiKey").Value ?? "";
        services.AddHttpClient("GroqApi", client =>
        {
            client.DefaultRequestHeaders.Authorization =
                new AuthenticationHeaderValue("Bearer", groqApiKey);
            client.Timeout = TimeSpan.FromMinutes(10);
        })
        .AddPolicyHandler(GetRetryPolicy());

        // Services
        services.AddSingleton<IJobQueueService, JobQueueService>();
        services.AddScoped<ILlmService, GroqLlmService>();
        services.AddScoped<ITranscriptionProvider, GroqTranscriptionProvider>();
        services.AddScoped<ITranscriptionService, TranscriptionService>();
        services.AddScoped<ISummaryService, SummaryService>();
        services.AddScoped<IChatService, ChatService>();
        services.AddScoped<IActionService, ActionService>();
        services.AddScoped<IExportService, ExportService>();
        services.AddScoped<IAuditService, AuditService>();
        services.AddSingleton<IJobProgressService, SignalRJobProgressService>();

        return services;
    }

    private static IAsyncPolicy<HttpResponseMessage> GetRetryPolicy()
    {
        return HttpPolicyExtensions
            .HandleTransientHttpError()
            .WaitAndRetryAsync(3, retryAttempt =>
                TimeSpan.FromSeconds(Math.Pow(2, retryAttempt)));
    }
}
