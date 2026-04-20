using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;
using TranscribeAi.BusinessObject.Entities;
using TranscribeAi.Services.Interfaces;

namespace TranscribeAi.Web.Pages.Admin;

[Authorize(Roles = "Admin")]
public class AuditLogModel : PageModel
{
    private readonly IAuditService _audit;

    public AuditLogModel(IAuditService audit)
    {
        _audit = audit;
    }

    public IReadOnlyList<AuditLog> Logs { get; set; } = new List<AuditLog>();

    public async Task OnGetAsync()
    {
        Logs = await _audit.GetRecentLogsAsync(200);
    }
}
