const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
const wsHost = window.location.host
const wsUrl = `${wsProtocol}//${wsHost}/ws`

const ws = new WebSocket(wsUrl);

let userId = null
let nickName = null
let onlineUsers = []
let selectedRecipients = []
let pendingTransfers = {}

ws.addEventListener('message', (e) => {
    const message = JSON.parse(e.data)

    if (message['type'] === "connection_established") {
        userId = message.user_id
        nickName = message.nickname

        document.getElementById('nickname').textContent = `You are ${nickName}`
        document.getElementById('user-id').textContent = userId 
    }

    else if (message['type'] === "user_list") {
        const userList = document.getElementById('user-list')
        onlineUsers = message['users']
        userList.innerHTML = ''

        for (user of onlineUsers) {
            const userItem = document.createElement('li')
            userItem.setAttribute('data-user-id', user.id)
            if (user.id === userId) {
                userItem.textContent = `${user.nickname} (You)`
            } else {
                userItem.textContent = user.nickname
                userItem.addEventListener('click', (e) => {
                    e.preventDefault()
                    userItem.classList.toggle('selected')
                    const isSelected = userItem.classList.contains('selected')
                    if (isSelected) {
                        selectedRecipients.push(userItem.dataset.userId)
                    } else {
                        const index = selectedRecipients.indexOf(userItem.dataset.userId)
                        selectedRecipients.splice(index, 1)
                    }
                    console.log(selectedRecipients)
                })
            }

            userList.appendChild(userItem)
        }
        console.log(userList)
    }

    else if (message['type'] === "transfer_offer") {
        const modal = document.createElement('div')
        const modalText = document.createElement('p')
        const buttons = document.createElement('div')
        const acceptButton = document.createElement('div')
        const declineButton = document.createElement('div')

        modal.setAttribute('id', 'transfer-request')
        modal.classList.add('modal')
        buttons.setAttribute('id', 'modal-buttons')
        acceptButton.setAttribute('id', 'accept')
        declineButton.setAttribute('id', 'decline')
        const fileNames = message['files'].map(f => f.name).join(', ')
        modalText.textContent = `${message['from_nickname']} wants to send you ${message['files'].length} file(s): ${fileNames} `
        
        modal.appendChild(modalText)
        modal.appendChild(buttons)
        buttons.appendChild(acceptButton)
        buttons.appendChild(declineButton)

        acceptButton.textContent = 'Accept'
        declineButton.textContent = 'Decline'
        document.body.appendChild(modal)

        acceptButton.addEventListener('click', () => {
            ws.send(JSON.stringify({
                type: "transfer_response",
                transfer_id: message['transfer_id'],
                accepted: true
            }))

            modal.remove()
        })

        declineButton.addEventListener('click', () => {
            ws.send(JSON.stringify({
                type: "transfer_response",
                transfer_id: message['transfer_id'],
                accepted: false
            }))

            modal.remove()
        })

    }

    else if (message['type'] === "transfer_accepted") {
        const transferId = message['transfer_id']
        const transfer = pendingTransfers[transferId]
        
        if (!transfer) {
            console.error(`Transfer ${transferId} not found`)
            return
        }

        const metadata = transfer.metadata
        const files = transfer.files

        for (file of files) {
            sendBinary(transferId, file['file_id'], file)
        }

        delete pendingTransfers[transferId]
    }
    
    else if (message['type'] === "transfer_declined") {
        const transferId = message['transfer_id']
        
        const modal = document.createElement('div')
        const modalText = document.createElement('p')
    
        modal.setAttribute('id', 'transfer-update')
        modal.classList.add('modal')
    
        transfer_id = message['transfer_id']
        modalText.textContent = `${message['to_nickname']} has declined.`

        modal.appendChild(modalText)
        document.body.appendChild(modal)

        setTimeout(() => {
            modal.remove()
        }, 5000)

        delete pendingTransfers[transferId]
    }
})


async function sendBinary(transferId, fileId, file) {
    chunkSize = 64 * 1024
    totalChunks = Math.ceil(file.size / chunkSize)

    ws.send(JSON.stringify({
        type: 'file_start',
        transfer_id: transferId,
        file_id: fileId,
        total_chunks: totalChunks,
        size: file.size
    }))

    for (let chunkIndex = 0; chunkIndex < totalChunks; chunkIndex++) {
        start = chunkIndex * chunkSize
        end = Math.min(start + chunkSize, file.size)

        chunk = file.slice(start, end)
        buffer = await chunk.arrayBuffer()

        ws.send(JSON.stringify({
            type: 'file_chunk',
            transfer_id: transferId,
            file_id: fileId,
            chunk_index: chunkIndex
        }))
        ws.send(buffer)
    }

    ws.send(JSON.stringify({
        type: 'file_end',
        transfer_id: transferId,
        file_id: fileId
    }))
}

function tossFiles() {
    if (selectedRecipients.length === 0) {
        alert('hey pal you need to select someone')
        return
    }

    const uploadedFiles = fileList.map((file, index) => ({
        file_id: generateUUID(),
        name: file.name,
        date_uploaded: new Date(),
        size: file.size,
        type: file.type
    }))
    
    for (recipient of selectedRecipients) {
        const transferId = generateUUID()
        
        pendingTransfers[message['transfer_id']] = {
            files: fileList,
            metadata: uploadedFiles
        }
        
        ws.send(JSON.stringify({
            transfer_id: transferId,
            type: "transfer_request",
            from_user: userId,
            to_user: recipient,
            files: uploadedFiles
        }))
        console.log(`sent to ${recipient}`)
    }
}

