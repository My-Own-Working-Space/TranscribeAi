using Microsoft.AspNetCore.SignalR;

namespace TranscribeAi.Web.Hubs;

/// <summary>
/// SignalR Hub for real-time transcription job progress updates.
/// Clients join a job-specific group and receive progress events.
/// </summary>
[Authorize]
public sealed class TranscriptionHub : Hub
{
    private readonly ILogger<TranscriptionHub> _logger;

    public TranscriptionHub(ILogger<TranscriptionHub> logger)
    {
        _logger = logger;
    }

    /// <summary>
    /// Client joins a group to receive progress updates for a specific job.
    /// </summary>
    public async Task JoinJobGroup(string jobId)
    {
        await Groups.AddToGroupAsync(Context.ConnectionId, $"job-{jobId}");
        _logger.LogDebug("Client {ConnectionId} joined job group {JobId}",
            Context.ConnectionId, jobId);
    }

    /// <summary>
    /// Client leaves a job group when navigating away.
    /// </summary>
    public async Task LeaveJobGroup(string jobId)
    {
        await Groups.RemoveFromGroupAsync(Context.ConnectionId, $"job-{jobId}");
    }

    public override async Task OnConnectedAsync()
    {
        _logger.LogDebug("SignalR client connected: {ConnectionId}", Context.ConnectionId);
        await base.OnConnectedAsync();
    }

    public override async Task OnDisconnectedAsync(Exception? exception)
    {
        _logger.LogDebug("SignalR client disconnected: {ConnectionId}", Context.ConnectionId);
        await base.OnDisconnectedAsync(exception);
    }
}
