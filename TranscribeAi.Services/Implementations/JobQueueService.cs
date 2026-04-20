using System.Threading.Channels;

namespace TranscribeAi.Services.Implementations;

/// <summary>
/// Async job queue using System.Threading.Channels — lock-free, bounded, back-pressure aware.
/// Producer: Razor Pages enqueue jobs.
/// Consumer: Worker Service dequeues and processes.
/// </summary>
public sealed class JobQueueService : IJobQueueService
{
    private readonly Channel<TranscriptionJobRequest> _channel;

    public JobQueueService()
    {
        var options = new BoundedChannelOptions(capacity: 100)
        {
            FullMode = BoundedChannelFullMode.Wait
        };
        _channel = Channel.CreateBounded<TranscriptionJobRequest>(options);
    }

    public async ValueTask EnqueueAsync(TranscriptionJobRequest request, CancellationToken ct = default)
    {
        await _channel.Writer.WriteAsync(request, ct);
    }

    public async ValueTask<TranscriptionJobRequest> DequeueAsync(CancellationToken ct = default)
    {
        return await _channel.Reader.ReadAsync(ct);
    }
}
