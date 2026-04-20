using System.Text;
using DocumentFormat.OpenXml;
using DocumentFormat.OpenXml.Packaging;
using DocumentFormat.OpenXml.Wordprocessing;

namespace TranscribeAi.Services.Implementations;

/// <summary>
/// Export service — generates TXT, SRT, and DOCX files from transcription data.
/// </summary>
public sealed class ExportService : IExportService
{
    private readonly IUnitOfWork _uow;

    public ExportService(IUnitOfWork uow)
    {
        _uow = uow;
    }

    public async Task<byte[]> ExportAsTxtAsync(Guid jobId, CancellationToken ct = default)
    {
        var job = await GetJobOrThrowAsync(jobId, ct);
        var segments = DeserializeSegments(job.SegmentsJson);

        var sb = new StringBuilder();
        sb.AppendLine($"TranscribeAI — Transcript Export");
        sb.AppendLine($"File: {job.OriginalFilename ?? "Unknown"}");
        sb.AppendLine($"Date: {job.CreatedAt:yyyy-MM-dd HH:mm} UTC");
        sb.AppendLine($"Language: {job.LanguageDetected ?? "auto"}");
        sb.AppendLine($"Confidence: {job.OverallConfidence:P1}");
        sb.AppendLine(new string('─', 60));
        sb.AppendLine();

        if (segments.Count > 0)
        {
            foreach (var seg in segments)
                sb.AppendLine($"[{FormatTimestamp(seg.Start)} → {FormatTimestamp(seg.End)}]  {seg.Text}");
        }
        else
        {
            sb.AppendLine(job.Transcript);
        }

        return Encoding.UTF8.GetBytes(sb.ToString());
    }

    public async Task<byte[]> ExportAsSrtAsync(Guid jobId, CancellationToken ct = default)
    {
        var job = await GetJobOrThrowAsync(jobId, ct);
        var segments = DeserializeSegments(job.SegmentsJson);

        var sb = new StringBuilder();
        int idx = 1;
        foreach (var seg in segments)
        {
            sb.AppendLine(idx.ToString());
            sb.AppendLine($"{FormatSrtTimestamp(seg.Start)} --> {FormatSrtTimestamp(seg.End)}");
            sb.AppendLine(seg.Text);
            sb.AppendLine();
            idx++;
        }

        return Encoding.UTF8.GetBytes(sb.ToString());
    }

    public async Task<byte[]> ExportAsDocxAsync(Guid jobId, CancellationToken ct = default)
    {
        var job = await GetJobOrThrowAsync(jobId, ct);
        var segments = DeserializeSegments(job.SegmentsJson);

        using var ms = new MemoryStream();
        using (var doc = WordprocessingDocument.Create(ms, WordprocessingDocumentType.Document))
        {
            var mainPart = doc.AddMainDocumentPart();
            mainPart.Document = new Document();
            var body = mainPart.Document.AppendChild(new Body());

            // Title
            AddParagraph(body, "TranscribeAI — Transcript", true, "28");

            // Metadata
            AddParagraph(body, $"File: {job.OriginalFilename ?? "Unknown"}", false, "20");
            AddParagraph(body, $"Date: {job.CreatedAt:yyyy-MM-dd HH:mm} UTC", false, "20");
            AddParagraph(body, $"Language: {job.LanguageDetected ?? "auto"} | Confidence: {job.OverallConfidence:P1}", false, "20");
            AddParagraph(body, "", false, "20"); // spacer

            // Transcript
            AddParagraph(body, "Transcript", true, "24");

            if (segments.Count > 0)
            {
                foreach (var seg in segments)
                {
                    var p = body.AppendChild(new Paragraph());
                    var timeRun = new Run(new RunProperties(
                        new Bold(), new FontSize { Val = "18" }, new Color { Val = "666666" }),
                        new Text($"[{FormatTimestamp(seg.Start)}] ") { Space = SpaceProcessingModeValues.Preserve });
                    var textRun = new Run(new RunProperties(new FontSize { Val = "22" }),
                        new Text(seg.Text));
                    p.Append(timeRun, textRun);
                }
            }
            else
            {
                AddParagraph(body, job.Transcript, false, "22");
            }

            mainPart.Document.Save();
        }

        return ms.ToArray();
    }

    // ── Helpers ──

    private async Task<TranscriptionJob> GetJobOrThrowAsync(Guid jobId, CancellationToken ct)
    {
        return await _uow.TranscriptionJobs.GetByIdAsync(jobId, ct)
            ?? throw new InvalidOperationException("Job not found");
    }

    private static List<SegmentDto> DeserializeSegments(string json)
    {
        try { return JsonSerializer.Deserialize<List<SegmentDto>>(json) ?? new(); }
        catch { return new(); }
    }

    private static void AddParagraph(Body body, string text, bool bold, string fontSize)
    {
        var p = body.AppendChild(new Paragraph());
        var rp = new RunProperties(new FontSize { Val = fontSize });
        if (bold) rp.Append(new Bold());
        p.Append(new Run(rp, new Text(text)));
    }

    private static string FormatTimestamp(double seconds)
    {
        var ts = TimeSpan.FromSeconds(seconds);
        return ts.Hours > 0 ? $"{ts:hh\\:mm\\:ss}" : $"{ts:mm\\:ss}";
    }

    private static string FormatSrtTimestamp(double seconds)
    {
        var h = (int)(seconds / 3600);
        var m = (int)(seconds % 3600 / 60);
        var s = (int)(seconds % 60);
        var ms = (int)((seconds - Math.Floor(seconds)) * 1000);
        return $"{h:D2}:{m:D2}:{s:D2},{ms:D3}";
    }
}
