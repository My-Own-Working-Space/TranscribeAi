namespace TranscribeAi.BusinessObject.Entities;

/// <summary>
/// User-submitted feedback (supports both authenticated and anonymous users).
/// </summary>
public class Feedback
{
    [Key]
    public Guid Id { get; set; } = Guid.NewGuid();

    /// <summary>Nullable — supports anonymous feedback.</summary>
    public string? UserId { get; set; }

    [MaxLength(255)]
    public string Name { get; set; } = string.Empty;

    [MaxLength(255)]
    public string Email { get; set; } = string.Empty;

    /// <summary>general | bug | feature | other</summary>
    [MaxLength(20)]
    public string FeedbackType { get; set; } = "general";

    [Required]
    public string Message { get; set; } = null!;

    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    // ── Navigation ──
    [ForeignKey(nameof(UserId))]
    public ApplicationUser? User { get; set; }
}
