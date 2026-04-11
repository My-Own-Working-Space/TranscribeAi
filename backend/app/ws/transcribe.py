from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import io
from ..services.streaming_stt import StreamingSTT
from ..services.ai_intelligence import ai_brain

router = APIRouter()

@router.websocket("/transcribe")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Client connected to transcription websocket")
    
    # Each connection gets its own stateful STT processor
    stt_processor = StreamingSTT()
    
    try:
        while True:
            # Receive binary audio chunk
            data = await websocket.receive_bytes()
            
            if not data:
                continue
                
            # Process chunk with the stateful processor
            transcription = await stt_processor.process_chunk(data)
            
            if transcription:
                # Send text back to client
                await websocket.send_json({"text": transcription, "type": "TRANSCRIPTION"})
                
                # Periodically trigger AI Intelligence
                full_transcript = stt_processor.last_transcript
                if len(full_transcript) % 600 < 50: # Trigger every ~600 chars
                    smart_notes = await ai_brain.generate_smart_notes(full_transcript)
                    if smart_notes:
                        await websocket.send_json({
                            "text": smart_notes,
                            "type": "SMART_NOTE"
                        })
    
    except WebSocketDisconnect:
        print("Client disconnected from transcription websocket")
    except Exception as e:
        print(f"Error in transcription websocket: {e}")
        # Only try to close if it's still open
        try:
            await websocket.close()
        except:
            pass
