namespace TranscribeAi.Services.Implementations;

/// <summary>
/// Multi-agent AI summary pipeline ported from Python: Generate → Review → Refine.
/// </summary>
public sealed class SummaryService : ISummaryService
{
    private readonly ILlmService _llm;
    private readonly IUnitOfWork _uow;
    private readonly ILogger<SummaryService> _logger;

    private const int MaxReviewPasses = 2;
    private const int QualityThreshold = 7;

    public SummaryService(ILlmService llm, IUnitOfWork uow, ILogger<SummaryService> logger)
    {
        _llm = llm;
        _uow = uow;
        _logger = logger;
    }

    public async Task<SummaryDto?> GetSummaryByJobIdAsync(Guid jobId, CancellationToken ct = default)
    {
        var summaries = await _uow.Summaries.FindAsync(s => s.JobId == jobId, ct);
        var summary = summaries.FirstOrDefault();
        return summary is null ? null : MapToDto(summary);
    }

    public async Task<SummaryDto> GenerateSummaryAsync(Guid jobId, string? language = null,
        CancellationToken ct = default)
    {
        var job = await _uow.TranscriptionJobs.GetByIdAsync(jobId, ct)
            ?? throw new InvalidOperationException("Job not found");

        if (string.IsNullOrWhiteSpace(job.Transcript))
            throw new InvalidOperationException("No transcript available");

        // Remove existing summary
        var existing = await _uow.Summaries.FindAsync(s => s.JobId == jobId, ct);
        if (existing.Any())
        {
            _uow.Summaries.RemoveRange(existing);
            await _uow.SaveChangesAsync(ct);
        }

        var text = job.Transcript.Length > 12000
            ? job.Transcript[..12000] + "\n\n[... truncated ...]"
            : job.Transcript;

        var modeStr = job.Mode.ToString().ToLower();

        // ── Step 1: Generate ──
        _logger.LogInformation("[Agent:Generator] Creating summary for job {JobId} (mode={Mode})", jobId, modeStr);
        var genPrompt = GetGeneratorPrompt(modeStr, language);
        var rawResponse = await _llm.ChatAsync(genPrompt, $"Transcript:\n\n{text}", ct: ct);
        var parsed = ParseSummaryJson(rawResponse);

        int reviewPasses = 0;

        // ── Step 2-3: Review → Refine loop ──
        for (int attempt = 0; attempt < MaxReviewPasses; attempt++)
        {
            _logger.LogInformation("[Agent:Reviewer] Pass {Pass} for job {JobId}", attempt + 1, jobId);

            var reviewInput = $"=== ORIGINAL TRANSCRIPT ===\n{text}\n\n=== AI SUMMARY TO REVIEW ===\n{JsonSerializer.Serialize(parsed)}";
            var reviewRaw = await _llm.ChatAsync(GetReviewerPrompt(language), reviewInput, 0.2f, ct: ct);
            var reviewDoc = _llm.ParseJsonResponse(reviewRaw);

            var score = 10;
            var issueCount = 0;
            if (reviewDoc is not null)
            {
                score = reviewDoc.RootElement.TryGetProperty("score", out var sp) ? sp.GetInt32() : 10;
                issueCount = reviewDoc.RootElement.TryGetProperty("issues", out var ip) ? ip.GetArrayLength() : 0;
            }

            _logger.LogInformation("[Agent:Reviewer] Score: {Score}/10, Issues: {Issues}", score, issueCount);
            reviewPasses++;

            if (score >= QualityThreshold && issueCount == 0)
            {
                _logger.LogInformation("[Pipeline] Quality sufficient (score={Score})", score);
                break;
            }

            // Refine
            _logger.LogInformation("[Agent:Refiner] Refining summary (score was {Score})", score);
            var refineInput = $"=== ORIGINAL TRANSCRIPT ===\n{text}\n\n=== DRAFT SUMMARY ===\n{JsonSerializer.Serialize(parsed)}\n\n=== REVIEW FEEDBACK ===\n{reviewRaw}";
            var refinedRaw = await _llm.ChatAsync(GetRefinerPrompt(language), refineInput, 0.25f, ct: ct);
            var refinedParsed = ParseSummaryJson(refinedRaw);
            if (!string.IsNullOrEmpty(refinedParsed.Summary))
            {
                parsed = refinedParsed;
                _logger.LogInformation("[Agent:Refiner] Summary successfully refined");
            }
            else
            {
                _logger.LogWarning("[Agent:Refiner] Failed to parse refined output, keeping previous");
                break;
            }

            reviewDoc?.Dispose();
        }

        // ── Save ──
        var summaryEntity = new AISummary
        {
            JobId = jobId,
            Summary = parsed.Summary,
            KeyPoints = JsonSerializer.Serialize(parsed.KeyPoints),
            Conclusion = parsed.Conclusion,
            LlmModel = "llama-3.3-70b-versatile",
            ReviewPasses = reviewPasses
        };
        await _uow.Summaries.AddAsync(summaryEntity, ct);
        await _uow.SaveChangesAsync(ct);

        _logger.LogInformation("[Pipeline] Summary saved for job {JobId} (passes={Passes})", jobId, reviewPasses);
        return MapToDto(summaryEntity);
    }

    // ── Prompt builders ──

    private static string GetGeneratorPrompt(string mode, string? lang) =>
        mode switch
        {
            "meeting" => """
                You are an expert meeting summarizer. Given a meeting transcript, produce JSON:
                {"summary": "2-3 paragraphs covering all agenda items", "key_points": ["key decisions and agreements with timestamps"], "conclusion": "concrete next steps"}
                Rules: Include WHO said what. Note all decisions. Reference timestamps. Use SAME language as transcript. Respond ONLY with valid JSON.
                """,
            "lecture" => """
                You are an expert lecture summarizer. Given a lecture transcript, produce JSON:
                {"summary": "2-3 paragraphs covering content comprehensively", "key_points": ["main concepts, definitions, examples"], "conclusion": "key takeaways for studying"}
                Rules: Capture all concepts. Include examples. Reference timestamps. Use SAME language as transcript. Respond ONLY with valid JSON.
                """,
            _ => """
                You are a world-class summarizer. Given a transcript, produce JSON:
                {"summary": "2-3 detailed paragraphs covering ALL main topics", "key_points": ["5-10 specific factual points with timestamps"], "conclusion": "1-2 sentence key takeaway"}
                Rules: Be SPECIFIC with names, numbers, dates. Reference timestamps. Cover ALL topics. Use SAME language as transcript. Respond ONLY with valid JSON.
                """
        } + GetLanguageInstruction(lang);

    private static string GetReviewerPrompt(string? lang) =>
        """
        You are a critical quality reviewer. Compare SUMMARY against ORIGINAL TRANSCRIPT:
        1. Accuracy: factual errors or hallucinations?
        2. Completeness: important topics missing?
        3. Specificity: includes names, numbers, timestamps?
        Respond with JSON: {"score": 1-10, "issues": ["problems"], "missing_topics": ["topics"], "suggestions": ["improvements"]}
        Be STRICT. Score 8+ = excellent. Respond ONLY with valid JSON.
        """ + GetLanguageInstruction(lang);

    private static string GetRefinerPrompt(string? lang) =>
        """
        You are a summary refinement specialist. You receive original transcript, draft summary, and review feedback.
        Produce IMPROVED JSON: {"summary": "...", "key_points": [...], "conclusion": "..."}
        Fix all accuracy issues. Add missing topics. Be more specific. Keep same language. Respond ONLY with valid JSON.
        """ + GetLanguageInstruction(lang);

    private static string GetLanguageInstruction(string? lang) => lang switch
    {
        "vi" => "\n- IMPORTANT: Write the ENTIRE summary in Vietnamese (Tiếng Việt).",
        "en" => "\n- IMPORTANT: Write the ENTIRE summary in English.",
        _ => ""
    };

    private (string Summary, List<string> KeyPoints, string Conclusion) ParseSummaryJson(string raw)
    {
        var doc = _llm.ParseJsonResponse(raw);
        if (doc is null) return (raw, new(), string.Empty);

        var root = doc.RootElement;
        var summary = root.TryGetProperty("summary", out var sp) ? sp.GetString() ?? raw : raw;
        var keyPoints = new List<string>();
        if (root.TryGetProperty("key_points", out var kp) && kp.ValueKind == JsonValueKind.Array)
            keyPoints = kp.EnumerateArray().Select(e => e.GetString() ?? "").Where(s => s.Length > 0).ToList();
        var conclusion = root.TryGetProperty("conclusion", out var cp) ? cp.GetString() ?? "" : "";

        doc.Dispose();
        return (summary, keyPoints, conclusion);
    }

    private static SummaryDto MapToDto(AISummary entity)
    {
        var keyPoints = new List<string>();
        try
        {
            if (!string.IsNullOrEmpty(entity.KeyPoints))
                keyPoints = JsonSerializer.Deserialize<List<string>>(entity.KeyPoints) ?? new();
        }
        catch { /* ignore parse errors */ }

        return new SummaryDto
        {
            Id = entity.Id,
            Summary = entity.Summary ?? string.Empty,
            KeyPoints = keyPoints,
            Conclusion = entity.Conclusion ?? string.Empty,
            LlmModel = entity.LlmModel,
            ReviewPasses = entity.ReviewPasses,
            GeneratedAt = entity.GeneratedAt
        };
    }
}
