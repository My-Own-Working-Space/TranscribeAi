using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;
using TranscribeAi.BusinessObject.Entities;
using TranscribeAi.DataAccessLayer.Repositories.Interfaces;
using TranscribeAi.Services.DTOs;

namespace TranscribeAi.Web.Pages;

public class IndexModel : PageModel
{
    private readonly ILogger<IndexModel> _logger;
    private readonly UserManager<ApplicationUser> _userManager;
    private readonly IUnitOfWork _uow;

    public IndexModel(ILogger<IndexModel> logger, UserManager<ApplicationUser> userManager, IUnitOfWork uow)
    {
        _logger = logger;
        _userManager = userManager;
        _uow = uow;
    }

    public bool IsAuthenticated => User.Identity?.IsAuthenticated == true;
    public DashboardStatsDto? Stats { get; set; }
    public IReadOnlyList<JobListItemDto> RecentJobs { get; set; } = new List<JobListItemDto>();

    public async Task OnGetAsync()
    {
        if (IsAuthenticated)
        {
            var user = await _userManager.GetUserAsync(User);
            if (user != null)
            {
                var userStats = await _uow.TranscriptionJobs.GetUserStatsAsync(user.Id);
                Stats = new DashboardStatsDto
                {
                    TotalJobs = userStats.Total,
                    CompletedJobs = userStats.Completed,
                    TotalMinutesTranscribed = userStats.TotalMinutes,
                    MinutesUsedThisMonth = user.MonthlyMinutesUsed,
                    MinutesLimit = user.MonthlyMinutesLimit,
                    Plan = user.Plan.ToString()
                };

                var jobs = await _uow.TranscriptionJobs.GetByUserIdAsync(user.Id, 5);
                RecentJobs = jobs.Select(j => new JobListItemDto
                {
                    Id = j.Id,
                    Status = j.Status.ToString(),
                    OriginalFilename = j.OriginalFilename,
                    CreatedAt = j.CreatedAt
                }).ToList();
            }
        }
    }
}
