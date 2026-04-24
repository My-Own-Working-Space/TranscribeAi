/* ═══════════════════════════════════════════════════════════════
   TranscribeAI — File Upload Client Logic
   Handles drag-and-drop, file selection UI, and upload progress
   ═══════════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('UploadedFile');
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
    // Click is handled natively by the #UploadedFile input which covers #dropZone (inset: 0)

    fileInput.addEventListener('change', (e) => {
        handleFiles(e.target.files);
    });

    ['dragover', 'dragenter'].forEach(type => {
        [dropZone, fileInput].forEach(el => {
            el.addEventListener(type, (e) => {
                e.preventDefault();
                dropZone.classList.add('drag-over');
            });
        });
    });

    ['dragleave', 'dragend', 'drop'].forEach(type => {
        [dropZone, fileInput].forEach(el => {
            el.addEventListener(type, (e) => {
                dropZone.classList.remove('drag-over');
            });
        });
    });

    fileInput.addEventListener('drop', (e) => {
        if (e.dataTransfer.files.length) {
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

        if (fileNameDisplay) fileNameDisplay.textContent = file.name;
        if (fileSizeDisplay) fileSizeDisplay.textContent = formatBytes(file.size);

        if (fileInfo) fileInfo.style.display = 'flex';
        if (dropZone) dropZone.style.display = 'none';
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
