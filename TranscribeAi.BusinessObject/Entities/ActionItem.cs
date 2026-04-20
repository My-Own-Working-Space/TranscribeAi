namespace TranscribeAi.BusinessObject.Entities;

/// <summary>
/// An action item extracted from a meeting transcript by the AI.
/// </summary>
public class ActionItem
{
    [Key]
    public Guid Id { get; set; } = Guid.NewGuid();

    [Required]
    public Guid JobId { get; set; }

    [Required]
    public string TaskDescription { get; set; } = null!;

    [MaxLength(255)]
    public string Assignee { get; set; } = "Unassigned";

    [MaxLength(255)]
    public string Deadline { get; set; } = "Not specified";

    [MaxLength(10)]
    public string Priority { get; set; } = "medium";

    public bool IsCompleted { get; set; }

    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    // ── Navigation ──
    [ForeignKey(nameof(JobId))]
    public TranscriptionJob Job { get; set; } = null!;
}
