namespace TranscribeAi.BusinessObject.Entities;

/// <summary>
/// AI-generated summary for a transcription job.
/// One-to-one relationship with TranscriptionJob.
/// Uses a multi-agent pipeline: Generator → Reviewer → Refiner.
/// </summary>
public class AISummary
{
    [Key]
    public Guid Id { get; set; } = Guid.NewGuid();

    [Required]
    public Guid JobId { get; set; }

    public string? Summary { get; set; }

    /// <summary>JSON array of key point strings.</summary>
    [Column(TypeName = "jsonb")]
    public string KeyPoints { get; set; } = "[]";

    public string? Conclusion { get; set; }

    [MaxLength(100)]
    public string? LlmModel { get; set; }

    /// <summary>Number of review/refine iterations performed.</summary>
    public int ReviewPasses { get; set; }

    public DateTime GeneratedAt { get; set; } = DateTime.UtcNow;

    // ── Navigation ──
    [ForeignKey(nameof(JobId))]
    public TranscriptionJob Job { get; set; } = null!;
}
