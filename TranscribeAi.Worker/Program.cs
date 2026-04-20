using Microsoft.EntityFrameworkCore;
using Serilog;
using TranscribeAi.DataAccessLayer.Data;
using TranscribeAi.DataAccessLayer.Repositories;
using TranscribeAi.Services.Implementations;
using TranscribeAi.Worker.Workers;
using System.Net.Http.Headers;
using Polly;
using Polly.Extensions.Http;
using TranscribeAi.DataAccessLayer.Repositories.Interfaces;

// ═══════════════════════════════════════════════════════════════
//  TranscribeAI — Background Worker Service Composition Root
// ═══════════════════════════════════════════════════════════════

var builder = Host.CreateApplicationBuilder(args);

// ── Serilog ──
builder.Services.AddSerilog((services, loggerConfiguration) => loggerConfiguration
    .ReadFrom.Configuration(builder.Configuration)
    .Enrich.FromLogContext()
    .WriteTo.Console(outputTemplate: "[{Timestamp:HH:mm:ss} {Level:u3}] (Worker) {Message:lj}{NewLine}{Exception}")
    .WriteTo.File("logs/worker-.log", rollingInterval: RollingInterval.Day));

// ── Database ──
var connectionString = builder.Configuration.GetConnectionString("DefaultConnection") 
    ?? "Data Source=transcribe.db";

if (connectionString.Contains("Host=") || connectionString.Contains("postgresql"))
{
    builder.Services.AddDbContext<TranscribeDbContext>(options =>
        options.UseNpgsql(connectionString, npgsql =>
            npgsql.MigrationsAssembly("TranscribeAi.DataAccessLayer")));
}
else
{
    builder.Services.AddDbContext<TranscribeDbContext>(options =>
        options.UseSqlite(connectionString, sqlite =>
            sqlite.MigrationsAssembly("TranscribeAi.DataAccessLayer")));
}

// ── Common Services ──
builder.Services.Configure<TranscribeAiOptions>(builder.Configuration.GetSection(TranscribeAiOptions.SectionName));
builder.Services.Configure<GroqOptions>(builder.Configuration.GetSection(GroqOptions.SectionName));

builder.Services.AddScoped<IUnitOfWork, UnitOfWork>();

// HTTP Client for Groq API
var groqApiKey = builder.Configuration.GetSection("Groq:ApiKey").Value ?? "";
builder.Services.AddHttpClient("GroqApi", client =>
{
    client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", groqApiKey);
    client.Timeout = TimeSpan.FromMinutes(10);
})
.AddPolicyHandler(HttpPolicyExtensions
    .HandleTransientHttpError()
    .WaitAndRetryAsync(3, retryAttempt => TimeSpan.FromSeconds(Math.Pow(2, retryAttempt))));

// Business Logic
builder.Services.AddScoped<ILlmService, GroqLlmService>();
builder.Services.AddScoped<ITranscriptionProvider, GroqTranscriptionProvider>();
builder.Services.AddScoped<ITranscriptionService, TranscriptionService>();
builder.Services.AddScoped<ISummaryService, SummaryService>();
builder.Services.AddScoped<IChatService, ChatService>();
builder.Services.AddScoped<IActionService, ActionService>();

builder.Services.AddSingleton<IJobQueueService, JobQueueService>();
builder.Services.AddHostedService<TranscriptionWorker>();

var host = builder.Build();
host.Run();
