using System.Net.Http.Headers;

namespace TranscribeAi.Services.Implementations;

/// <summary>
/// Groq Cloud API speech-to-text provider using whisper-large-v3-turbo.
/// Sends audio via multipart POST to Groq's OpenAI-compatible transcription endpoint.
/// </summary>
public sealed class GroqTranscriptionProvider : ITranscriptionProvider
{
    private readonly HttpClient _httpClient;
    private readonly ILogger<GroqTranscriptionProvider> _logger;

    private const string TranscribeUrl = "https://api.groq.com/openai/v1/audio/transcriptions";

    public GroqTranscriptionProvider(IHttpClientFactory httpClientFactory,
        ILogger<GroqTranscriptionProvider> logger)
    {
        _httpClient = httpClientFactory.CreateClient("GroqApi");
        _logger = logger;
    }

    public async Task<TranscriptionResultDto> TranscribeAsync(string filePath,
        string? language = null, CancellationToken ct = default)
    {
        var startTime = DateTime.UtcNow;

        using var form = new MultipartFormDataContent();
        await using var fileStream = File.OpenRead(filePath);

        var fileContent = new StreamContent(fileStream);
        fileContent.Headers.ContentType = new MediaTypeHeaderValue("audio/mpeg");
        form.Add(fileContent, "file", Path.GetFileName(filePath));
        form.Add(new StringContent("whisper-large-v3-turbo"), "model");
        form.Add(new StringContent("verbose_json"), "response_format");

        if (!string.IsNullOrEmpty(language))
            form.Add(new StringContent(language), "language");

        _logger.LogInformation("Sending audio to Groq STT API: {FileName}", Path.GetFileName(filePath));

        var response = await _httpClient.PostAsync(TranscribeUrl, form, ct);
        response.EnsureSuccessStatusCode();

        var json = await response.Content.ReadAsStringAsync(ct);
        using var doc = JsonDocument.Parse(json);
        var root = doc.RootElement;

        var fullText = root.GetProperty("text").GetString() ?? string.Empty;
        var detectedLang = root.TryGetProperty("language", out var langProp) ? langProp.GetString() ?? "" : "";
        var duration = root.TryGetProperty("duration", out var durProp) ? durProp.GetDouble() : 0;

        var segments = new List<SegmentDto>();
        double confSum = 0;

        if (root.TryGetProperty("segments", out var segArray))
        {
            int idx = 0;
            foreach (var seg in segArray.EnumerateArray())
            {
                var avgLogProb = seg.TryGetProperty("avg_logprob", out var lp) ? lp.GetDouble() : -1.0;
                var confidence = Math.Round(Math.Exp(Math.Max(avgLogProb, -1.0)), 4);
                confSum += confidence;

                segments.Add(new SegmentDto
                {
                    Index = idx++,
                    Start = Math.Round(seg.GetProperty("start").GetDouble(), 2),
                    End = Math.Round(seg.GetProperty("end").GetDouble(), 2),
                    Text = seg.GetProperty("text").GetString()?.Trim() ?? string.Empty,
                    Confidence = confidence
                });
            }
        }

        var processingTime = (DateTime.UtcNow - startTime).TotalSeconds;

        return new TranscriptionResultDto
        {
            FullText = fullText.Trim(),
            Segments = segments,
            OverallConfidence = segments.Count > 0 ? Math.Round(confSum / segments.Count, 4) : 0,
            DurationSeconds = duration > 0 ? duration : (segments.LastOrDefault()?.End ?? 0),
            ProcessingTimeSeconds = Math.Round(processingTime, 2),
            LanguageDetected = detectedLang,
            Model = "whisper-large-v3-turbo"
        };
    }
}
