namespace TranscribeAi.BusinessObject.Entities;

/// <summary>
/// A single message in a chat Q&amp;A session over a transcript.
/// Replaces Redis-only storage from the Python version with persistent DB storage.
/// </summary>
public class ChatMessage
{
    [Key]
    public Guid Id { get; set; } = Guid.NewGuid();

    [Required]
    public Guid JobId { get; set; }

    [Required]
    public string UserId { get; set; } = null!;

    /// <summary>"user" or "assistant"</summary>
    [Required, MaxLength(20)]
    public string Role { get; set; } = null!;

    [Required]
    public string Content { get; set; } = null!;

    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    // ── Navigation ──
    [ForeignKey(nameof(JobId))]
    public TranscriptionJob Job { get; set; } = null!;

    [ForeignKey(nameof(UserId))]
    public ApplicationUser User { get; set; } = null!;
}
