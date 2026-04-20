namespace TranscribeAi.DataAccessLayer.Configurations;

public class AISummaryConfiguration : IEntityTypeConfiguration<AISummary>
{
    public void Configure(EntityTypeBuilder<AISummary> builder)
    {
        builder.HasKey(s => s.Id);
        builder.HasIndex(s => s.JobId).IsUnique();

        builder.Property(s => s.LlmModel).HasMaxLength(100);
        builder.Property(s => s.KeyPoints).HasDefaultValue("[]");
        builder.Property(s => s.ReviewPasses).HasDefaultValue(0);
        builder.Property(s => s.GeneratedAt).HasDefaultValueSql("CURRENT_TIMESTAMP");
    }
}

public class ActionItemConfiguration : IEntityTypeConfiguration<ActionItem>
{
    public void Configure(EntityTypeBuilder<ActionItem> builder)
    {
        builder.HasKey(a => a.Id);
        builder.HasIndex(a => a.JobId).HasDatabaseName("idx_actions_job");

        builder.Property(a => a.Assignee).HasMaxLength(255).HasDefaultValue("Unassigned");
        builder.Property(a => a.Deadline).HasMaxLength(255).HasDefaultValue("Not specified");
        builder.Property(a => a.Priority).HasMaxLength(10).HasDefaultValue("medium");
        builder.Property(a => a.IsCompleted).HasDefaultValue(false);
        builder.Property(a => a.CreatedAt).HasDefaultValueSql("CURRENT_TIMESTAMP");
    }
}

public class ChatMessageConfiguration : IEntityTypeConfiguration<ChatMessage>
{
    public void Configure(EntityTypeBuilder<ChatMessage> builder)
    {
        builder.HasKey(c => c.Id);
        builder.HasIndex(c => c.JobId).HasDatabaseName("idx_chat_job");
        builder.HasIndex(c => new { c.JobId, c.UserId }).HasDatabaseName("idx_chat_session");

        builder.Property(c => c.Role).HasMaxLength(20);
        builder.Property(c => c.CreatedAt).HasDefaultValueSql("CURRENT_TIMESTAMP");
    }
}

public class AuditLogConfiguration : IEntityTypeConfiguration<AuditLog>
{
    public void Configure(EntityTypeBuilder<AuditLog> builder)
    {
        builder.HasKey(a => a.Id);
        builder.HasIndex(a => a.UserId).HasDatabaseName("idx_audit_user");
        builder.HasIndex(a => a.Timestamp).HasDatabaseName("idx_audit_timestamp").IsDescending();

        builder.Property(a => a.Action).HasConversion<string>().HasMaxLength(30);
        builder.Property(a => a.Details).HasMaxLength(1000);
        builder.Property(a => a.IpAddress).HasMaxLength(45);
        builder.Property(a => a.UserAgent).HasMaxLength(500);
        builder.Property(a => a.Timestamp).HasDefaultValueSql("CURRENT_TIMESTAMP");
    }
}

public class FeedbackConfiguration : IEntityTypeConfiguration<Feedback>
{
    public void Configure(EntityTypeBuilder<Feedback> builder)
    {
        builder.HasKey(f => f.Id);

        builder.Property(f => f.Name).HasMaxLength(255);
        builder.Property(f => f.Email).HasMaxLength(255);
        builder.Property(f => f.FeedbackType).HasMaxLength(20).HasDefaultValue("general");
        builder.Property(f => f.CreatedAt).HasDefaultValueSql("CURRENT_TIMESTAMP");

        builder.HasOne(f => f.User)
               .WithMany()
               .HasForeignKey(f => f.UserId)
               .OnDelete(DeleteBehavior.SetNull);
    }
}
