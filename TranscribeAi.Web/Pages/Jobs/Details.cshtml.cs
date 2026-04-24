using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;
using TranscribeAi.BusinessObject.Entities;
using TranscribeAi.DataAccessLayer.Repositories.Interfaces;
using TranscribeAi.Services.DTOs;
using TranscribeAi.Services.Interfaces;

namespace TranscribeAi.Web.Pages.Jobs;

[Authorize]
public class DetailsModel : PageModel
{
    private readonly IUnitOfWork _uow;
    private readonly UserManager<ApplicationUser> _userManager;
    private readonly IChatService _chat;
    private readonly IActionService _action;
    private readonly IExportService _export;
    private readonly ILogger<DetailsModel> _logger;

    public DetailsModel(
        IUnitOfWork uow,
        UserManager<ApplicationUser> userManager,
        IChatService chat,
        IActionService action,
        IExportService export,
        ILogger<DetailsModel> logger)
    {
        _uow = uow;
        _userManager = userManager;
        _chat = chat;
        _action = action;
        _export = export;
        _logger = logger;
    }

    public TranscriptionJob Job { get; set; } = null!;
    public List<SegmentDto> Segments { get; set; } = new();
    public SummaryDto? Summary { get; set; }
    public IReadOnlyList<ActionItemDto> Actions { get; set; } = new List<ActionItemDto>();
    public IReadOnlyList<ChatMessageDto> ChatHistory { get; set; } = new List<ChatMessageDto>();

    public async Task<IActionResult> OnGetAsync(Guid id)
    {
        var userId = _userManager.GetUserId(User);
        if (userId == null) return Unauthorized();

        var job = await _uow.TranscriptionJobs.GetByIdAndUserAsync(id, userId);
        if (job == null) return NotFound();

        Job = job;
        
        try 
        {
            Segments = JsonSerializer.Deserialize<List<SegmentDto>>(job.SegmentsJson) ?? new();
        }
        catch { Segments = new(); }

        if (job.Summary != null)
        {
            Summary = new SummaryDto
            {
                Summary = job.Summary.Summary ?? string.Empty,
                KeyPoints = JsonSerializer.Deserialize<List<string>>(job.Summary.KeyPoints) ?? new(),
                Conclusion = job.Summary.Conclusion ?? string.Empty,
                LlmModel = job.Summary.LlmModel,
                GeneratedAt = job.Summary.GeneratedAt
            };
        }

        Actions = job.ActionItems.Select(a => new ActionItemDto
        {
            Id = a.Id,
            TaskDescription = a.TaskDescription,
            Assignee = a.Assignee,
            Deadline = a.Deadline,
            Priority = a.Priority,
            IsCompleted = a.IsCompleted
        }).ToList();

        ChatHistory = await _chat.GetHistoryAsync(id, userId);

        return Page();
    }

    public async Task<IActionResult> OnPostChatAsync(Guid id, string question)
    {
        _logger.LogInformation("[Chat] Received question for job {JobId}: {Question}", id, question);
        var userId = _userManager.GetUserId(User);
        if (userId == null) return Unauthorized();

        if (string.IsNullOrWhiteSpace(question)) 
        {
            _logger.LogWarning("[Chat] Question was empty for job {JobId}", id);
            return BadRequest();
        }

        var response = await _chat.AskQuestionAsync(id, userId, question);
        _logger.LogInformation("[Chat] Generated answer for job {JobId}", id);
        return new JsonResult(response);
    }

    public async Task<IActionResult> OnGetExportAsync(Guid id, string format)
    {
        var userId = _userManager.GetUserId(User);
        if (userId == null) return Unauthorized();

        var job = await _uow.TranscriptionJobs.GetByIdAndUserAsync(id, userId);
        if (job == null) return NotFound();

        byte[] data;
        string contentType;
        string ext;

        switch (format.ToLower())
        {
            case "txt":
                data = await _export.ExportAsTxtAsync(id);
                contentType = "text/plain";
                ext = "txt";
                break;
            case "srt":
                data = await _export.ExportAsSrtAsync(id);
                contentType = "text/plain";
                ext = "srt";
                break;
            case "docx":
                data = await _export.ExportAsDocxAsync(id);
                contentType = "application/vnd.openxmlformats-officedocument.wordprocessingml.document";
                ext = "docx";
                break;
            default:
                return BadRequest("Invalid format");
        }

        var filename = $"{job.OriginalFilename}_{DateTime.UtcNow:yyyyMMdd}.{ext}";
        return File(data, contentType, filename);
    }
}
