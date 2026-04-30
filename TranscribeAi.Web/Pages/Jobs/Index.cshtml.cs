using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;
using TranscribeAi.BusinessObject.Entities;
using TranscribeAi.DataAccessLayer.Repositories.Interfaces;
using TranscribeAi.Services.DTOs;

namespace TranscribeAi.Web.Pages.Jobs;

[Authorize]
public class IndexModel : PageModel
{
    private readonly IUnitOfWork _uow;
    private readonly UserManager<ApplicationUser> _userManager;

    public IndexModel(IUnitOfWork uow, UserManager<ApplicationUser> userManager)
    {
        _uow = uow;
        _userManager = userManager;
    }

    public IReadOnlyList<JobListItemDto> Jobs { get; set; } = new List<JobListItemDto>();

    public async Task OnGetAsync()
    {
        var userId = _userManager.GetUserId(User);
        if (string.IsNullOrEmpty(userId)) return;

        var jobs = await _uow.TranscriptionJobs.GetByUserIdAsync(userId);
        
        Jobs = jobs.Select(j => new JobListItemDto
        {
            Id = j.Id,
            Status = j.Status.ToString(),
            OriginalFilename = j.OriginalFilename,
            ProjectName = j.ProjectName ?? j.OriginalFilename,
            Description = j.Description,
            FileSizeBytes = j.FileSizeBytes,
            DurationSeconds = j.DurationSeconds,
            OverallConfidence = j.OverallConfidence,
            ProcessingTimeSeconds = j.ProcessingTimeSeconds,
            Mode = j.Mode.ToString(),
            LanguageDetected = j.LanguageDetected,
            HasSummary = j.Summary != null,
            CreatedAt = j.CreatedAt,
            CompletedAt = j.CompletedAt
        }).OrderByDescending(j => j.CreatedAt).ToList();
    }

    public async Task<IActionResult> OnPostDeleteAsync(Guid id)
    {
        var userId = _userManager.GetUserId(User);
        var job = await _uow.TranscriptionJobs.GetByIdAsync(id);

        if (job != null && job.UserId == userId)
        {
            _uow.TranscriptionJobs.Remove(job);
            await _uow.SaveChangesAsync();
        }

        return RedirectToPage();
    }
}
