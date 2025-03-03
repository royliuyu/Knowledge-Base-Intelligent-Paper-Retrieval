
document.addEventListener('DOMContentLoaded', function () {
    const folderInput = document.getElementById('folderInput');
    const selectedFolderPath = document.getElementById('selectedFolderPath');
    const chatSendButton = document.getElementById('chatSendButton');
    const chatInput = document.getElementById('chatInput');
    const summaryText = document.querySelector('.summary-text');
    const uploadedFilesList = document.getElementById('uploadedFilesList');
    const filePreviewSection = document.getElementById('filePreview');

    // Attach event listener to the send button
    if (chatSendButton) {
        chatSendButton.addEventListener('click', sendMessage);
    }

    // Add keydown event listener to the chat input
    if (chatInput) {
        chatInput.addEventListener('keydown', function (event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        });
    }

    // Dragging functionality for resizing left and right sections
    const resizer = document.querySelector('.resizer');
    const fileSection = document.querySelector('.file-list-section');
    const chatSection = document.querySelector('.chat-section');
    let isResizing = false;

    resizer.addEventListener('mousedown', function () { isResizing = true; });
    document.addEventListener('mousemove', function (e) {
        if (!isResizing) return;
        const containerRect = document.querySelector('.container').getBoundingClientRect();
        const newFileSectionWidth = e.clientX - containerRect.left;
        if (newFileSectionWidth >= 0 && newFileSectionWidth <= containerRect.width) {
            fileSection.style.flexBasis = `${newFileSectionWidth}px`;
            chatSection.style.flexBasis = `calc(100% - ${newFileSectionWidth}px)`;
        }
    });
    document.addEventListener('mouseup', function () { isResizing = false; });

    // Folder selection logic
    if (folderInput) {
        folderInput.addEventListener('change', function (event) {
            const files = event.target.files;
            if (files.length > 0) {
                let relativePath = files[0].webkitRelativePath ? files[0].webkitRelativePath.split('/').slice(0, -1).join('/') : "Selected Folder";
                if (selectedFolderPath) {
                    selectedFolderPath.textContent = `Selected Folder: ${relativePath}`;
                    selectedFolderPath.style.display = 'block';
                }

                uploadedFilesList.innerHTML = '';
                Array.from(files).filter(file => file.type === 'application/pdf').forEach(file => {
                    const listItem = document.createElement('li');
                    listItem.textContent = file.name;
                    listItem.addEventListener('dblclick', () => previewFile(file));
                    uploadedFilesList.appendChild(listItem);
                });

                summaryText.textContent = `${files.length} PDF files found.`;

                // Send relative path to backend
                sendFolderPathToBackend(relativePath);
            } else {
                selectedFolderPath.textContent = '';
                summaryText.textContent = "No files found.";
                uploadedFilesList.innerHTML = '';
                filePreviewSection.innerHTML = '';
            }
        });
    }

    // Preview file function
   function previewFile(file) {
        const previewHeading = document.getElementById('previewHeading');
        const filePreviewSection = document.getElementById('filePreview');

        // 清空现有预览内容
        filePreviewSection.innerHTML = '';

        // 更新预览标题
        if (previewHeading) {
            previewHeading.textContent = file.name;
        }

        if (file.type.startsWith('image/')) {
            // 预览图片
            const img = document.createElement('img');
            img.src = URL.createObjectURL(file);
            img.alt = file.name;
            img.style.maxWidth = '100%';
            filePreviewSection.appendChild(img);
        } else if (file.type === 'application/pdf') {
            // 预览 PDF
            const iframe = document.createElement('iframe');
            iframe.src = URL.createObjectURL(file);
            iframe.style.width = '100%';
            iframe.style.height = '400px';
            filePreviewSection.appendChild(iframe);
        } else {
            // 其他文件类型
            filePreviewSection.textContent = `Unsupported file type: ${file.type}`;
        }
    }


    // Send message with timestamp
    function sendMessage() {
        const message = chatInput.value.trim();
        if (message) {
            const timestamp = new Date().toISOString();

            addMessage(message, 'user-message', timestamp); // Display user's message

            fetch('/chat_kb/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
//                    user_id: '000001',
                    question: message,
                    pdf_directory: folderInput.value || '',
                    timestamp: timestamp
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => addMessage(data.response || "No information found.", 'bot-message'))
            .catch(error => {
                console.error('Error during chat:', error);
                addMessage('Error processing request.', 'bot-message');
            });

            chatInput.value = '';
        } else {
            alert('Please enter a question.');
        }
    }

    // Add message to chat session
    function addMessage(content, className, timestamp = null) {
        const chatSessionDiv = document.getElementById('chatSession');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${className}`;

        if (className === 'bot-message') {
            messageDiv.innerHTML = renderMarkdownToHTML(content);
        } else {
            const fullTimestamp = timestamp || new Date().toLocaleString();
            messageDiv.innerHTML = `${content} <span class="timestamp">[${fullTimestamp}]</span>`;
        }

        chatSessionDiv.appendChild(messageDiv);
        chatSessionDiv.scrollTop = chatSessionDiv.scrollHeight;
    }

    // Render Markdown to HTML
    function renderMarkdownToHTML(text) {
        return typeof marked !== 'undefined'
            ? marked.parse(text)
            : text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                 .replace(/_(.*?)_/g, '<em>$1</em>');
    }

    // Send folder path to backend
    function sendFolderPathToBackend(relativePath) {
        const timestamp = new Date().toISOString();

        fetch('/resolve_path/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
//                user_id: '000001',
                relative_path: relativePath,
                timestamp: timestamp
            })
        })
        .then(response => response.json())
        .then(data => {
            console.log('Absolute Path:', data.absolute_path);
        })
        .catch(error => console.error('Error resolving path:', error));
    }
});