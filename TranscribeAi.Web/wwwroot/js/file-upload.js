/* ═══════════════════════════════════════════════════════════════
   TranscribeAI — File Upload Client Logic
   Handles drag-and-drop, file selection UI, and upload progress
   ═══════════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const fileInfo = document.getElementById('fileInfo');
    const fileNameDisplay = document.getElementById('fileName');
    const fileSizeDisplay = document.getElementById('fileSize');
    const removeFileBtn = document.getElementById('removeFile');
    const uploadForm = document.getElementById('uploadForm');
    const progressContainer = document.getElementById('uploadProgress');
    const progressBarFill = document.getElementById('uploadBar');
    const progressPercent = document.getElementById('uploadPercent');
    const submitBtn = document.getElementById('submitBtn');

    if (!dropZone || !fileInput) return;

    // ── File Selection ──

    dropZone.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', (e) => {
        handleFiles(e.target.files);
    });

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('drag-over');
    });

    ['dragleave', 'dragend'].forEach(type => {
        dropZone.addEventListener(type, () => {
            dropZone.classList.remove('drag-over');
        });
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        if (e.dataTransfer.files.length) {
            fileInput.files = e.dataTransfer.files;
            handleFiles(e.dataTransfer.files);
        }
    });

    removeFileBtn.addEventListener('click', () => {
        fileInput.value = '';
        fileInfo.style.display = 'none';
        dropZone.style.display = 'block';
    });

    function handleFiles(files) {
        if (files.length === 0) return;
        const file = files[0];

        fileNameDisplay.textContent = file.name;
        fileSizeDisplay.textContent = formatBytes(file.size);

        fileInfo.style.display = 'flex';
        dropZone.style.display = 'none';
    }

    function formatBytes(bytes, decimals = 2) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }

    // ── XHR Upload with Progress ──

    uploadForm.addEventListener('submit', (e) => {
        // We use default form submission for simplicity in this demo, 
        // but normally we'd switch to AJAX/Fetch if we want accurate progress for large files.
        // For now, we'll just show the progress container when the button is clicked.
        
        if (fileInput.files.length > 0) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="pulse">⏳</span> Processing...';
            progressContainer.style.display = 'block';
            
            // Artificial progress simulation for the initial stage
            let current = 0;
            const interval = setInterval(() => {
                current += Math.random() * 5;
                if (current > 95) {
                    clearInterval(interval);
                    current = 95;
                }
                progressBarFill.style.width = current + '%';
                progressPercent.textContent = Math.round(current) + '%';
            }, 500);
        }
    });
});
