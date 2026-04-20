namespace TranscribeAi.Worker.Workers;

/// <summary>
/// Background worker service that processes transcription jobs from the internal channel queue.
/// Runs as a long-running HostedService.
/// </summary>
public sealed class TranscriptionWorker : BackgroundService
{
    private readonly IJobQueueService _queue;
    private readonly IServiceProvider _serviceProvider;
    private readonly IJobProgressService _progress;
    private readonly ILogger<TranscriptionWorker> _logger;

    public TranscriptionWorker(
        IJobQueueService queue,
        IServiceProvider serviceProvider,
        IJobProgressService progress,
        ILogger<TranscriptionWorker> logger)
    {
        _queue = queue;
        _serviceProvider = serviceProvider;
        _progress = progress;
        _logger = logger;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        _logger.LogInformation("TranscriptionWorker started. Waiting for jobs...");

        while (!stoppingToken.IsCancellationRequested)
        {
            try
            {
                var request = await _queue.DequeueAsync(stoppingToken);
                _logger.LogInformation("Dequeued job {JobId} for user {UserId}", request.JobId, request.UserId);

                await ProcessJobAsync(request, stoppingToken);
            }
            catch (OperationCanceledException)
            {
                break;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error occurred while processing transcription queue");
            }
        }

        _logger.LogInformation("TranscriptionWorker shutting down.");
    }

    private async Task ProcessJobAsync(TranscriptionJobRequest request, CancellationToken ct)
    {
        using var scope = _serviceProvider.CreateScope();
        var uow = scope.ServiceProvider.GetRequiredService<IUnitOfWork>();
        var transcription = scope.ServiceProvider.GetRequiredService<ITranscriptionService>();
        var summary = scope.ServiceProvider.GetRequiredService<ISummaryService>();
        var action = scope.ServiceProvider.GetRequiredService<IActionService>();

        var jobId = request.JobId;

        try
        {
            var job = await uow.TranscriptionJobs.GetByIdAsync(jobId, ct);
            if (job == null) return;

            job.Status = JobStatus.Processing;
            await uow.SaveChangesAsync(ct);
            await _progress.NotifyProgressAsync(jobId, 5, "Initializing", "Preparing high-performance AI models...", ct);

            // ── STEP 1: Transcription ──
            await _progress.NotifyProgressAsync(jobId, 15, "Transcribing", "Analyzing audio with Whisper Turbo...", ct);
            var result = await transcription.TranscribeFileAsync(request.FilePath, request.Language, ct);

            job.Transcript = result.FullText;
            job.SegmentsJson = JsonSerializer.Serialize(result.Segments);
            job.OverallConfidence = result.OverallConfidence;
            job.DurationSeconds = result.DurationSeconds;
            job.ProcessingTimeSeconds = result.ProcessingTimeSeconds;
            job.LanguageDetected = result.LanguageDetected;
            job.WhisperModel = result.Model;
            
            await uow.SaveChangesAsync(ct);
            await _progress.NotifyProgressAsync(jobId, 60, "Post-processing", "Cleaning up segments and timestamps...", ct);

            // ── STEP 2: Summary ──
            await _progress.NotifyProgressAsync(jobId, 75, "AI Summarization", "Generating multi-agent intelligence summary...", ct);
            await summary.GenerateSummaryAsync(jobId, result.LanguageDetected, ct);

            // ── STEP 3: Action Items ──
            if (request.Mode == JobMode.Meeting)
            {
                await _progress.NotifyProgressAsync(jobId, 90, "Extracting Actions", "Identifying key tasks and assignees...", ct);
                await action.ExtractActionsAsync(jobId, ct);
            }

            // ── FINAL: Complete ──
            job.Status = JobStatus.Completed;
            job.CompletedAt = DateTime.UtcNow;
            await uow.SaveChangesAsync(ct);

            await _progress.NotifyCompletionAsync(jobId, ct);
            _logger.LogInformation("Successfully completed job {JobId}", jobId);

            if (File.Exists(request.FilePath)) File.Delete(request.FilePath);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to process job {JobId}", jobId);
            
            var job = await uow.TranscriptionJobs.GetByIdAsync(jobId, ct);
            if (job != null)
            {
                job.Status = JobStatus.Failed;
                job.Error = ex.Message;
                await uow.SaveChangesAsync(ct);
            }

            await _progress.NotifyFailureAsync(jobId, ex.Message, ct);
        }
    }
}
