using TranscribeAi.DataAccessLayer.Data;
using TranscribeAi.DataAccessLayer.Repositories.Interfaces;

namespace TranscribeAi.DataAccessLayer.Repositories;

/// <summary>
/// Unit of Work implementation — coordinates all repositories under a single DbContext transaction.
/// </summary>
public class UnitOfWork : IUnitOfWork
{
    private readonly TranscribeDbContext _context;

    private ITranscriptionJobRepository? _transcriptionJobs;
    private IRepository<AISummary>? _summaries;
    private IRepository<ActionItem>? _actionItems;
    private IRepository<ChatMessage>? _chatMessages;
    private IRepository<AuditLog>? _auditLogs;
    private IRepository<Feedback>? _feedbacks;

    public UnitOfWork(TranscribeDbContext context)
    {
        _context = context;
    }

    public ITranscriptionJobRepository TranscriptionJobs
        => _transcriptionJobs ??= new TranscriptionJobRepository(_context);

    public IRepository<AISummary> Summaries
        => _summaries ??= new Repository<AISummary>(_context);

    public IRepository<ActionItem> ActionItems
        => _actionItems ??= new Repository<ActionItem>(_context);

    public IRepository<ChatMessage> ChatMessages
        => _chatMessages ??= new Repository<ChatMessage>(_context);

    public IRepository<AuditLog> AuditLogs
        => _auditLogs ??= new Repository<AuditLog>(_context);

    public IRepository<Feedback> Feedbacks
        => _feedbacks ??= new Repository<Feedback>(_context);

    public async Task<int> SaveChangesAsync(CancellationToken ct = default)
        => await _context.SaveChangesAsync(ct);

    public void Dispose()
    {
        _context.Dispose();
        GC.SuppressFinalize(this);
    }
}
