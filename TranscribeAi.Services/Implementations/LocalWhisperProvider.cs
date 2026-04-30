using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using TranscribeAi.Services.Configuration;
using TranscribeAi.Services.DTOs;
using TranscribeAi.Services.Interfaces;

namespace TranscribeAi.Services.Implementations;

/// <summary>
/// Connects to a local Whisper API (FastAPI) running at localhost:8000.
/// </summary>
public sealed class LocalWhisperProvider : ITranscriptionProvider
{
    private readonly HttpClient _httpClient;
    private readonly TranscribeAiOptions _options;
    private readonly ILogger<LocalWhisperProvider> _logger;

    public LocalWhisperProvider(
        IHttpClientFactory httpClientFactory,
        IOptions<TranscribeAiOptions> options,
        ILogger<LocalWhisperProvider> logger)
    {
        _httpClient = httpClientFactory.CreateClient();
        _httpClient.Timeout = TimeSpan.FromMinutes(10); // Local CPU inference can be slow
        _options = options.Value;
        _logger = logger;
    }

    public async Task<TranscriptionResultDto> TranscribeAsync(string filePath,
        string? language = null, Action<SegmentDto>? onSegmentTranscribed = null, CancellationToken ct = default)
    {
        var startTime = DateTime.UtcNow;
        _logger.LogInformation("Calling LOCAL Whisper API at {Url} for file {FileName}", 
            _options.LocalWhisperUrl, Path.GetFileName(filePath));

        var fullTextBuilder = new StringBuilder();
        var segments = new List<SegmentDto>();
        var detectedLang = "unknown";
        int segmentIndex = 0;

        try
        {
            using var form = new MultipartFormDataContent();
            await using var fileStream = File.OpenRead(filePath);
            var fileContent = new StreamContent(fileStream);
            fileContent.Headers.ContentType = new MediaTypeHeaderValue("audio/mpeg");
            form.Add(fileContent, "file", Path.GetFileName(filePath));

            using var request = new HttpRequestMessage(HttpMethod.Post, _options.LocalWhisperUrl) { Content = form };
            using var response = await _httpClient.SendAsync(request, HttpCompletionOption.ResponseHeadersRead, ct);
            response.EnsureSuccessStatusCode();

            using var stream = await response.Content.ReadAsStreamAsync(ct);
            using var reader = new StreamReader(stream);

            while (!reader.EndOfStream)
            {
                var line = await reader.ReadLineAsync(ct);
                if (string.IsNullOrWhiteSpace(line)) continue;

                using var doc = JsonDocument.Parse(line);
                var root = doc.RootElement;
                var type = root.GetProperty("type").GetString();

                if (type == "info")
                {
                    detectedLang = root.TryGetProperty("language", out var lp) ? lp.GetString() ?? "unknown" : "unknown";
                }
                else if (type == "segment")
                {
                    var segment = new SegmentDto
                    {
                        Index = segmentIndex++,
                        Start = root.GetProperty("start").GetDouble(),
                        End = root.GetProperty("end").GetDouble(),
                        Text = root.GetProperty("text").GetString() ?? string.Empty,
                        Confidence = 1.0
                    };

                    segments.Add(segment);
                    fullTextBuilder.Append(segment.Text).Append(" ");
                    
                    // Callback for real-time UI updates
                    onSegmentTranscribed?.Invoke(segment);
                }
                else if (type == "error")
                {
                    var msg = root.GetProperty("message").GetString();
                    throw new Exception($"Local Whisper API Error: {msg}");
                }
            }

            var processingTime = (DateTime.UtcNow - startTime).TotalSeconds;

            return new TranscriptionResultDto
            {
                FullText = fullTextBuilder.ToString().Trim(),
                Segments = segments,
                OverallConfidence = 1.0,
                DurationSeconds = segments.LastOrDefault()?.End ?? processingTime,
                ProcessingTimeSeconds = Math.Round(processingTime, 2),
                LanguageDetected = detectedLang,
                Model = "local-faster-whisper-stream"
            };
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error calling local Whisper API at {Url}", _options.LocalWhisperUrl);
            throw;
        }
    }
}
