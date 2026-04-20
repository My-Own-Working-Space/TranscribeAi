namespace TranscribeAi.DataAccessLayer.Data;

/// <summary>
/// EF Core database context for TranscribeAI.
/// Extends IdentityDbContext to integrate ASP.NET Core Identity tables
/// alongside application-specific entities.
/// </summary>
public class TranscribeDbContext : IdentityDbContext<ApplicationUser>
{
    public TranscribeDbContext(DbContextOptions<TranscribeDbContext> options)
        : base(options)
    {
    }

    public DbSet<TranscriptionJob> TranscriptionJobs => Set<TranscriptionJob>();
    public DbSet<AISummary> AISummaries => Set<AISummary>();
    public DbSet<ActionItem> ActionItems => Set<ActionItem>();
    public DbSet<ChatMessage> ChatMessages => Set<ChatMessage>();
    public DbSet<Feedback> Feedbacks => Set<Feedback>();
    public DbSet<AuditLog> AuditLogs => Set<AuditLog>();

    protected override void OnModelCreating(ModelBuilder builder)
    {
        base.OnModelCreating(builder);

        // Apply all IEntityTypeConfiguration classes from this assembly
        builder.ApplyConfigurationsFromAssembly(typeof(TranscribeDbContext).Assembly);
    }

    /// <summary>
    /// Automatically set UpdatedAt on ApplicationUser when saving changes.
    /// </summary>
    public override Task<int> SaveChangesAsync(CancellationToken cancellationToken = default)
    {
        foreach (var entry in ChangeTracker.Entries<ApplicationUser>())
        {
            if (entry.State == EntityState.Modified)
            {
                entry.Entity.UpdatedAt = DateTime.UtcNow;
            }
        }

        return base.SaveChangesAsync(cancellationToken);
    }
}
