// contentScript.js - Product-Grade Real-Time Notes Engine

(function () {
    console.log('TranscribeAi: [PRO] Sidebar Engine Loading...');

    let sidebar = null;
    let transcriptColumn = null;
    let notesColumn = null;
    let isRecording = false;
    let notes = [];

    const SidebarUI = {
        create() {
            if (document.getElementById('transcribe-ai-sidebar')) return document.getElementById('transcribe-ai-sidebar');

            const container = document.createElement('div');
            container.id = 'transcribe-ai-sidebar';
            container.innerHTML = `
        <div class="sidebar-header">
          <div class="header-left">
            <span class="header-title">Live Notes</span>
            <div class="status-indicator">
              <div class="dot" id="status-dot"></div>
              <span id="status-text">Idle</span>
            </div>
          </div>
          <button id="close-sidebar">&times;</button>
        </div>
        
        <div class="sidebar-main">
          <div class="column" id="transcript-col">
            <div class="column-header">Transcript</div>
          </div>
          <div class="column" id="notes-col">
            <div class="column-header">
              Notes
              <button id="add-manual-note" class="btn-text-only" style="color:var(--accent-blue)">+ Add</button>
            </div>
          </div>
        </div>

        <div class="sidebar-footer">
          <button id="toggle-record" class="btn-pill primary">Start Recording</button>
          <button id="save-notes" class="btn-pill">Save</button>
          <button id="download-notes" class="btn-pill">Export</button>
        </div>
      `;
            return container;
        },

        addTranscriptItem(text) {
            if (!text || !transcriptColumn) return;
            const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
            const item = document.createElement('div');
            item.className = 'transcript-item';
            item.innerHTML = `
        <span class="item-time">${time}</span>
        <div class="item-text">${text}</div>
      `;
            item.onclick = () => this.addNoteItem(text);
            transcriptColumn.appendChild(item);
            transcriptColumn.scrollTop = transcriptColumn.scrollHeight;
        },

        addNoteItem(text = '', id = Date.now()) {
            if (!notesColumn) return;

            const block = document.createElement('div');
            block.className = 'note-block';
            block.dataset.id = id;
            block.innerHTML = `
        <div class="note-editable" contenteditable="true" placeholder="Type here...">${text}</div>
        <div class="note-actions">
          <button class="btn-text-only btn-delete">Delete</button>
        </div>
      `;

            // Handle events
            block.querySelector('.btn-delete').onclick = () => {
                block.remove();
                this.saveToStorage();
            };

            block.querySelector('.note-editable').onblur = () => this.saveToStorage();

            notesColumn.appendChild(block);
            notesColumn.scrollTop = notesColumn.scrollHeight;

            if (text === '') block.querySelector('.note-editable').focus();
        },

        saveToStorage() {
            const allNotes = Array.from(document.querySelectorAll('.note-editable'))
                .map(el => el.innerText.trim())
                .filter(t => t !== '');
            localStorage.setItem('transcribe_ai_notes', JSON.stringify(allNotes));
            console.log('TranscribeAi: Notes saved locally');
        },

        loadFromStorage() {
            const saved = localStorage.getItem('transcribe_ai_notes');
            if (saved) {
                const parsed = JSON.parse(saved);
                parsed.forEach(t => this.addNoteItem(t));
            }
        },

        exportNotes() {
            const allNotes = Array.from(document.querySelectorAll('.note-editable'))
                .map(el => el.innerText.trim())
                .filter(t => t !== '');

            const content = allNotes.join('\n\n---\n\n');
            const blob = new Blob([content], { type: 'text/markdown' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `Meeting_Notes_${new Date().toISOString().split('T')[0]}.md`;
            a.click();
            URL.revokeObjectURL(url);
        }
    };

    function init() {
        if (sidebar) return;
        sidebar = SidebarUI.create();
        document.body.appendChild(sidebar);

        transcriptColumn = document.getElementById('transcript-col');
        notesColumn = document.getElementById('notes-col');

        // Button Events
        document.getElementById('close-sidebar').onclick = hideSidebar;
        document.getElementById('add-manual-note').onclick = () => SidebarUI.addNoteItem();
        document.getElementById('save-notes').onclick = () => SidebarUI.saveToStorage();
        document.getElementById('download-notes').onclick = () => SidebarUI.exportNotes();

        const recordBtn = document.getElementById('toggle-record');
        recordBtn.onclick = () => {
            isRecording = !isRecording;
            updateStatusUI(isRecording);
            chrome.runtime.sendMessage({ action: isRecording ? 'START_RECORDING' : 'STOP_RECORDING' });
        };

        SidebarUI.loadFromStorage();
        showSidebar();
    }

    function updateStatusUI(recording) {
        const dot = document.getElementById('status-dot');
        const text = document.getElementById('status-text');
        const btn = document.getElementById('toggle-record');

        if (recording) {
            dot.classList.add('recording');
            text.innerText = 'Recording';
            btn.innerText = 'Stop Recording';
            btn.classList.add('danger');
        } else {
            dot.classList.remove('recording');
            text.innerText = 'Idle';
            btn.innerText = 'Start Recording';
            btn.classList.remove('danger');
        }
    }

    function showSidebar() {
        if (!sidebar) return;
        sidebar.style.display = 'flex';
        document.documentElement.style.paddingRight = '600px';
        document.documentElement.style.transition = 'padding-right 0.3s ease';
    }

    function hideSidebar() {
        if (!sidebar) return;
        sidebar.style.display = 'none';
        document.documentElement.style.paddingRight = '0';
    }

    // Listen for messages
    chrome.runtime.onMessage.addListener((request) => {
        if (request.action === 'NEW_TRANSCRIPTION') {
            if (request.type === 'SMART_NOTE') {
                SidebarUI.addNoteItem(`**[AI] Smart Update:**\n${request.text}`);
            } else {
                SidebarUI.addTranscriptItem(request.text || "...");
            }
        } else if (request.action === 'TOGGLE_SIDEBAR') {
            if (!sidebar) init();
            else if (sidebar.style.display === 'none') showSidebar();
            else hideSidebar();
        }
    });

    // Injection logic
    if (document.body) init();
    else window.addEventListener('load', init);
})();
