const placeholderIcon = '/templates/images/file_placeholder_icon.png'
const form = document.getElementById('form')
const dropZone = document.getElementById('dropzone')
const fileInput = document.getElementById('file-input')
const uploadButton = document.getElementById('upload-button')
let fileList = [];

function preventDefaults(e) {
    e.preventDefault()
    e.stopPropagation()
}

dropZone.addEventListener('dragover', (e) => {
    preventDefaults(e)
    dropZone.classList.add('drag-over')
})

dropZone.addEventListener('dragleave', (e) => {
    preventDefaults(e)
    dropZone.classList.remove('drag-over')
})

dropZone.addEventListener('drop', (e) => {
    preventDefaults(e)
    dropZone.classList.remove('drag-over')
    handleFiles(e.dataTransfer.files);
})

dropZone.addEventListener('click', () => {
    fileInput.click();
})

fileInput.addEventListener('change', (e) => {
    handleFiles(e.target.files);
})


uploadButton.addEventListener('click', () => {
    if (fileList.length > 0) {
        tossFiles()
    }
});
uploadButton.addEventListener('keydown', (e) => {
    if (fileList.length > 0) {
        if (e.key == 'Enter' || e.key == ' ') {
            e.preventDefault()
            tossFiles()
        }
    }
});

function handleFiles(files) {
    const container = document.getElementById('preview-container');
    files = Array.from(files)
    for (const file of files) {
        fileList.push(file)
        const reader = new FileReader();
        reader.readAsDataURL(file);

        reader.onloadend = function(e) {
            const item = document.createElement('div');
            item.classList.add('preview-item');

            const icon = document.createElement('img');
            icon.classList.add('preview-image');
            if (isValidFileType(file)) {
                icon.src = e.target.result;
            } else {
                icon.src = placeholderIcon;
            }

            const name = document.createElement('span');
            name.classList.add('file-details');
            name.textContent = shortenFileName(file.name);
            name.title = file.name;

            const size = document.createElement('span');
            size.classList.add('file-details');
            const new_size = calculateSize(file.size)[0]
            const unit = calculateSize(file.size)[1]
            size.textContent = new_size + unit;
            size.title = new_size + unit;

            const del = document.createElement('button');
            del.textContent = 'x';
            del.classList.add('delete-button');
            del.addEventListener('click', () => {
                removeFile(file, item);
            })

            item.appendChild(icon);
            item.appendChild(name);
            item.appendChild(size);
            item.appendChild(del);
            container.appendChild(item);
        };
    }

    updateFileInput();
}

function shortenFileName(name, max = 20) {
    if (name.length <= max) {
        return name;
    }
    const parts = name.split('.');
    const file_ext = parts.pop();
    const base = parts.join('.');
    return base.substring(0, max - file_ext.length - 4) + '...' + file_ext;
}

function calculateSize(size) {
    let base = 0
    while (size > 1000) {
        size = size / 1000;
        base += 3;
    }

    let unit;

    switch (base) {
        case 0:
            unit = 'B';
            break;
        case 3:
            unit = 'kB';
            break;
        case 6:
            unit = 'MB';
            break;
        case 9:
            unit = 'GB';
            break;
        case 12:
            unit = 'TB';
            break;
    }

    return [size.toFixed(1), unit];
}

function isValidFileType(file) {
    const allowedTypes = ['image/jpeg', 'image/png'];
    return allowedTypes.includes(file.type);
}

function updateFileInput() {
    const dataTransfer = new DataTransfer();
    for (const file of fileList) {
        dataTransfer.items.add(file);
    }
    fileInput.files = dataTransfer.files;
    const hasFiles = fileList.length > 0;
    console.log("testing");
    uploadButton.classList.toggle('alive', hasFiles);
    uploadButton.classList.toggle('dead', !hasFiles);
}

function removeFile(file, item) {
    fileList = fileList.filter(f => f !== file);
    item.remove();
    updateFileInput();
}

// http doesnt support random uuid
function generateUUID() {
    return ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c => (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16))
}
