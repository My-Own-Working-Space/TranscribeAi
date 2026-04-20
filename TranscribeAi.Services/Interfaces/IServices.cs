namespace TranscribeAi.Services.Interfaces;

/// <summary>
/// Abstraction over LLM providers (Groq, OpenAI, etc.) for chat completions.
/// </summary>
public interface ILlmService
{
    /// <summary>Single-turn chat completion.</summary>
    Task<string> ChatAsync(string systemPrompt, string userMessage,
        float temperature = 0.3f, int maxTokens = 4096, CancellationToken ct = default);

    /// <summary>Multi-turn chat with message history.</summary>
    Task<string> ChatWithHistoryAsync(string systemPrompt, List<ChatMessageDto> messages,
        float temperature = 0.3f, int maxTokens = 2048, CancellationToken ct = default);

    /// <summary>Parse a JSON string from LLM response, handling markdown fences.</summary>
    JsonDocument? ParseJsonResponse(string text);
}

/// <summary>
/// Abstraction over speech-to-text providers for pluggable transcription engines.
/// </summary>
public interface ITranscriptionProvider
{
    /// <summary>Transcribe an audio file and return structured results.</summary>
    Task<TranscriptionResultDto> TranscribeAsync(string filePath, string? language = null,
        CancellationToken ct = default);
}

/// <summary>
/// Orchestrates the transcription workflow: validation, engine call, persistence.
/// </summary>
public interface ITranscriptionService
{
    Task<TranscriptionResultDto> TranscribeFileAsync(string filePath, string? language = null,
        CancellationToken ct = default);
}

/// <summary>
/// Multi-agent AI summary pipeline: Generate → Review → Refine.
/// </summary>
public interface ISummaryService
{
    Task<SummaryDto> GenerateSummaryAsync(Guid jobId, string? language = null,
        CancellationToken ct = default);
    Task<SummaryDto?> GetSummaryByJobIdAsync(Guid jobId, CancellationToken ct = default);
}

/// <summary>
/// AI-powered Q&A over transcripts with conversation history.
/// </summary>
public interface IChatService
{
    Task<ChatResponseDto> AskQuestionAsync(Guid jobId, string userId, string question,
        CancellationToken ct = default);
    Task<IReadOnlyList<ChatMessageDto>> GetHistoryAsync(Guid jobId, string userId,
        CancellationToken ct = default);
    Task ClearHistoryAsync(Guid jobId, string userId, CancellationToken ct = default);
}

/// <summary>
/// Extract action items from meeting transcripts via LLM.
/// </summary>
public interface IActionService
{
    Task<IReadOnlyList<ActionItemDto>> ExtractActionsAsync(Guid jobId,
        CancellationToken ct = default);
    Task<ActionItemDto> UpdateActionAsync(Guid actionId, bool? isCompleted, string? priority,
        CancellationToken ct = default);
}

/// <summary>
/// Export transcripts in various formats (TXT, SRT, DOCX).
/// </summary>
public interface IExportService
{
    Task<byte[]> ExportAsTxtAsync(Guid jobId, CancellationToken ct = default);
    Task<byte[]> ExportAsSrtAsync(Guid jobId, CancellationToken ct = default);
    Task<byte[]> ExportAsDocxAsync(Guid jobId, CancellationToken ct = default);
}

/// <summary>
/// Security audit logging service.
/// </summary>
public interface IAuditService
{
    Task LogAsync(string userId, AuditAction action, string? details = null,
        string? ipAddress = null, string? userAgent = null, CancellationToken ct = default);
    Task<IReadOnlyList<AuditLog>> GetRecentLogsAsync(int count = 100,
        CancellationToken ct = default);
}

/// <summary>
/// Async job queue using System.Threading.Channels for background processing.
/// </summary>
public interface IJobQueueService
{
    ValueTask EnqueueAsync(TranscriptionJobRequest request, CancellationToken ct = default);
    ValueTask<TranscriptionJobRequest> DequeueAsync(CancellationToken ct = default);
}
