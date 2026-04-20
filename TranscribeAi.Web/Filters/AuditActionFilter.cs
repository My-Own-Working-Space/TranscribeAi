using Microsoft.AspNetCore.Mvc.Filters;
using TranscribeAi.BusinessObject.Enums;
using TranscribeAi.Services.Interfaces;

namespace TranscribeAi.Web.Filters;

/// <summary>
/// Action filter that automatically logs security-relevant actions to the audit log.
/// </summary>
public sealed class AuditActionFilter : IAsyncActionFilter
{
    private readonly IAuditService _audit;
    private readonly AuditAction _action;
    private readonly string? _detailsTemplate;

    public AuditActionFilter(IAuditService audit, AuditAction action, string? detailsTemplate = null)
    {
        _audit = audit;
        _action = action;
        _detailsTemplate = detailsTemplate;
    }

    public async Task OnActionExecutionAsync(ActionExecutingContext context, ActionExecutionDelegate next)
    {
        // Execute the action first
        var resultContext = await next();

        // Only log successful actions (or if we want to log attempts, we can do it before next())
        if (resultContext.Exception == null)
        {
            var userId = context.HttpContext.User.FindFirst(System.Security.Claims.ClaimTypes.NameIdentifier)?.Value;
            if (userId != null)
            {
                var details = _detailsTemplate;
                
                // Basic template replacement
                if (details != null && context.ActionArguments.TryGetValue("id", out var id))
                {
                    details = details.Replace("{id}", id?.ToString());
                }

                var ip = context.HttpContext.Connection.RemoteIpAddress?.ToString();
                var ua = context.HttpContext.Request.Headers["User-Agent"].ToString();

                await _audit.LogAsync(userId, _action, details, ip, ua);
            }
        }
    }
}

/// <summary>
/// Attribute to apply the AuditActionFilter to a page or action.
/// </summary>
public sealed class AuditAttribute : TypeFilterAttribute
{
    public AuditAttribute(AuditAction action, string? details = null) 
        : base(typeof(AuditActionFilter))
    {
        Arguments = new object[] { action, details ?? string.Empty };
    }
}
