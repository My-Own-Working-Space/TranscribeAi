using System.Net.Http.Headers;
using System.Text.Json.Serialization;

namespace TranscribeAi.Services.Implementations;

/// <summary>
/// Groq Cloud API wrapper for LLM chat completions.
/// Uses IHttpClientFactory for connection pooling and resilience.
/// </summary>
public sealed class GroqLlmService : ILlmService
{
    private readonly HttpClient _httpClient;
    private readonly ILogger<GroqLlmService> _logger;
    private readonly string _model;

    private const string BaseUrl = "https://api.groq.com/openai/v1/chat/completions";

    public GroqLlmService(IHttpClientFactory httpClientFactory, ILogger<GroqLlmService> logger,
        IOptions<GroqOptions> options)
    {
        _httpClient = httpClientFactory.CreateClient("GroqApi");
        _logger = logger;
        _model = options.Value.Model;
    }

    public async Task<string> ChatAsync(string systemPrompt, string userMessage,
        float temperature = 0.3f, int maxTokens = 4096, CancellationToken ct = default)
    {
        var messages = new List<ChatMessageDto>
        {
            new() { Role = "user", Content = userMessage }
        };
        return await ChatWithHistoryAsync(systemPrompt, messages, temperature, maxTokens, ct);
    }

    public async Task<string> ChatWithHistoryAsync(string systemPrompt, List<ChatMessageDto> messages,
        float temperature = 0.3f, int maxTokens = 2048, CancellationToken ct = default)
    {
        var allMessages = new List<object>
        {
            new { role = "system", content = systemPrompt }
        };
        allMessages.AddRange(messages.Select(m => (object)new { role = m.Role, content = m.Content }));

        var requestBody = new
        {
            model = _model,
            messages = allMessages,
            temperature,
            max_tokens = maxTokens
        };

        var json = JsonSerializer.Serialize(requestBody);
        var content = new StringContent(json, System.Text.Encoding.UTF8, "application/json");

        var response = await _httpClient.PostAsync(BaseUrl, content, ct);
        response.EnsureSuccessStatusCode();

        var responseJson = await response.Content.ReadAsStringAsync(ct);
        using var doc = JsonDocument.Parse(responseJson);

        var result = doc.RootElement
            .GetProperty("choices")[0]
            .GetProperty("message")
            .GetProperty("content")
            .GetString();

        return result ?? string.Empty;
    }

    public JsonDocument? ParseJsonResponse(string text)
    {
        text = text.Trim();

        // Strip markdown code fences
        if (text.StartsWith("```"))
        {
            var lines = text.Split('\n');
            var inner = lines.Skip(1).TakeWhile(l => l.Trim() != "```");
            text = string.Join('\n', inner);
        }

        try
        {
            return JsonDocument.Parse(text);
        }
        catch (JsonException)
        {
            // Try to extract JSON from surrounding text
            var startBrace = text.IndexOf('{');
            var startBracket = text.IndexOf('[');
            var start = (startBrace, startBracket) switch
            {
                (-1, -1) => -1,
                (-1, _) => startBracket,
                (_, -1) => startBrace,
                _ => Math.Min(startBrace, startBracket)
            };

            if (start == -1) return null;

            var closer = text[start] == '{' ? '}' : ']';
            var end = text.LastIndexOf(closer);
            if (end <= start) return null;

            try
            {
                return JsonDocument.Parse(text[start..(end + 1)]);
            }
            catch (JsonException)
            {
                _logger.LogWarning("Failed to parse JSON from LLM response");
                return null;
            }
        }
    }
}
