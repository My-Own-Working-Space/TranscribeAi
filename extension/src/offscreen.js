// offscreen.js - Handles audio capture and WebSocket streaming

let recorder;
let socket;

chrome.runtime.onMessage.addListener(async (message) => {
    if (message.target !== 'offscreen') return;

    if (message.action === 'START_RECORDING') {
        startCapture(message.streamId);
    } else if (message.action === 'STOP_RECORDING') {
        stopRecording();
    }
});

async function startCapture(streamId) {
    if (recorder && recorder.state !== 'inactive') return;

    const mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
            mandatory: {
                chromeMediaSource: 'tab',
                chromeMediaSourceId: streamId
            }
        },
        video: false
    });

    // Setup WebSocket
    socket = new WebSocket('ws://localhost:8000/ws/transcribe');
    socket.binaryType = 'arraybuffer';

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        chrome.runtime.sendMessage({
            action: 'NEW_TRANSCRIPTION_FROM_OFFSCREEN',
            text: data.text,
            type: data.type
        });
    };

    const options = { mimeType: 'audio/webm;codecs=opus' };
    recorder = MediaRecorder.isTypeSupported(options.mimeType)
        ? new MediaRecorder(mediaStream, options)
        : new MediaRecorder(mediaStream);

    recorder.ondataavailable = async (event) => {
        if (event.data.size > 0 && socket && socket.readyState === WebSocket.OPEN) {
            const buffer = await event.data.arrayBuffer();
            socket.send(buffer);
        }
    };

    socket.onopen = () => {
        console.log('TranscribeAi: WebSocket Connected, starting capture...');
        recorder.start(1000); // 1 second chunks
    };

    socket.onclose = () => {
        console.log('TranscribeAi: WebSocket Closed');
        if (recorder && recorder.state !== 'inactive') recorder.stop();
    };

    socket.onerror = (err) => {
        console.error('TranscribeAi: WebSocket Error:', err);
    };
}

function stopRecording() {
    if (recorder && recorder.state !== 'inactive') {
        recorder.stop();
        recorder.stream.getTracks().forEach(track => track.stop());
    }
    if (socket) {
        socket.close();
    }
    // Don't close window automatically to allow viewing logs if needed
    // window.close(); 
}
