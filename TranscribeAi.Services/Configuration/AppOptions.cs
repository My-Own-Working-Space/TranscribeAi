namespace TranscribeAi.Services.Configuration;

/// <summary>
/// General application settings.
/// </summary>
public sealed class TranscribeAiOptions
{
    public const string SectionName = "TranscribeAi";

    public string AppName { get; set; } = "TranscribeAI";
    public string AppVersion { get; set; } = "3.0.0";
    public int MaxFileSizeMb { get; set; } = 200;
    public string[] SupportedFormats { get; set; } = ["wav", "mp3", "flac", "ogg", "m4a", "mp4", "mkv", "webm"];
    public string TempUploadDir { get; set; } = "temp_uploads";
}

/// <summary>
/// Groq API specific settings.
/// </summary>
public sealed class GroqOptions
{
    public const string SectionName = "Groq";

    public string ApiKey { get; set; } = string.Empty;
    public string Model { get; set; } = "llama-3.3-70b-versatile";
    public string TranscriptionModel { get; set; } = "whisper-large-v3-turbo";
}
