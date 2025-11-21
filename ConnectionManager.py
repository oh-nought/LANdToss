import json

class ConnectionManager:
    def __init__(self):
        self.users = {}
        self.pending_transfers = {}
        self.active_transfers = {}
        self.expecting_binary = {}

    async def connect(self, user_id, nickname, websocket):
        self.users[user_id] = {
            'websocket': websocket,
            'nickname': nickname
        }

        await websocket.send_text(json.dumps({
            "type": "connectionEstablished",
            "userId": user_id,
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

    async def create_pending_transfer(self, transfer_id, from_user, to_user, files, file_count):
        files = {file['fileId']: file for file in files}
        print(files)
        
        self.pending_transfers[transfer_id] = {
            'from': from_user,
            'to': to_user,
            'files': files,
            'file_count': file_count
        }

        sender_nickname = self.users[from_user]['nickname']
        recipient_websocket = self.users[to_user]['websocket']

        message = json.dumps({
            "type": "transferOffer",
            "transferId": transfer_id,
            "fromNickname": sender_nickname,
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
            files = transfer_data['files'] # transfer_data['files'] is a list of dicts
            file_count = transfer_data['file_count']


            self.active_transfers[transfer_id] = {
                'from': sender_id,
                'to': recipient_id,
                'files': files,
                'file_count': file_count,
                'completed_files': 0
            }
            sender = self.active_transfers[transfer_id]['from']
            del self.pending_transfers[transfer_id]
            
            sender_websocket = self.users[sender]['websocket']

            message = json.dumps({
                "type": "transferAccepted",
                "transferId": transfer_id,
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
                "type": "transferDeclined",
                "transferId": transfer_id,
                "toNickname": recipient_nickname
            })
            
            await sender_websocket.send_text(message)

    async def initialize_file_transfer(self, transfer_id, file_id, metadata):
        total_chunks = metadata['total_chunks']

        self.active_transfers[transfer_id]['files'][file_id].update({
            'chunks_recieved': 0,
            'total_chunks': total_chunks
        })

        recipient = self.active_transfers[transfer_id]['to']
        recipient_websocket = self.users[recipient]['websocket']

        await recipient_websocket.send_text(json.dumps({
            'type': 'fileStart',
            'fileId': file_id,
            'filename': metadata.get('name'),
            'totalChunks': metadata['total_chunks'],
            'size': metadata['size']
        }))

    async def prepare_for_chunk(self, sender_websocket, transfer_id, file_id, chunk_index):
        self.expecting_binary[sender_websocket] = {
            'transfer_id': transfer_id,
            'file_id': file_id,
            'chunk_index': chunk_index
        }

    async def forward_chunk(self, sender_websocket, binary_data):
        transfer_id = self.expecting_binary[sender_websocket]['transfer_id']
        transfer = self.active_transfers[transfer_id]
        recipient = transfer['to']
        recipient_websocket = self.users[recipient]['websocket']

        file_id = self.expecting_binary[sender_websocket]['file_id']
        chunk_index = self.expecting_binary[sender_websocket]['chunk_index']

        await recipient_websocket.send_text(json.dumps({
            'type': 'fileChunk',
            'fileId': file_id,
            'chunkIndex': chunk_index
        }))

        await recipient_websocket.send_bytes(binary_data)

        transfer['files'][file_id]['chunks_recieved'] += 1

        # delete now rather than later; will overwrite anyway if later
        # might protect from unexpected binary since the forwarding would fail if there were no expected binary as opposed to having a stale/yet to be overwritten flag
        del self.expecting_binary[sender_websocket]

    async def finalize_file_transfer(self, transfer_id, file_id):
        transfer = self.active_transfers[transfer_id]
        recipient = transfer['to']
        recipient_websocket = self.users[recipient]['websocket']

        await recipient_websocket.send_text(json.dumps({
            'type': 'fileEnd',
            'transferId': transfer_id,
            'fileId': file_id
        }))

        completed_files = transfer['completed_files']
        total_files = transfer['file_count']
        completed_files += 1

        # log file transfer; sqlite maybe?

        # check if entire transfer is done, if so, tell recipient
        if completed_files == total_files:
            await recipient_websocket.send_text(json.dumps({
                'type': 'transferComplete',
                'transferId': transfer_id
            }))

            # maybe log radxa metrics if in use

            # clean up transfer
            del transfer

    async def broadcast_user_list(self):
        user_list = []
        for user_id, user_data in self.users.items():
            user_object = {
                "id": user_id,
                "nickname": user_data['nickname']
            }
            user_list.append(user_object)
        
        message = json.dumps({
            "type": "userList",
            "users": user_list
        })
        
        for user_id, user_data in self.users.items():
            try:
                websocket = user_data['websocket']
                await websocket.send_text(message)
            except Exception as e:
                print(f"Failed to send to {user_id}: {e}")