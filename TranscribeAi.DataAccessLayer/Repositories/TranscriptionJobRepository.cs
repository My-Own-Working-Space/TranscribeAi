using TranscribeAi.DataAccessLayer.Data;
using TranscribeAi.DataAccessLayer.Repositories.Interfaces;

namespace TranscribeAi.DataAccessLayer.Repositories;

/// <summary>
/// Specialized TranscriptionJob repository with domain queries optimized for the SaaS workflow.
/// </summary>
public class TranscriptionJobRepository : Repository<TranscriptionJob>, ITranscriptionJobRepository
{
    public TranscriptionJobRepository(TranscribeDbContext context) : base(context) { }

    public async Task<IReadOnlyList<TranscriptionJob>> GetByUserIdAsync(
        string userId, int limit = 50, CancellationToken ct = default)
    {
        return await DbSet
            .AsNoTracking()
            .Where(j => j.UserId == userId)
            .OrderByDescending(j => j.CreatedAt)
            .Take(limit)
            .Include(j => j.Summary)
            .ToListAsync(ct);
    }

    public async Task<TranscriptionJob?> GetWithDetailsAsync(Guid jobId, CancellationToken ct = default)
    {
        return await DbSet
            .Include(j => j.Summary)
            .Include(j => j.ActionItems)
            .Include(j => j.User)
            .FirstOrDefaultAsync(j => j.Id == jobId, ct);
    }

    public async Task<TranscriptionJob?> GetByIdAndUserAsync(
        Guid jobId, string userId, CancellationToken ct = default)
    {
        return await DbSet
            .Include(j => j.Summary)
            .Include(j => j.ActionItems)
            .FirstOrDefaultAsync(j => j.Id == jobId && j.UserId == userId, ct);
    }

    public async Task<IReadOnlyList<TranscriptionJob>> GetByStatusAsync(
        JobStatus status, int limit = 10, CancellationToken ct = default)
    {
        return await DbSet
            .Where(j => j.Status == status)
            .OrderBy(j => j.CreatedAt)
            .Take(limit)
            .ToListAsync(ct);
    }

    public async Task<(int Total, int Completed, double TotalMinutes)> GetUserStatsAsync(
        string userId, CancellationToken ct = default)
    {
        var jobs = DbSet.Where(j => j.UserId == userId);

        var total = await jobs.CountAsync(ct);
        var completed = await jobs.CountAsync(j => j.Status == JobStatus.Completed, ct);
        var totalSeconds = await jobs
            .Where(j => j.Status == JobStatus.Completed)
            .SumAsync(j => j.DurationSeconds, ct);

        return (total, completed, Math.Round(totalSeconds / 60.0, 1));
    }
}
