namespace TranscribeAi.Services.Implementations;

/// <summary>
/// Orchestrates transcription: delegates to the configured ITranscriptionProvider.
/// </summary>
public sealed class TranscriptionService : ITranscriptionService
{
    private readonly ITranscriptionProvider _provider;
    private readonly ILogger<TranscriptionService> _logger;

    public TranscriptionService(ITranscriptionProvider provider, ILogger<TranscriptionService> logger)
    {
        _provider = provider;
        _logger = logger;
    }

    public async Task<TranscriptionResultDto> TranscribeFileAsync(string filePath,
        string? language = null, CancellationToken ct = default)
    {
        _logger.LogInformation("Starting transcription for {FilePath}", filePath);

        var result = await _provider.TranscribeAsync(filePath, language, ct);

        _logger.LogInformation(
            "Transcription complete: {SegmentCount} segments, {Duration}s audio, {Confidence} confidence",
            result.Segments.Count, result.DurationSeconds, result.OverallConfidence);

        return result;
    }
}
