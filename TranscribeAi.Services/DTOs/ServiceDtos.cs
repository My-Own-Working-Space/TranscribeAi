namespace TranscribeAi.Services.DTOs;

/// <summary>Result from the transcription engine (Groq STT API).</summary>
public sealed record TranscriptionResultDto
{
    public string FullText { get; init; } = string.Empty;
    public List<SegmentDto> Segments { get; init; } = new();
    public double OverallConfidence { get; init; }
    public double DurationSeconds { get; init; }
    public double ProcessingTimeSeconds { get; init; }
    public string LanguageDetected { get; init; } = string.Empty;
    public string Model { get; init; } = string.Empty;
}

public sealed record SegmentDto
{
    public int Index { get; init; }
    public double Start { get; init; }
    public double End { get; init; }
    public string Text { get; init; } = string.Empty;
    public double Confidence { get; init; }
    public string? Speaker { get; init; }
}

/// <summary>AI-generated summary with key points.</summary>
public sealed record SummaryDto
{
    public Guid Id { get; init; }
    public string Summary { get; init; } = string.Empty;
    public List<string> KeyPoints { get; init; } = new();
    public string Conclusion { get; init; } = string.Empty;
    public string? LlmModel { get; init; }
    public int ReviewPasses { get; init; }
    public DateTime GeneratedAt { get; init; }
}

/// <summary>Chat Q&A response.</summary>
public sealed record ChatResponseDto
{
    public string Answer { get; init; } = string.Empty;
    public List<ChatSourceDto> Sources { get; init; } = new();
}

public sealed record ChatSourceDto
{
    public string Time { get; init; } = string.Empty;
    public string Text { get; init; } = string.Empty;
    public int Relevance { get; init; }
}

public sealed record ChatMessageDto
{
    public string Role { get; init; } = string.Empty;
    public string Content { get; init; } = string.Empty;
}

/// <summary>User dashboard statistics.</summary>
public sealed record DashboardStatsDto
{
    public int TotalJobs { get; init; }
    public int CompletedJobs { get; init; }
    public double TotalMinutesTranscribed { get; init; }
    public int MinutesUsedThisMonth { get; init; }
    public int MinutesLimit { get; init; }
    public string Plan { get; init; } = string.Empty;
}

/// <summary>Real-time job progress update sent via SignalR.</summary>
public sealed record JobProgressDto
{
    public int Percent { get; init; }
    public string Step { get; init; } = string.Empty;
    public string Detail { get; init; } = string.Empty;
}

/// <summary>Request to enqueue a transcription job.</summary>
public sealed record TranscriptionJobRequest
{
    public Guid JobId { get; init; }
    public string UserId { get; init; } = string.Empty;
    public string FilePath { get; init; } = string.Empty;
    public string? Language { get; init; }
    public JobMode Mode { get; init; }
}

/// <summary>Action item DTO for display.</summary>
public sealed record ActionItemDto
{
    public Guid Id { get; init; }
    public string TaskDescription { get; init; } = string.Empty;
    public string Assignee { get; init; } = string.Empty;
    public string Deadline { get; init; } = string.Empty;
    public string Priority { get; init; } = string.Empty;
    public bool IsCompleted { get; init; }
}

/// <summary>Job list item for history view.</summary>
public sealed record JobListItemDto
{
    public Guid Id { get; init; }
    public string Status { get; init; } = string.Empty;
    public string? OriginalFilename { get; init; }
    public int FileSizeBytes { get; init; }
    public double DurationSeconds { get; init; }
    public double OverallConfidence { get; init; }
    public double ProcessingTimeSeconds { get; init; }
    public string Mode { get; init; } = string.Empty;
    public string? LanguageDetected { get; init; }
    public bool HasSummary { get; init; }
    public DateTime CreatedAt { get; init; }
    public DateTime? CompletedAt { get; init; }
}
