const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
const wsHost = window.location.host
const wsUrl = `${wsProtocol}//${wsHost}/ws`

const ws = new WebSocket(wsUrl);

let userId = null
let nickName = null
let onlineUsers = []
let selectedRecipients = []
let pendingTransfers = {}
let receivingFiles = {}
let expectingBinary = null

ws.addEventListener('message', (e) => {
    if (typeof e.data === "string") {
        const message = JSON.parse(e.data)
    
        if (message.type === "connectionEstablished") {
            userId = message.userId
            nickName = message.nickname
    
            handleUserInfo(userId, nickName)
        }
    
        else if (message.type === "userList") {
            onlineUsers = message.users
            handleUserList(onlineUsers)
        }
    
        else if (message.type === "transferOffer") {
            const transferId = message.transferId
            const fromNickname = message.fromNickname
            const fileCount = Object.keys(message.files).length
            let fileNames = []
            
            Object.keys(message.files).forEach(key => {
                fileNames.push(message.files[key]['name'])
            })

            fileNames = fileNames.join(', ')

            handleTransferOffers(transferId, fromNickname, fileCount, fileNames)
            
            document.addEventListener('transferresponse', (e) => {
                const transferId = e.detail.transferId;
                const response = e.detail.response;

                if (response) {
                    ws.send(JSON.stringify({
                        type: "transfer_response",
                        transfer_id: transferId,
                        accepted: true
                    }))
                } else {
                    ws.send(JSON.stringify({
                        type: "transfer_response",
                        transfer_id: transferId,
                        accepted: false
                    }))
                }
            })
        }
    
        else if (message.type === "transferAccepted") {
            const transferId = message.transferId
            const transfer = pendingTransfers[transferId]
            
            if (!transfer) {
                console.error(`Transfer ${transferId} not found`)
                return
            }
    
            const metadata = transfer.metadata
            const files = transfer.files
    
            for (const m of metadata) {
                const file = files.find(f => f.name === m.name && f.size === m.size)

                if (file) {
                    sendBinary(transferId, m.fileId, file)
                } else {
                    console.error(`File not found for metadata: ${m.name}`)
                }
            }
    
            delete pendingTransfers[transferId]
        }
        
        else if (message.type === "transferDeclined") {
            const transferId = message.transferId
        
            handleTransferDecline(message.toNickname)
    
            delete pendingTransfers[transferId]
        }
    
        else if (message.type === "fileStart") {
            const fileId = message.fileId
            const totalChunks = message.totalChunks
            const filename = message.filename
            const size = message.size
            const filetype = message.filetype
    
            receivingFiles[fileId] = {
                chunks: [],
                totalChunks: totalChunks,
                chunksRecieved: 0,
                filename: filename,
                size: size,
                filetype: filetype
            }

            console.log(receivingFiles)
        }
    
        else if (message.type === "fileChunk") {
            const fileId = message.fileId
            const chunkIndex = message.chunkIndex

            expectingBinary = {
                fileId: fileId,
                chunkIndex: chunkIndex
            }
        }

        else if (message.type === "fileEnd") {
            fileId = message['fileId']
            const chunks = receivingFiles[fileId].chunks
            const filename = receivingFiles[fileId].filename
            const filetype = receivingFiles[fileId].filetype

            buildFile(chunks, filename, filetype)
        }
    } else {
        
        if (!expectingBinary) {
            console.error("Got binary but wasn't expecting any")
            return
        }

        const fileId = expectingBinary.fileId
        const chunkIndex = expectingBinary.chunkIndex

        receivingFiles[fileId].chunks[chunkIndex] = e.data
        receivingFiles[fileId].chunksRecieved += 1

        expectingBinary = null
    }

})


async function sendBinary(transferId, fileId, file) {
    chunkSize = 64 * 1024
    totalChunks = Math.ceil(file.size / chunkSize)

    ws.send(JSON.stringify({
        type: "file_start",
        filename: file.name,
        transfer_id: transferId,
        file_id: fileId,
        total_chunks: totalChunks,
        size: file.size,
        filetype: file.type
    }))

    // slicing files into 64kb chunks 
    for (let chunkIndex = 0; chunkIndex < totalChunks; chunkIndex++) {
        start = chunkIndex * chunkSize
        end = Math.min(start + chunkSize, file.size)

        chunk = file.slice(start, end)
        buffer = await chunk.arrayBuffer()

        ws.send(JSON.stringify({
            type: "file_chunk",
            transfer_id: transferId,
            file_id: fileId,
            chunk_index: chunkIndex
        }))
        ws.send(buffer)
    }

    ws.send(JSON.stringify({
        type: "file_end",
        transfer_id: transferId,
        file_id: fileId
    }))
}

function tossFiles() {
    if (selectedRecipients.length === 0) {
        alert("hey pal you need to select someone")
        return
    }

    const uploadedFiles = fileList.map(file => ({
        fileId: generateUUID(),
        name: file.name,
        date_uploaded: new Date(),
        size: file.size,
        type: file.type
    }))
    
    for (const recipient of selectedRecipients) {
        const transferId = generateUUID()
        
        pendingTransfers[transferId] = {
            files: fileList,
            metadata: uploadedFiles
        }
        
        ws.send(JSON.stringify({
            transfer_id: transferId,
            type: "transfer_request",
            from_user: userId,
            to_user: recipient,
            files: uploadedFiles,
            file_count: uploadedFiles.length
        }))
        console.log(`sent to ${recipient}`)
    }
}

function buildFile(chunks, filename, filetype) {
    const combinedBlob = new Blob(chunks, { type: filetype } )
    const url = URL.createObjectURL(combinedBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.append(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
}