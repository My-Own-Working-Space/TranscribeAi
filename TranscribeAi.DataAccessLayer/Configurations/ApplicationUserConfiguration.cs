namespace TranscribeAi.DataAccessLayer.Configurations;

public class ApplicationUserConfiguration : IEntityTypeConfiguration<ApplicationUser>
{
    public void Configure(EntityTypeBuilder<ApplicationUser> builder)
    {
        builder.Property(u => u.FullName).HasMaxLength(255);
        builder.Property(u => u.Plan).HasConversion<string>().HasMaxLength(20).HasDefaultValue(UserPlan.Free);
        builder.Property(u => u.MonthlyMinutesUsed).HasDefaultValue(0);
        builder.Property(u => u.MonthlyMinutesLimit).HasDefaultValue(9999);
        builder.Property(u => u.CreatedAt).HasDefaultValueSql("CURRENT_TIMESTAMP");
        builder.Property(u => u.UpdatedAt).HasDefaultValueSql("CURRENT_TIMESTAMP");

        builder.HasMany(u => u.Jobs)
               .WithOne(j => j.User)
               .HasForeignKey(j => j.UserId)
               .OnDelete(DeleteBehavior.Cascade);

        builder.HasMany(u => u.AuditLogs)
               .WithOne(a => a.User)
               .HasForeignKey(a => a.UserId)
               .OnDelete(DeleteBehavior.Cascade);
    }
}
