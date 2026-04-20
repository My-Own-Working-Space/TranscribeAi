using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;
using Microsoft.EntityFrameworkCore;
using TranscribeAi.BusinessObject.Entities;
using TranscribeAi.BusinessObject.Enums;
using TranscribeAi.DataAccessLayer.Repositories.Interfaces;

namespace TranscribeAi.Web.Pages.Admin;

[Authorize(Roles = "Admin")]
public class DashboardModel : PageModel
{
    private readonly IUnitOfWork _uow;
    private readonly UserManager<ApplicationUser> _userManager;

    public DashboardModel(IUnitOfWork uow, UserManager<ApplicationUser> userManager)
    {
        _uow = uow;
        _userManager = userManager;
    }

    public int TotalUsers { get; set; }
    public int ActiveJobs { get; set; }
    public int CompletedJobs { get; set; }
    public double TotalSystemMinutes { get; set; }
    public IReadOnlyList<TranscriptionJob> RecentSystemJobs { get; set; } = new List<TranscriptionJob>();

    public async Task OnGetAsync()
    {
        TotalUsers = await _userManager.Users.CountAsync();
        
        var allJobs = await _uow.TranscriptionJobs.GetAllAsync();
        ActiveJobs = allJobs.Count(j => j.Status == JobStatus.Queued || j.Status == JobStatus.Processing);
        CompletedJobs = allJobs.Count(j => j.Status == JobStatus.Completed);
        TotalSystemMinutes = Math.Round(allJobs.Where(j => j.Status == JobStatus.Completed).Sum(j => j.DurationSeconds) / 60.0, 1);

        RecentSystemJobs = allJobs.OrderByDescending(j => j.CreatedAt).Take(10).ToList();
    }
}
