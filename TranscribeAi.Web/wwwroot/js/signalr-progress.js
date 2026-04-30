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

    const mediaPlayer = document.getElementById('mediaPlayer');
    const transcriptArea = document.getElementById('transcriptArea');

    // ── Click to Seek ──
    document.addEventListener('click', (e) => {
        const timestamp = e.target.closest('.timestamp');
        if (timestamp && mediaPlayer) {
            const startTime = parseFloat(timestamp.dataset.start);
            if (!isNaN(startTime)) {
                mediaPlayer.currentTime = startTime;
                mediaPlayer.play();
                
                // Highlight active segment
                document.querySelectorAll('.segment').forEach(s => s.classList.remove('active-segment'));
                timestamp.closest('.segment').classList.add('active-segment');
            }
        }
    });

    connection.on("OnSegmentReceived", (jId, segment) => {
        if (jId !== jobId || !transcriptArea) return;

        // Remove placeholder
        const placeholder = transcriptArea.querySelector('h3');
        if (placeholder && placeholder.textContent.includes('progress')) {
            transcriptArea.innerHTML = '';
        }

        const segmentDiv = document.createElement('div');
        segmentDiv.className = 'segment';
        segmentDiv.style.opacity = '0';
        segmentDiv.style.transition = 'opacity 0.5s ease';
        
        // Format MM:SS
        const minutes = Math.floor(segment.start / 60);
        const seconds = Math.floor(segment.start % 60);
        const timestamp = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        
        segmentDiv.innerHTML = `
            <div class="speaker-col">
                <div class="speaker-tag">Speaker</div>
                <div class="timestamp" data-start="${segment.start}" style="cursor: pointer; color: var(--accent-primary); font-weight: 700;">
                    ${timestamp}
                </div>
            </div>
            <div class="text-col">
                ${segment.text}
            </div>
        `;
        
        transcriptArea.appendChild(segmentDiv);
        setTimeout(() => segmentDiv.style.opacity = '1', 10);
        
        // Only auto-scroll if user is near bottom
        const threshold = 150;
        const isAtBottom = (window.innerHeight + window.scrollY) >= (document.body.offsetHeight - threshold);
        if (isAtBottom) {
            window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
        }
    });

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
