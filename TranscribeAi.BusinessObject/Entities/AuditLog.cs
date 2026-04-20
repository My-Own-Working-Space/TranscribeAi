using TranscribeAi.BusinessObject.Enums;

namespace TranscribeAi.BusinessObject.Entities;

/// <summary>
/// Security audit log entry tracking user actions for compliance.
/// </summary>
public class AuditLog
{
    [Key]
    public Guid Id { get; set; } = Guid.NewGuid();

    [Required]
    public string UserId { get; set; } = null!;

    public AuditAction Action { get; set; }

    /// <summary>Additional context about the action (e.g. filename, job ID).</summary>
    [MaxLength(1000)]
    public string? Details { get; set; }

    [MaxLength(45)]
    public string? IpAddress { get; set; }

    [MaxLength(500)]
    public string? UserAgent { get; set; }

    public DateTime Timestamp { get; set; } = DateTime.UtcNow;

    // ── Navigation ──
    [ForeignKey(nameof(UserId))]
    public ApplicationUser User { get; set; } = null!;
}
