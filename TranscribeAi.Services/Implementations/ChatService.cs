namespace TranscribeAi.Services.Implementations;

/// <summary>
/// AI Chat service — Q&A over transcripts with persistent DB history (replaces Redis).
/// </summary>
public sealed class ChatService : IChatService
{
    private readonly ILlmService _llm;
    private readonly IUnitOfWork _uow;
    private readonly ILogger<ChatService> _logger;

    private const int MaxHistoryMessages = 20;

    private const string SystemPrompt =
        "You are an intelligent assistant that answers questions about a transcript. " +
        "Answer ONLY based on the transcript content. Reference timestamps when possible (e.g. 'At 2:30...'). " +
        "If the answer isn't in the transcript, say so. Respond in the same language as the question.";

    public ChatService(ILlmService llm, IUnitOfWork uow, ILogger<ChatService> logger)
    {
        _llm = llm;
        _uow = uow;
        _logger = logger;
    }

    public async Task<ChatResponseDto> AskQuestionAsync(Guid jobId, string userId,
        string question, CancellationToken ct = default)
    {
        var job = await _uow.TranscriptionJobs.GetByIdAsync(jobId, ct)
            ?? throw new InvalidOperationException("Job not found");

        if (string.IsNullOrWhiteSpace(job.Transcript))
            throw new InvalidOperationException("No transcript available");

        // Build context from segments
        var context = BuildContext(job);

        // Load recent history from DB
        var historyEntities = await _uow.ChatMessages.FindAsync(
            m => m.JobId == jobId && m.UserId == userId, ct);
        var recent = historyEntities
            .OrderByDescending(m => m.CreatedAt)
            .Take(MaxHistoryMessages)
            .OrderBy(m => m.CreatedAt)
            .ToList();

        // Build LLM messages
        var messages = new List<ChatMessageDto>
        {
            new() { Role = "user", Content = $"Transcript:\n\n{context}" },
            new() { Role = "assistant", Content = "I've read the transcript. Ask me anything about it." }
        };
        foreach (var m in recent.TakeLast(6))
            messages.Add(new ChatMessageDto { Role = m.Role, Content = m.Content });
        messages.Add(new ChatMessageDto { Role = "user", Content = question });

        var answer = await _llm.ChatWithHistoryAsync(SystemPrompt, messages, ct: ct);

        // Save to DB
        await _uow.ChatMessages.AddAsync(new ChatMessage
        {
            JobId = jobId, UserId = userId, Role = "user", Content = question
        }, ct);
        await _uow.ChatMessages.AddAsync(new ChatMessage
        {
            JobId = jobId, UserId = userId, Role = "assistant", Content = answer
        }, ct);
        await _uow.SaveChangesAsync(ct);

        // Find relevant source segments
        var segments = DeserializeSegments(job.SegmentsJson);
        var sources = FindSources(segments, question);

        return new ChatResponseDto { Answer = answer, Sources = sources };
    }

    public async Task<IReadOnlyList<ChatMessageDto>> GetHistoryAsync(Guid jobId, string userId,
        CancellationToken ct = default)
    {
        var messages = await _uow.ChatMessages.FindAsync(
            m => m.JobId == jobId && m.UserId == userId, ct);

        return messages
            .OrderBy(m => m.CreatedAt)
            .Select(m => new ChatMessageDto { Role = m.Role, Content = m.Content })
            .ToList();
    }

    public async Task ClearHistoryAsync(Guid jobId, string userId, CancellationToken ct = default)
    {
        var messages = await _uow.ChatMessages.FindAsync(
            m => m.JobId == jobId && m.UserId == userId, ct);
        _uow.ChatMessages.RemoveRange(messages);
        await _uow.SaveChangesAsync(ct);
    }

    private static string BuildContext(TranscriptionJob job)
    {
        var segments = DeserializeSegments(job.SegmentsJson);
        if (segments.Count == 0) return job.Transcript.Length > 10000 ? job.Transcript[..10000] : job.Transcript;

        var context = string.Join('\n', segments.Select(s =>
            $"[{FormatTime(s.Start)}-{FormatTime(s.End)}] {s.Text}"));
        return context.Length > 10000 ? context[..10000] + "\n[... truncated ...]" : context;
    }

    private static List<SegmentDto> DeserializeSegments(string json)
    {
        try { return JsonSerializer.Deserialize<List<SegmentDto>>(json) ?? new(); }
        catch { return new(); }
    }

    private static List<ChatSourceDto> FindSources(List<SegmentDto> segments, string question)
    {
        if (segments.Count == 0) return new();

        var stops = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
        {
            "the","a","is","are","was","what","how","why","when","where","who","about",
            "in","on","at","to","for","of","and","or","not","là","của","và","có","không","được","gì","như"
        };

        var keywords = question.ToLower().Split(' ', StringSplitOptions.RemoveEmptyEntries)
            .Where(w => !stops.Contains(w)).ToHashSet();
        if (keywords.Count == 0) return new();

        return segments
            .Select(s =>
            {
                var words = s.Text.ToLower().Split(' ', StringSplitOptions.RemoveEmptyEntries).ToHashSet();
                var overlap = keywords.Intersect(words).Count();
                return new { Segment = s, Relevance = overlap };
            })
            .Where(x => x.Relevance > 0)
            .OrderByDescending(x => x.Relevance)
            .Take(3)
            .Select(x => new ChatSourceDto
            {
                Time = $"{FormatTime(x.Segment.Start)}-{FormatTime(x.Segment.End)}",
                Text = x.Segment.Text,
                Relevance = x.Relevance
            })
            .ToList();
    }

    private static string FormatTime(double seconds)
    {
        var m = (int)seconds / 60;
        var s = (int)seconds % 60;
        return $"{m:D2}:{s:D2}";
    }
}
