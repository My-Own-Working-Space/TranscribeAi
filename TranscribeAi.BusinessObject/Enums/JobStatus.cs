namespace TranscribeAi.BusinessObject.Enums;

/// <summary>
/// Represents the lifecycle status of a transcription job.
/// </summary>
public enum JobStatus
{
    Queued = 0,
    Processing = 1,
    Completed = 2,
    Failed = 3
}
