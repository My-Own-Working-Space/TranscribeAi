namespace TranscribeAi.DataAccessLayer.Repositories.Interfaces;

/// <summary>
/// Specialized repository for TranscriptionJob with domain-specific queries.
/// </summary>
public interface ITranscriptionJobRepository : IRepository<TranscriptionJob>
{
    /// <summary>Get all jobs for a specific user, ordered by creation date descending.</summary>
    Task<IReadOnlyList<TranscriptionJob>> GetByUserIdAsync(string userId, int limit = 50, CancellationToken ct = default);

    /// <summary>Get a job with all navigation properties eagerly loaded.</summary>
    Task<TranscriptionJob?> GetWithDetailsAsync(Guid jobId, CancellationToken ct = default);

    /// <summary>Get a job only if it belongs to the specified user (IDOR prevention).</summary>
    Task<TranscriptionJob?> GetByIdAndUserAsync(Guid jobId, string userId, CancellationToken ct = default);

    /// <summary>Get jobs by status (for worker processing queue).</summary>
    Task<IReadOnlyList<TranscriptionJob>> GetByStatusAsync(JobStatus status, int limit = 10, CancellationToken ct = default);

    /// <summary>Get dashboard statistics for a user.</summary>
    Task<(int Total, int Completed, double TotalMinutes)> GetUserStatsAsync(string userId, CancellationToken ct = default);
}
