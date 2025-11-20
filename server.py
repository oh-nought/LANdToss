from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from ConnectionManager import ConnectionManager
import json
import uuid
import random

app = FastAPI()
manager = ConnectionManager()

app.mount("/templates", StaticFiles(directory="templates"), name="templates")
templates = Jinja2Templates(directory="templates")

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

                print("recieved message:", message)
                print("message type", message_type)
            
                if message_type == 'transfer_request':
                    transfer_id = message['transfer_id']
                    from_user = message['from_user']
                    to_user = message['to_user']
                    files = message['files']
                    
                    await manager.create_pending_transfer(
                        transfer_id=transfer_id,
                        from_user=from_user,
                        to_user=to_user,
                        files=files
                    )
                    print(f"got the request from {from_user}")

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
    
def generate_nickname():
    adjectives = ['Amused', 'Brave', 'Cloudy', 'Distinct', 'Calm', 'Clumsy', 'Dizzy', 'Eager', 'Happy', 'Funny', 'Kind', 'Lazy', 'Super', 'Wild']
    animals = ['Cat', 'Dog', 'Fish', 'Deer', 'Panda', 'Eagle', 'Fox', 'Tiger', 'Falcon', 'Lion']
    adj = random.choice(adjectives)
    animal = random.choice(animals)
    number = random.randint(10, 99)

    return f'{adj}{animal}{number}'