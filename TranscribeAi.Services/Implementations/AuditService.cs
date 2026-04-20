namespace TranscribeAi.Services.Implementations;

/// <summary>
/// Security audit logging — persists user actions for compliance.
/// </summary>
public sealed class AuditService : IAuditService
{
    private readonly IUnitOfWork _uow;
    private readonly ILogger<AuditService> _logger;

    public AuditService(IUnitOfWork uow, ILogger<AuditService> logger)
    {
        _uow = uow;
        _logger = logger;
    }

    public async Task LogAsync(string userId, AuditAction action, string? details = null,
        string? ipAddress = null, string? userAgent = null, CancellationToken ct = default)
    {
        var entry = new AuditLog
        {
            UserId = userId,
            Action = action,
            Details = details,
            IpAddress = ipAddress,
            UserAgent = userAgent
        };

        await _uow.AuditLogs.AddAsync(entry, ct);
        await _uow.SaveChangesAsync(ct);

        _logger.LogInformation("Audit: {Action} by {UserId} — {Details}", action, userId, details);
    }

    public async Task<IReadOnlyList<AuditLog>> GetRecentLogsAsync(int count = 100,
        CancellationToken ct = default)
    {
        var all = await _uow.AuditLogs.GetAllAsync(ct);
        return all.OrderByDescending(a => a.Timestamp).Take(count).ToList();
    }
}
