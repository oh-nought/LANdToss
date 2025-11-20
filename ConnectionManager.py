import json

class ConnectionManager:
    def __init__(self):
        self.users = {}
        self.pending_transfers = {}
        self.active_transfers = {}

    async def connect(self, user_id, nickname, websocket):
        self.users[user_id] = {
            'websocket': websocket,
            'nickname': nickname
        }

        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "user_id": user_id,
            "nickname": nickname
        }))

        await self.broadcast_user_list()
        
        print(f'{user_id} has connected!')

    async def disconnect(self, user_id):
        if user_id in self.users:
            del self.users[user_id]
            print(f'{user_id} has disconnected!')

            await self.broadcast_user_list()
        else:
            print("user doesn't exist")
    
    def get_online_users(self):
        pass

    async def create_pending_transfer(self, transfer_id, from_user, to_user, files):
        self.pending_transfers[transfer_id] = {
            'from': from_user,
            'to': to_user,
            'files': files
        }

        sender_nickname = self.users[from_user]['nickname']
        recipient_websocket = self.users[to_user]['websocket']

        message = json.dumps({
            "type": "transfer_offer",
            "transfer_id": transfer_id,
            "from_nickname": sender_nickname,
            "files": files
        })

        await recipient_websocket.send_text(message)

    async def accept_transfer(self, transfer_id):
        if not self.pending_transfers.get(transfer_id):
            raise ValueError
        else:
            transfer_data = self.pending_transfers[transfer_id]
            sender_id = transfer_data['from']
            recipient_id = transfer_data['to']
            files = transfer_data['files']


            self.active_transfers[transfer_id] = {
                'from': sender_id,
                'to': recipient_id,
                'files': files,
                'status': 'transferring',
                'chunks_recieved': 0,
                'totals_chunks': sum([file['size'] for file in files])
            }
            sender = self.active_transfers[transfer_id]['from']
            del self.pending_transfers[transfer_id]
            
            sender_websocket = self.users[sender]['websocket']

            message = json.dumps({
                "type": "transfer_accepted",
                "transfer_id": transfer_id,
                "files": files
            })

            await sender_websocket.send_text(message)


    async def decline_transfer(self, transfer_id):
        if not self.pending_transfers.get(transfer_id):
            raise ValueError
        else:
            sender = self.pending_transfers[transfer_id]['from']
            sender_websocket = self.users[sender]['websocket']
            recipient = self.pending_transfers[transfer_id]['to']
            recipient_nickname = self.users[recipient]['nickname']

            del self.pending_transfers[transfer_id]

            message = json.dumps({
                "type": "transfer_declined",
                "transfer_id": transfer_id,
                "to_nickname": recipient_nickname
            })
            
            await sender_websocket.send_text(message)

    async def initialize_file_transfer(self, transfer_id, file_id, metadata):
        pass

    async def prepare_for_chunk(self, sender_websocket, transfer_id, file_id, chunk_index):
        pass

    async def forward_chunk(self, sender_websocket, binary_data):
        pass

    async def finalize_file_transfer(self, transfer_id, file_id):
        pass

    async def broadcast_user_list(self):
        user_list = []
        for user_id, user_data in self.users.items():
            user_object = {
                "id": user_id,
                "nickname": user_data['nickname']
            }
            user_list.append(user_object)
        
        message = json.dumps({
            "type": "user_list",
            "users": user_list
        })
        
        for user_id, user_data in self.users.items():
            try:
                websocket = user_data['websocket']
                await websocket.send_text(message)
            except Exception as e:
                print(f"Failed to send to {user_id}: {e}")