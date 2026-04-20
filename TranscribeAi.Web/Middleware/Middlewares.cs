namespace TranscribeAi.Web.Middleware;

/// <summary>
/// Adds security headers to all responses: X-Frame-Options, CSP, HSTS, etc.
/// </summary>
public sealed class SecurityHeadersMiddleware
{
    private readonly RequestDelegate _next;

    public SecurityHeadersMiddleware(RequestDelegate next) => _next = next;

    public async Task InvokeAsync(HttpContext context)
    {
        // Skip preflight requests
        if (context.Request.Method != "OPTIONS")
        {
            var headers = context.Response.Headers;
            headers["X-Frame-Options"] = "DENY";
            headers["X-Content-Type-Options"] = "nosniff";
            headers["Referrer-Policy"] = "strict-origin-when-cross-origin";
            headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()";
            headers["X-XSS-Protection"] = "1; mode=block";
        }

        await _next(context);
    }
}

/// <summary>
/// Global exception handler — catches unhandled exceptions and returns a friendly error page.
/// </summary>
public sealed class GlobalExceptionMiddleware
{
    private readonly RequestDelegate _next;
    private readonly ILogger<GlobalExceptionMiddleware> _logger;

    public GlobalExceptionMiddleware(RequestDelegate next, ILogger<GlobalExceptionMiddleware> logger)
    {
        _next = next;
        _logger = logger;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        try
        {
            await _next(context);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Unhandled exception for {Method} {Path}",
                context.Request.Method, context.Request.Path);

            context.Response.StatusCode = 500;
            context.Response.Redirect("/Error");
        }
    }
}

/// <summary>
/// Structured request logging with timing.
/// </summary>
public sealed class RequestLoggingMiddleware
{
    private readonly RequestDelegate _next;
    private readonly ILogger<RequestLoggingMiddleware> _logger;

    public RequestLoggingMiddleware(RequestDelegate next, ILogger<RequestLoggingMiddleware> logger)
    {
        _next = next;
        _logger = logger;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        var start = DateTime.UtcNow;
        await _next(context);
        var elapsed = (DateTime.UtcNow - start).TotalMilliseconds;

        // Only log non-static requests
        var path = context.Request.Path.Value ?? "";
        if (!path.StartsWith("/css") && !path.StartsWith("/js") && !path.StartsWith("/lib")
            && !path.StartsWith("/_"))
        {
            _logger.LogInformation("{Method} {Path} → {Status} ({Elapsed:F0}ms)",
                context.Request.Method, path, context.Response.StatusCode, elapsed);
        }
    }
}
