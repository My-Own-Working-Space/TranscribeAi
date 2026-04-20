using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;
using System.ComponentModel.DataAnnotations;
using TranscribeAi.BusinessObject.Entities;
using TranscribeAi.DataAccessLayer.Repositories.Interfaces;

namespace TranscribeAi.Web.Pages.Account;

[Authorize]
public class ProfileModel : PageModel
{
    private readonly UserManager<ApplicationUser> _userManager;
    private readonly IUnitOfWork _uow;

    public ProfileModel(UserManager<ApplicationUser> userManager, IUnitOfWork uow)
    {
        _userManager = userManager;
        _uow = uow;
    }

    [BindProperty]
    public InputModel Input { get; set; } = new();

    public DashboardStatsDto Stats { get; set; } = new();

    public string? StatusMessage { get; set; }

    public class InputModel
    {
        [Required]
        [Display(Name = "Full Name")]
        public string FullName { get; set; } = string.Empty;

        [Phone]
        [Display(Name = "Phone number")]
        public string? PhoneNumber { get; set; }
    }

    public async Task<IActionResult> OnGetAsync()
    {
        var user = await _userManager.GetUserAsync(User);
        if (user == null)
        {
            return NotFound($"Unable to load user with ID '{_userManager.GetUserId(User)}'.");
        }

        Input = new InputModel
        {
            FullName = user.FullName,
            PhoneNumber = user.PhoneNumber
        };

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

        return Page();
    }

    public async Task<IActionResult> OnPostAsync()
    {
        var user = await _userManager.GetUserAsync(User);
        if (user == null)
        {
            return NotFound($"Unable to load user with ID '{_userManager.GetUserId(User)}'.");
        }

        if (!ModelState.IsValid)
        {
            return Page();
        }

        var fullName = user.FullName;
        if (Input.FullName != fullName)
        {
            user.FullName = Input.FullName;
        }

        var phoneNumber = await _userManager.GetPhoneNumberAsync(user);
        if (Input.PhoneNumber != phoneNumber)
        {
            var setPhoneResult = await _userManager.SetPhoneNumberAsync(user, Input.PhoneNumber);
            if (!setPhoneResult.Succeeded)
            {
                StatusMessage = "Unexpected error when trying to set phone number.";
                return RedirectToPage();
            }
        }

        await _userManager.UpdateAsync(user);

        StatusMessage = "Your profile has been updated";
        return RedirectToPage();
    }
}
