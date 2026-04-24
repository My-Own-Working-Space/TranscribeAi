using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;
using TranscribeAi.BusinessObject.Entities;

namespace TranscribeAi.Web.Pages.Account;

[AllowAnonymous]
public class RegisterConfirmationModel : PageModel
{
    private readonly UserManager<ApplicationUser> _userManager;

    public RegisterConfirmationModel(UserManager<ApplicationUser> userManager)
    {
        _userManager = userManager;
    }

    [BindProperty(SupportsGet = true)]
    public string? Email { get; set; }

    public IActionResult OnGet()
    {
        if (Email == null) return RedirectToPage("/Index");
        return Page();
    }

    public async Task<IActionResult> OnPostAsync()
    {
        if (Email == null) return RedirectToPage("/Index");

        var user = await _userManager.FindByEmailAsync(Email);
        if (user != null)
        {
            var token = await _userManager.GenerateEmailConfirmationTokenAsync(user);
            await _userManager.ConfirmEmailAsync(user, token);
            return RedirectToPage("Login", new { msg = "Email verified successfully. You can now log in." });
        }

        return Page();
    }
}
