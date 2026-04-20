using Microsoft.AspNetCore.SignalR;
using TranscribeAi.Services.Interfaces;
using TranscribeAi.Web.Hubs;

namespace TranscribeAi.Web.Services;

/// <summary>
/// Implementation of IJobProgressService that uses SignalR to notify clients.
/// </summary>
public sealed class SignalRJobProgressService : IJobProgressService
{
    private readonly IHubContext<TranscriptionHub> _hubContext;
    private readonly ILogger<SignalRJobProgressService> _logger;

    public SignalRJobProgressService(IHubContext<TranscriptionHub> hubContext, ILogger<SignalRJobProgressService> logger)
    {
        _hubContext = hubContext;
        _logger = logger;
    }

    public async Task NotifyProgressAsync(Guid jobId, int percent, string step, string detail, CancellationToken ct = default)
    {
        _logger.LogDebug("Sending SignalR progress for {JobId}: {Percent}%", jobId, percent);
        await _hubContext.Clients.Group($"job-{jobId}")
            .SendAsync("OnProgressUpdate", jobId, percent, step, detail, ct);
    }

    public async Task NotifyCompletionAsync(Guid jobId, CancellationToken ct = default)
    {
        _logger.LogInformation("Sending SignalR completion for {JobId}", jobId);
        await _hubContext.Clients.Group($"job-{jobId}")
            .SendAsync("OnJobCompleted", jobId, ct);
    }

    public async Task NotifyFailureAsync(Guid jobId, string error, CancellationToken ct = default)
    {
        _logger.LogWarning("Sending SignalR failure for {JobId}: {Error}", jobId, error);
        await _hubContext.Clients.Group($"job-{jobId}")
            .SendAsync("OnJobFailed", jobId, error, ct);
    }
}
