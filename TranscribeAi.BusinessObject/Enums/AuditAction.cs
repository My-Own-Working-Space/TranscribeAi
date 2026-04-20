namespace TranscribeAi.BusinessObject.Enums;

/// <summary>
/// Security-relevant actions tracked in the audit log.
/// </summary>
public enum AuditAction
{
    Login = 0,
    Logout = 1,
    Register = 2,
    Upload = 3,
    Delete = 4,
    Export = 5,
    AdminAccess = 6,
    SettingsChange = 7
}
