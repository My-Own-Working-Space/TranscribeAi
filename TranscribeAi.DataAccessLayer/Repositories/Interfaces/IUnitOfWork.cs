namespace TranscribeAi.DataAccessLayer.Repositories.Interfaces;

/// <summary>
/// Unit of Work pattern — coordinates multiple repositories under a single transaction.
/// </summary>
public interface IUnitOfWork : IDisposable
{
    ITranscriptionJobRepository TranscriptionJobs { get; }
    IRepository<AISummary> Summaries { get; }
    IRepository<ActionItem> ActionItems { get; }
    IRepository<ChatMessage> ChatMessages { get; }
    IRepository<AuditLog> AuditLogs { get; }
    IRepository<Feedback> Feedbacks { get; }

    /// <summary>Persist all pending changes in a single transaction.</summary>
    Task<int> SaveChangesAsync(CancellationToken ct = default);
}
