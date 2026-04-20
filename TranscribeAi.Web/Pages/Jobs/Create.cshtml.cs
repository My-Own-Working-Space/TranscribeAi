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
    public InputModel Input { get; set; } = new();

    public class InputModel
    {
        [Required]
        [Display(Name = "Audio/Video File")]
        public IFormFile? File { get; set; }

        [Display(Name = "Job Mode")]
        public JobMode Mode { get; set; } = JobMode.Standard;

        [Display(Name = "Language (Optional)")]
        [StringLength(10)]
        public string? Language { get; set; }
    }

    public void OnGet()
    {
    }

    public async Task<IActionResult> OnPostAsync()
    {
        if (Input.File == null || Input.File.Length == 0)
        {
            ModelState.AddModelError("Input.File", "Please select a file to upload.");
        }

        if (!ModelState.IsValid)
        {
            return Page();
        }

        var userId = _userManager.GetUserId(User);
        if (userId == null) return Unauthorized();

        // 1. Validate file extension
        var ext = Path.GetExtension(Input.File!.FileName).ToLower().TrimStart('.');
        if (!_options.SupportedFormats.Contains(ext))
        {
            ModelState.AddModelError("Input.File", $"Unsupported file format. Supported: {string.Join(", ", _options.SupportedFormats)}");
            return Page();
        }

        // 2. Create Job entity
        var jobId = Guid.NewGuid();
        var uploadDir = Path.Combine(_env.ContentRootPath, _options.TempUploadDir);
        if (!Directory.Exists(uploadDir)) Directory.CreateDirectory(uploadDir);

        var fileName = $"{jobId}_{Input.File.FileName}";
        var filePath = Path.Combine(uploadDir, fileName);

        var job = new TranscriptionJob
        {
            Id = jobId,
            UserId = userId,
            Status = JobStatus.Queued,
            OriginalFilename = Input.File.FileName,
            StoragePath = filePath,
            FileSizeBytes = (int)Input.File.Length,
            Mode = Input.Mode
        };

        // 3. Save file to disk
        try
        {
            using (var stream = new FileStream(filePath, FileMode.Create))
            {
                await Input.File.CopyToAsync(stream);
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
            Language = Input.Language,
            Mode = Input.Mode
        });

        _logger.LogInformation("Job {JobId} enqueued for user {UserId}", jobId, userId);

        return RedirectToPage("./Details", new { id = jobId });
    }
}
