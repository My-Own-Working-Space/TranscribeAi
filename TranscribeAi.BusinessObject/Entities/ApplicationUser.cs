using TranscribeAi.BusinessObject.Enums;

namespace TranscribeAi.BusinessObject.Entities;

/// <summary>
/// Application user extending ASP.NET Core Identity with SaaS-specific properties.
/// Maps to the 'AspNetUsers' table via Identity framework.
/// </summary>
public class ApplicationUser : IdentityUser
{
    [MaxLength(255)]
    public string FullName { get; set; } = string.Empty;

    public UserPlan Plan { get; set; } = UserPlan.Free;

    public int MonthlyMinutesUsed { get; set; }

    public int MonthlyMinutesLimit { get; set; } = 9999;

    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;

    // ── Navigation Properties ──
    public ICollection<TranscriptionJob> Jobs { get; set; } = new List<TranscriptionJob>();
    public ICollection<AuditLog> AuditLogs { get; set; } = new List<AuditLog>();
}
