namespace TranscribeAi.DataAccessLayer.Configurations;

public class TranscriptionJobConfiguration : IEntityTypeConfiguration<TranscriptionJob>
{
    public void Configure(EntityTypeBuilder<TranscriptionJob> builder)
    {
        builder.HasKey(j => j.Id);

        builder.Property(j => j.Status)
               .HasConversion<string>()
               .HasMaxLength(20)
               .HasDefaultValue(JobStatus.Queued);

        builder.Property(j => j.Mode)
               .HasConversion<string>()
               .HasMaxLength(20)
               .HasDefaultValue(JobMode.Standard);

        builder.Property(j => j.OriginalFilename).HasMaxLength(500);
        builder.Property(j => j.StoragePath).HasMaxLength(1000);
        builder.Property(j => j.WhisperModel).HasMaxLength(50).HasDefaultValue("base");
        builder.Property(j => j.LanguageDetected).HasMaxLength(10);
        builder.Property(j => j.Transcript).HasDefaultValue(string.Empty);
        builder.Property(j => j.SegmentsJson).HasDefaultValue("[]");
        builder.Property(j => j.CreatedAt).HasDefaultValueSql("CURRENT_TIMESTAMP");

        // Indexes matching the existing Supabase schema
        builder.HasIndex(j => new { j.UserId, j.Status }).HasDatabaseName("idx_jobs_user_status");
        builder.HasIndex(j => j.CreatedAt).HasDatabaseName("idx_jobs_created_at").IsDescending();

        builder.HasOne(j => j.User)
               .WithMany(u => u.Jobs)
               .HasForeignKey(j => j.UserId)
               .OnDelete(DeleteBehavior.Cascade);

        builder.HasOne(j => j.Summary)
               .WithOne(s => s.Job)
               .HasForeignKey<AISummary>(s => s.JobId)
               .OnDelete(DeleteBehavior.Cascade);

        builder.HasMany(j => j.ActionItems)
               .WithOne(a => a.Job)
               .HasForeignKey(a => a.JobId)
               .OnDelete(DeleteBehavior.Cascade);

        builder.HasMany(j => j.ChatMessages)
               .WithOne(c => c.Job)
               .HasForeignKey(c => c.JobId)
               .OnDelete(DeleteBehavior.Cascade);
    }
}
