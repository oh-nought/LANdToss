from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from ConnectionManager import ConnectionManager
from utils import generate_nickname
import socket
import uvicorn
import json
import uuid
from settings import *

app = FastAPI()
manager = ConnectionManager()

app.mount("/client", StaticFiles(directory="client"), name="client")
templates = Jinja2Templates(directory="client")

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    user_id = str(uuid.uuid4())
    nickname = generate_nickname()
    await manager.connect(user_id, nickname, websocket)

    try:
        while True:
            data = await websocket.receive()
            if 'text' in data:
                message = json.loads(data['text'])
                message_type = message['type']
            
                if message_type == 'transfer_request':
                    transfer_id = message['transfer_id']
                    from_user = message['from_user']
                    to_user = message['to_user']
                    files = message['files']
                    file_count = message['file_count']
                    
                    await manager.create_pending_transfer(
                        transfer_id=transfer_id,
                        from_user=from_user,
                        to_user=to_user,
                        files=files,
                        file_count=file_count
                    )

                if message_type == 'transfer_response':
                    transfer_id = message['transfer_id']
                    
                    if message['accepted']:
                        await manager.accept_transfer(transfer_id=transfer_id)
                    else:
                        await manager.decline_transfer(transfer_id=transfer_id)


                if message_type == 'file_start':
                    await manager.initialize_file_transfer(
                        transfer_id=message['transfer_id'],
                        file_id=message['file_id'],
                        metadata=message
                    )


                if message_type == 'file_chunk':
                    await manager.prepare_for_chunk(
                        sender_websocket=websocket,
                        transfer_id=message['transfer_id'],
                        file_id=message['file_id'],
                        chunk_index=message['chunk_index']
                    )

                if message_type == 'file_end':
                    await manager.finalize_file_transfer(
                        transfer_id=message['transfer_id'],
                        file_id=message['file_id']
                    )
            
            elif 'bytes' in data:
                await manager.forward_chunk(
                    sender_websocket=websocket,
                    binary_data=data['bytes']
                )
    except WebSocketDisconnect:
        print(f"{user_id}'s websocket disconnected")
        await manager.disconnect(user_id)
    except RuntimeError as e:
        print(f"RuntimeError occurred for {user_id}'s websocket: {e}")
        await manager.disconnect(user_id)
    except Exception as e:
        print(f"Unexpected error occured for {user_id}: {e}")
        await manager.disconnect(user_id)


if __name__ == "__main__":
    host = socket.gethostname()
    ip = socket.gethostbyname(host)
    print('LANdToss Server')
    print(f"""

    Visit: http://{ip}:{int(PORT)} to connect
          
        """)
    uvicorn.run("server:app", host=HOST, port=int(PORT))