namespace TranscribeAi.Services.Implementations;

/// <summary>
/// Action items extraction service — uses LLM to extract tasks from meeting transcripts.
/// </summary>
public sealed class ActionService : IActionService
{
    private readonly ILlmService _llm;
    private readonly IUnitOfWork _uow;
    private readonly ILogger<ActionService> _logger;

    private const string Prompt =
        "Extract ALL action items from the transcript. For each, provide: " +
        "\"task\" (what to do), \"assignee\" (who, or \"Unassigned\"), \"deadline\" (when, or \"Not specified\"), " +
        "\"priority\" (\"low\"/\"medium\"/\"high\"). Return a JSON array. If none found, return [].";

    public ActionService(ILlmService llm, IUnitOfWork uow, ILogger<ActionService> logger)
    {
        _llm = llm;
        _uow = uow;
        _logger = logger;
    }

    public async Task<IReadOnlyList<ActionItemDto>> ExtractActionsAsync(Guid jobId,
        CancellationToken ct = default)
    {
        var job = await _uow.TranscriptionJobs.GetByIdAsync(jobId, ct)
            ?? throw new InvalidOperationException("Job not found");

        if (string.IsNullOrWhiteSpace(job.Transcript))
            return Array.Empty<ActionItemDto>();

        // Remove existing action items
        var existing = await _uow.ActionItems.FindAsync(a => a.JobId == jobId, ct);
        if (existing.Any())
        {
            _uow.ActionItems.RemoveRange(existing);
            await _uow.SaveChangesAsync(ct);
        }

        var text = job.Transcript.Length > 12000 ? job.Transcript[..12000] : job.Transcript;
        var response = await _llm.ChatAsync(Prompt, $"Transcript:\n\n{text}", ct: ct);
        var doc = _llm.ParseJsonResponse(response);

        var items = new List<ActionItem>();

        if (doc is not null && doc.RootElement.ValueKind == JsonValueKind.Array)
        {
            foreach (var el in doc.RootElement.EnumerateArray())
            {
                if (!el.TryGetProperty("task", out var taskProp)) continue;

                var item = new ActionItem
                {
                    JobId = jobId,
                    TaskDescription = taskProp.GetString() ?? "",
                    Assignee = el.TryGetProperty("assignee", out var a) ? a.GetString() ?? "Unassigned" : "Unassigned",
                    Deadline = el.TryGetProperty("deadline", out var d) ? d.GetString() ?? "Not specified" : "Not specified",
                    Priority = el.TryGetProperty("priority", out var p) ? p.GetString() ?? "medium" : "medium"
                };
                await _uow.ActionItems.AddAsync(item, ct);
                items.Add(item);
            }

            doc.Dispose();
        }

        await _uow.SaveChangesAsync(ct);
        _logger.LogInformation("Extracted {Count} actions for job {JobId}", items.Count, jobId);

        return items.Select(MapToDto).ToList();
    }

    public async Task<ActionItemDto> UpdateActionAsync(Guid actionId, bool? isCompleted,
        string? priority, CancellationToken ct = default)
    {
        var item = await _uow.ActionItems.GetByIdAsync(actionId, ct)
            ?? throw new InvalidOperationException("Action item not found");

        if (isCompleted.HasValue) item.IsCompleted = isCompleted.Value;
        if (!string.IsNullOrEmpty(priority)) item.Priority = priority;

        _uow.ActionItems.Update(item);
        await _uow.SaveChangesAsync(ct);

        return MapToDto(item);
    }

    private static ActionItemDto MapToDto(ActionItem a) => new()
    {
        Id = a.Id,
        TaskDescription = a.TaskDescription,
        Assignee = a.Assignee,
        Deadline = a.Deadline,
        Priority = a.Priority,
        IsCompleted = a.IsCompleted
    };
}
