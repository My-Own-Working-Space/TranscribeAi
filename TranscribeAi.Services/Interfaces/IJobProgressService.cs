namespace TranscribeAi.Services.Interfaces;

/// <summary>
/// Interface for reporting transcription job progress.
/// Decouples the Worker from the SignalR Hub.
/// </summary>
public interface IJobProgressService
{
    Task NotifyProgressAsync(Guid jobId, int percent, string step, string detail, CancellationToken ct = default);
    Task NotifyCompletionAsync(Guid jobId, CancellationToken ct = default);
    Task NotifyFailureAsync(Guid jobId, string error, CancellationToken ct = default);
}
