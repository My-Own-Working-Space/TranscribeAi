using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;
using System.ComponentModel.DataAnnotations;
using TranscribeAi.BusinessObject.Entities;
using TranscribeAi.BusinessObject.Enums;
using TranscribeAi.DataAccessLayer.Repositories.Interfaces;
using TranscribeAi.Services.Interfaces;
using TranscribeAi.Web.Configuration;
using Microsoft.Extensions.Options;
using Microsoft.AspNetCore.Authorization;

namespace TranscribeAi.Web.Pages.Jobs;

[Authorize]
[RequestFormLimits(MultipartBodyLengthLimit = 209715200)] // 200MB
[RequestSizeLimit(209715200)]
public class CreateModel : PageModel
{
    private readonly IUnitOfWork _uow;
    private readonly UserManager<ApplicationUser> _userManager;
    private readonly IJobQueueService _queue;
    private readonly TranscribeAiOptions _options;
    private readonly IWebHostEnvironment _env;
    private readonly ILogger<CreateModel> _logger;

    public CreateModel(
        IUnitOfWork uow,
        UserManager<ApplicationUser> userManager,
        IJobQueueService queue,
        IOptions<TranscribeAiOptions> options,
        IWebHostEnvironment env,
        ILogger<CreateModel> logger)
    {
        _uow = uow;
        _userManager = userManager;
        _queue = queue;
        _options = options.Value;
        _env = env;
        _logger = logger;
    }

    [BindProperty]
    [Required(ErrorMessage = "Please select a file to upload.")]
    [Display(Name = "Audio/Video File")]
    public IFormFile? UploadedFile { get; set; }

    [BindProperty]
    [Display(Name = "Job Mode")]
    public JobMode Mode { get; set; } = JobMode.Standard;

    [BindProperty]
    [Display(Name = "Language (Optional)")]
    [StringLength(10)]
    public string? Language { get; set; }

    public void OnGet()
    {
    }

    public async Task<IActionResult> OnPostAsync()
    {
        _logger.LogInformation("POST /Jobs/Create received. UploadedFile is null: {IsNull}, Request.Form.Files Count: {FileCount}", 
            UploadedFile == null, Request.Form.Files.Count);
        
        foreach(var file in Request.Form.Files)
        {
            _logger.LogInformation("Found file in Request.Form.Files: Name={Name}, FileName={FileName}, Length={Length}", 
                file.Name, file.FileName, file.Length);
        }

        if (!ModelState.IsValid)
        {
            _logger.LogWarning("ModelState is invalid. Count: {Count}", ModelState.ErrorCount);
            foreach (var key in ModelState.Keys)
            {
                var entry = ModelState[key];
                foreach (var error in entry.Errors)
                {
                    _logger.LogWarning("Validation Error - Key: '{Key}', Error: '{ErrorMessage}'", key, error.ErrorMessage);
                }
            }
            return Page();
        }

        var userId = _userManager.GetUserId(User);
        if (userId == null) return Unauthorized();

        // 1. Validate file extension
        var ext = Path.GetExtension(UploadedFile!.FileName).ToLower().TrimStart('.');
        if (!_options.SupportedFormats.Contains(ext))
        {
            ModelState.AddModelError(nameof(UploadedFile), $"Unsupported file format. Supported: {string.Join(", ", _options.SupportedFormats)}");
            return Page();
        }

        // 2. Create Job entity
        var jobId = Guid.NewGuid();
        var uploadDir = Path.Combine(_env.ContentRootPath, _options.TempUploadDir);
        if (!Directory.Exists(uploadDir)) Directory.CreateDirectory(uploadDir);

        var fileName = $"{jobId}_{UploadedFile.FileName}";
        var filePath = Path.Combine(uploadDir, fileName);

        var job = new TranscriptionJob
        {
            Id = jobId,
            UserId = userId,
            Status = JobStatus.Queued,
            OriginalFilename = UploadedFile.FileName,
            StoragePath = filePath,
            FileSizeBytes = (int)UploadedFile.Length,
            Mode = Mode
        };

        // 3. Save file to disk
        try
        {
            using (var stream = new FileStream(filePath, FileMode.Create))
            {
                await UploadedFile.CopyToAsync(stream);
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to save uploaded file for job {JobId}", jobId);
            ModelState.AddModelError(string.Empty, "An error occurred while saving the file. Please try again.");
            return Page();
        }

        // 4. Persist to DB
        await _uow.TranscriptionJobs.AddAsync(job);
        await _uow.SaveChangesAsync();

        // 5. Enqueue for background processing
        await _queue.EnqueueAsync(new TranscriptionJobRequest
        {
            JobId = jobId,
            UserId = userId,
            FilePath = filePath,
            Language = Language,
            Mode = Mode
        });

        _logger.LogInformation("Job {JobId} enqueued for user {UserId}", jobId, userId);

        return RedirectToPage("./Details", new { id = jobId });
    }
}
