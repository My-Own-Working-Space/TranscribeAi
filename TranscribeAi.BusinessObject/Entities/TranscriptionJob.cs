using TranscribeAi.BusinessObject.Enums;

namespace TranscribeAi.BusinessObject.Entities;

/// <summary>
/// Represents a single transcription job — from upload through completion.
/// Mirrors the 'transcription_jobs' table from the existing Supabase schema.
/// </summary>
public class TranscriptionJob
{
    [Key]
    public Guid Id { get; set; } = Guid.NewGuid();

    [Required]
    public string UserId { get; set; } = null!;

    public JobStatus Status { get; set; } = JobStatus.Queued;

    [MaxLength(500)]
    public string? OriginalFilename { get; set; }

    [MaxLength(1000)]
    public string? StoragePath { get; set; }

    public int FileSizeBytes { get; set; }

    public double DurationSeconds { get; set; }

    [MaxLength(50)]
    public string WhisperModel { get; set; } = "base";

    [MaxLength(10)]
    public string? LanguageDetected { get; set; }

    public double OverallConfidence { get; set; }

    public double ProcessingTimeSeconds { get; set; }

    /// <summary>Full plain-text transcript.</summary>
    public string Transcript { get; set; } = string.Empty;

    /// <summary>
    /// JSON array of segment objects: [{index, start, end, text, confidence, speaker}].
    /// Stored as JSONB in PostgreSQL, TEXT in SQLite.
    /// </summary>
    [Column(TypeName = "jsonb")]
    public string SegmentsJson { get; set; } = "[]";

    public JobMode Mode { get; set; } = JobMode.Standard;

    public string? Error { get; set; }

    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    public DateTime? CompletedAt { get; set; }

    // ── Navigation Properties ──

    [ForeignKey(nameof(UserId))]
    public ApplicationUser User { get; set; } = null!;

    public AISummary? Summary { get; set; }

    public ICollection<ActionItem> ActionItems { get; set; } = new List<ActionItem>();

    public ICollection<ChatMessage> ChatMessages { get; set; } = new List<ChatMessage>();
}
