/* ═══════════════════════════════════════════════════════════════
   TranscribeAI — SignalR Progress Client
   Listens for real-time transcription updates and completes the UI
   ═══════════════════════════════════════════════════════════════ */

if (typeof signalR !== 'undefined' && typeof jobId !== 'undefined') {
    const connection = new signalR.HubConnectionBuilder()
        .withUrl("/hubs/transcription")
        .withAutomaticReconnect()
        .build();

    const progressSection = document.getElementById('processingStates');
    const progressBar = document.getElementById('progressBar');
    const progressPercent = document.getElementById('progressPercent');
    const progressStep = document.getElementById('progressStep');
    const progressDetail = document.getElementById('progressDetail');
    const jobStatusBadge = document.getElementById('jobStatusBadge');

    // ── Hub Event Handlers ──

    connection.on("OnProgressUpdate", (jId, percent, step, detail) => {
        if (jId !== jobId) return;

        console.log(`[SignalR] Job ${jId} progress: ${percent}% - ${step}`);
        
        if (progressSection) progressSection.style.display = 'block';
        if (progressBar) progressBar.style.width = percent + '%';
        if (progressPercent) progressPercent.textContent = percent + '%';
        if (progressStep) progressStep.textContent = step;
        if (progressDetail) progressDetail.textContent = detail;
        
        if (jobStatusBadge) {
            jobStatusBadge.className = 'badge badge-processing';
            jobStatusBadge.innerHTML = '<span class="pulse">●</span> Processing';
        }
    });

    connection.on("OnJobCompleted", (jId) => {
        if (jId !== jobId) return;

        console.log(`[SignalR] Job ${jId} completed!`);
        
        if (progressStep) progressStep.textContent = "Processing complete!";
        if (progressDetail) progressDetail.textContent = "Refreshing page to show results...";
        if (progressBar) progressBar.style.width = '100%';
        if (progressPercent) progressPercent.textContent = '100%';
        
        if (jobStatusBadge) {
            jobStatusBadge.className = 'badge badge-completed';
            jobStatusBadge.textContent = 'Completed';
        }

        // Notification and refresh
        setTimeout(() => {
            window.location.reload();
        }, 1500);
    });

    connection.on("OnJobFailed", (jId, error) => {
        if (jId !== jobId) return;

        console.error(`[SignalR] Job ${jId} failed: ${error}`);
        
        if (progressStep) progressStep.textContent = "Transcription failed";
        if (progressDetail) progressDetail.textContent = error || "An unexpected error occurred.";
        if (progressBar) progressBar.style.background = 'var(--danger)';
        
        if (jobStatusBadge) {
            jobStatusBadge.className = 'badge badge-failed';
            jobStatusBadge.textContent = 'Failed';
        }
    });

    // ── Lifecycle ──

    connection.start()
        .then(() => {
            console.log("[SignalR] Connected to TranscriptionHub");
            // Join the specific group for this job
            connection.invoke("JoinJobGroup", jobId)
                .catch(err => console.error(err.toString()));
        })
        .catch(err => console.error(err.toString()));
}
