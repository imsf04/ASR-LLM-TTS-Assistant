// app.js - 前端主逻辑

// 全局变量
let isRecording = false;
let mediaRecorder = null;
let audioChunks = [];
let isTTSEnabled = false;

// 实时语音对话相关
let socket;
let audioContext;
let scriptProcessor;
let mediaStreamSource;
let isVoiceChatActive = false;
const audioQueue = [];
let isPlaying = false;

const SAMPLE_RATE = 16000;
const BUFFER_SIZE = 4096;

// DOM元素引用
let voiceChatBtn;
let pauseVoiceBtn;
let recordBtn;
let sendBtn;
let chatInput;

// 初始化
document.addEventListener('DOMContentLoaded', function () {    // 获取DOM元素引用
    voiceChatBtn = document.getElementById('voice-chat-btn');
    pauseVoiceBtn = document.getElementById('pause-voice-btn');
    recordBtn = document.getElementById('record-btn');
    sendBtn = document.getElementById('send-btn');
    chatInput = document.getElementById('chat-input');    // 绑定事件监听器
    if (voiceChatBtn) {
        voiceChatBtn.addEventListener('click', () => {
            if (isVoiceChatActive) {
                stopVoiceChat();
            } else {
                startVoiceChat();
            }
        });
    }

    // 绑定暂停按钮事件
    if (pauseVoiceBtn) {
        pauseVoiceBtn.addEventListener('click', () => {
            if (pauseVoiceBtn.textContent.includes('暂停')) {
                pauseVoiceChat();
            } else {
                resumeVoiceChat();
            }
        });
    }

    // 移除欢迎消息当有真实对话时
    clearWelcomeMessage();

    // 初始化MathJax
    if (window.MathJax) {
        MathJax.typesetPromise();
    }
});

// 清除欢迎消息
function clearWelcomeMessage() {
    const welcome = document.querySelector('.welcome-message');
    if (welcome && document.querySelectorAll('.message').length > 0) {
        welcome.style.display = 'none';
    }
}

// 聊天消息渲染
function renderMessage(role, content, time) {
    clearWelcomeMessage();

    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const avatar = role === 'user'
        ? '<div class="message-avatar">我</div>'
        : '<div class="message-avatar"><i class="fas fa-robot"></i></div>';

    const html = `
        ${avatar}
        <div class="message-content">
            <div class="markdown-body">${marked.parse(content)}</div>
            <div class="message-time">${time || ''}</div>
            ${role === 'assistant' ? `
                <div class="message-actions mt-2">
                    <button class="btn btn-sm btn-outline-secondary" onclick="speakText('${content.replace(/'/g, "\\'")}')">
                        <i class="fas fa-volume-up"></i> 朗读
                    </button>
                    <button class="btn btn-sm btn-outline-secondary" onclick="copyToClipboard('${content.replace(/'/g, "\\'")}')">
                        <i class="fas fa-copy"></i> 复制
                    </button>
                </div>
            ` : ''}
        </div>
    `;

    messageDiv.innerHTML = html;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    // 重新渲染数学公式
    if (window.MathJax) {
        MathJax.typesetPromise([messageDiv]);
    }
}

// 发送消息
function sendMessage() {
    const input = document.getElementById('messageInput');
    const text = input.value.trim();
    if (!text) return;

    renderMessage('user', text, new Date().toLocaleTimeString());
    input.value = '';
    showTyping();

    fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text })
    })
        .then(res => res.json())
        .then(data => {
            hideTyping();
            if (data.success) {
                renderMessage('assistant', data.response, new Date().toLocaleTimeString());

                // 自动TTS
                if (isTTSEnabled) {
                    speakText(data.response);
                }
            } else {
                renderMessage('assistant', data.error || '出错了', new Date().toLocaleTimeString());
            }
        })
        .catch(err => {
            hideTyping();
            console.error('Chat error:', err);
            renderMessage('assistant', '网络错误，请稍后重试', new Date().toLocaleTimeString());
        });
}

// 回车发送
function handleKeyPress(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
}

// 显示/隐藏打字中
function showTyping() {
    const chatMessages = document.getElementById('chatMessages');
    let typing = document.getElementById('typingIndicator');
    if (!typing) {
        typing = document.createElement('div');
        typing.id = 'typingIndicator';
        typing.className = 'typing-indicator';
        typing.innerHTML = `
            <div class="message-avatar"><i class="fas fa-robot"></i></div>
            <div class="message-content">
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
                <small class="text-muted">AI助手正在思考...</small>
            </div>
        `;
        chatMessages.appendChild(typing);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

function hideTyping() {
    const typing = document.getElementById('typingIndicator');
    if (typing) typing.remove();
}

// 录音功能
async function toggleRecording() {
    const recordBtn = document.getElementById('recordBtn');
    const indicator = document.getElementById('recordingIndicator');

    if (!isRecording) {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    sampleRate: 16000,
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true
                }
            });

            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];

            mediaRecorder.ondataavailable = event => {
                audioChunks.push(event.data);
            };

            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                await sendAudioForASR(audioBlob);

                // 停止所有音频轨道
                stream.getTracks().forEach(track => track.stop());
            };

            mediaRecorder.start();
            isRecording = true;
            recordBtn.textContent = '停止录音';
            recordBtn.classList.add('btn-danger');
            recordBtn.classList.remove('btn-outline-light');
            indicator.style.display = 'block';

        } catch (err) {
            console.error('录音权限被拒绝:', err);
            alert('无法访问麦克风，请检查浏览器权限设置');
        }
    } else {
        stopRecording();
    }
}

function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        isRecording = false;

        const recordBtn = document.getElementById('recordBtn');
        const indicator = document.getElementById('recordingIndicator');

        recordBtn.textContent = '开始录音';
        recordBtn.classList.remove('btn-danger');
        recordBtn.classList.add('btn-outline-light');
        indicator.style.display = 'none';
    }
}

// 发送音频进行ASR
async function sendAudioForASR(audioBlob) {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.wav');

    try {
        showTyping();
        const response = await fetch('/asr', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        hideTyping(); if (data.success) {
            // 将识别的文本填入输入框
            const input = document.getElementById('messageInput');
            input.value = data.transcription;  // 修复：使用正确的字段名
            input.focus();

            // 显示识别结果
            renderMessage('user', `🎤 语音识别: ${data.transcription}`, new Date().toLocaleTimeString());

            // 可选：自动发送识别的消息（用户可以选择启用）
            // 添加一个短暂延迟，让用户看到识别结果
            setTimeout(() => {
                // 如果用户在3秒内没有修改文本，可以提示是否发送
                if (input.value === data.transcription) {
                    // 这里可以添加自动发送逻辑，或者显示发送按钮高亮
                    const sendBtn = document.querySelector('button[onclick="sendMessage()"]');
                    if (sendBtn) {
                        sendBtn.classList.add('btn-success');
                        sendBtn.classList.remove('btn-primary');
                        sendBtn.textContent = '发送识别内容';

                        // 5秒后恢复按钮状态
                        setTimeout(() => {
                            sendBtn.classList.remove('btn-success');
                            sendBtn.classList.add('btn-primary');
                            sendBtn.textContent = '发送';
                        }, 5000);
                    }
                }
            }, 1000);
        } else {
            alert(`语音识别失败: ${data.error}`);
        }
    } catch (err) {
        hideTyping();
        console.error('ASR error:', err);
        alert('语音识别服务暂时不可用');
    }
}

// TTS 功能
function toggleTTS() {
    isTTSEnabled = !isTTSEnabled;
    const ttsBtn = document.getElementById('ttsBtn');

    if (isTTSEnabled) {
        ttsBtn.textContent = '关闭语音';
        ttsBtn.classList.add('btn-success');
        ttsBtn.classList.remove('btn-outline-light');
    } else {
        ttsBtn.textContent = '开启语音';
        ttsBtn.classList.remove('btn-success');
        ttsBtn.classList.add('btn-outline-light');
    }
}

async function speakText(text) {
    try {
        const response = await fetch('/tts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: text,
                voice: 'longxiaochun_v2'
            })
        });

        const data = await response.json();

        if (data.success) {
            // 将base64音频转换为blob并播放
            const audioData = atob(data.audio);
            const arrayBuffer = new ArrayBuffer(audioData.length);
            const uint8Array = new Uint8Array(arrayBuffer);

            for (let i = 0; i < audioData.length; i++) {
                uint8Array[i] = audioData.charCodeAt(i);
            }

            const audioBlob = new Blob([arrayBuffer], { type: 'audio/mp3' });
            const audioUrl = URL.createObjectURL(audioBlob);
            const audio = new Audio(audioUrl);

            audio.play().catch(err => {
                console.error('音频播放失败:', err);
            });

            // 清理URL
            audio.onended = () => URL.revokeObjectURL(audioUrl);

        } else {
            console.error('TTS失败:', data.error);
        }
    } catch (err) {
        console.error('TTS请求失败:', err);
    }
}

// 文件上传功能
function uploadAudio() {
    document.getElementById('audioFileInput').click();
}

function attachFile() {
    document.getElementById('documentFileInput').click();
}

async function handleAudioUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('audio', file);

    try {
        showTyping();
        const response = await fetch('/asr', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        hideTyping();

        if (data.success) {
            const input = document.getElementById('messageInput');
            input.value = data.text;
            renderMessage('user', `📎 音频文件识别: ${data.text}`, new Date().toLocaleTimeString());
        } else {
            alert(`音频识别失败: ${data.error}`);
        }
    } catch (err) {
        hideTyping();
        console.error('Audio upload error:', err);
        alert('音频上传失败');
    }

    // 清空文件输入
    event.target.value = '';
}

async function handleDocumentUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/upload_document', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            alert(`文档上传成功！已处理 ${data.chunks_added} 个文本块`);
            renderMessage('assistant', `📄 文档 "${data.filename}" 已上传到知识库`, new Date().toLocaleTimeString());
        } else {
            alert(`文档上传失败: ${data.error}`);
        }
    } catch (err) {
        console.error('Document upload error:', err);
        alert('文档上传失败');
    }

    // 清空文件输入
    event.target.value = '';
}

// 知识库管理
async function uploadDocument() {
    const fileInput = document.getElementById('uploadFile');
    const file = fileInput.files[0];

    if (!file) {
        alert('请选择文件');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    const progressDiv = document.querySelector('.upload-progress');
    const progressBar = document.querySelector('.progress-bar');

    try {
        progressDiv.style.display = 'block';
        progressBar.style.width = '50%';

        const response = await fetch('/upload_document', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        progressBar.style.width = '100%';

        setTimeout(() => {
            if (data.success) {
                alert(`文档上传成功！\n文件名: ${data.filename}\n处理块数: ${data.chunks_added}`);
                bootstrap.Modal.getInstance(document.getElementById('uploadModal')).hide();
                fileInput.value = '';
            } else {
                alert(`上传失败: ${data.error}`);
            }
            progressDiv.style.display = 'none';
            progressBar.style.width = '0%';
        }, 500);

    } catch (err) {
        console.error('Upload error:', err);
        alert('上传失败，请稍后重试');
        progressDiv.style.display = 'none';
        progressBar.style.width = '0%';
    }
}

async function showDocuments() {
    const modal = new bootstrap.Modal(document.getElementById('documentsModal'));
    const listDiv = document.getElementById('documentsList');

    // 显示加载状态
    listDiv.innerHTML = `
        <div class="text-center py-3">
            <div class="spinner-border" role="status">
                <span class="visually-hidden">加载中...</span>
            </div>
        </div>
    `;

    modal.show();

    try {
        const response = await fetch('/list_documents');
        const data = await response.json();

        if (data.success) {
            if (data.documents.length === 0) {
                listDiv.innerHTML = '<p class="text-muted text-center">暂无文档</p>';
            } else {
                listDiv.innerHTML = data.documents.map(doc => `
                    <div class="document-item">
                        <div class="d-flex justify-content-between align-items-start">
                            <div class="flex-grow-1">
                                <h6 class="mb-1">${doc.filename}</h6>
                                <div class="document-meta">
                                    <small>上传时间: ${new Date(doc.added_at).toLocaleString()}</small><br>
                                    <small>文件大小: ${(doc.file_size / 1024).toFixed(1)} KB</small><br>
                                    <small>文本块数: ${doc.total_chunks}</small>
                                </div>
                                <p class="text-truncate-2 mt-2 mb-0">${doc.content_preview}</p>
                            </div>
                            <button class="btn btn-sm btn-outline-danger ms-2" onclick="deleteDocument('${doc.filename}')">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                `).join('');
            }
        } else {
            listDiv.innerHTML = '<p class="text-danger">加载失败</p>';
        }
    } catch (err) {
        console.error('Load documents error:', err);
        listDiv.innerHTML = '<p class="text-danger">加载失败</p>';
    }
}

async function deleteDocument(filename) {
    if (!confirm(`确定要删除文档 "${filename}" 吗？`)) {
        return;
    }

    try {
        const response = await fetch('/delete_document', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename })
        });

        const data = await response.json();

        if (data.success) {
            alert('文档删除成功');
            showDocuments(); // 刷新列表
        } else {
            alert(`删除失败: ${data.error}`);
        }
    } catch (err) {
        console.error('Delete document error:', err);
        alert('删除失败');
    }
}

// 其他功能
function startNewChat() {
    if (confirm('确定要开始新对话吗？当前对话内容将会清空。')) {
        clearHistory();
    }
}

async function clearHistory() {
    try {
        const response = await fetch('/clear_history', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const data = await response.json();

        if (data.success) {
            // 清空聊天界面
            const chatMessages = document.getElementById('chatMessages');
            chatMessages.innerHTML = `
                <div class="welcome-message text-center py-5">
                    <i class="fas fa-robot fa-3x text-primary mb-3"></i>
                    <h5>欢迎使用ASR-LLM-TTS智能助手</h5>
                    <p class="text-muted">您可以通过文字输入、语音输入或上传文档与我对话</p>
                </div>
            `;
        }
    } catch (err) {
        console.error('Clear history error:', err);
    }
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        // 临时显示复制成功的提示
        const toast = document.createElement('div');
        toast.className = 'position-fixed top-50 start-50 translate-middle bg-success text-white px-3 py-2 rounded';
        toast.style.zIndex = '9999';
        toast.textContent = '已复制到剪贴板';
        document.body.appendChild(toast);

        setTimeout(() => {
            document.body.removeChild(toast);
        }, 2000);
    }).catch(err => {
        console.error('复制失败:', err);
    });
}

function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    sidebar.classList.toggle('show');
}

function showSettings() {
    alert('设置功能开发中...');
}

function showAbout() {
    alert('ASR-LLM-TTS 智能助手\n版本: 1.0.0\n基于阿里云DashScope API构建');
}

// 响应式处理
window.addEventListener('resize', function () {
    if (window.innerWidth > 768) {
        document.querySelector('.sidebar').classList.remove('show');
    }
});

// --- 实时语音对话函数 ---
function initSocket() {
    socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port + '/voice');

    socket.on('connect', () => {
        console.log('成功连接到Socket.IO服务器');
        showToast('实时连接已建立');
    });

    socket.on('disconnect', () => {
        console.log('与Socket.IO服务器断开连接');
        showToast('实时连接已断开', 'error');
        stopVoiceChat();
    }); socket.on('server_message', (data) => {
        console.log('来自服务器的消息:', data.message);
        showToast(data.message, 'info');
    });

    socket.on('voice_status', (data) => {
        console.log('语音状态:', data.status, data.message);

        // 根据状态更新UI
        if (data.status === 'speaking') {
            showToast('🗣️ ' + data.message, 'info');
        } else if (data.status === 'processing') {
            showToast('⚙️ ' + data.message, 'warning');
        } else if (data.status === 'idle') {
            showToast('😴 ' + data.message, 'secondary');
        }

        // 更新按钮状态
        updateVoiceChatButtonStatus(data.status);
    });

    socket.on('asr_result', (data) => {
        console.log('ASR 结果:', data.text);
        renderMessage('user', data.text, new Date().toLocaleTimeString());
    }); socket.on('tts_speech', (data) => {
        console.log('收到TTS音频');
        const audioBlob = new Blob([base64ToBytes(data.audio)], { type: 'audio/mpeg' });
        const audioUrl = URL.createObjectURL(audioBlob);
        audioQueue.push(audioUrl);
        playFromQueue();
    });

    socket.on('llm_response', (data) => {
        console.log('LLM回复:', data.text);
        renderMessage('assistant', data.text, new Date().toLocaleTimeString());
    });

    socket.on('server_error', (data) => {
        console.error('服务器错误:', data.message);
        showToast(`错误: ${data.message}`, 'error');
    });
}

// 显示提示消息
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'info'} position-fixed`;
    toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 250px;';
    toast.textContent = message;

    document.body.appendChild(toast);

    setTimeout(() => {
        if (document.body.contains(toast)) {
            document.body.removeChild(toast);
        }
    }, 3000);
}

function startVoiceChat() {
    if (!socket || !socket.connected) {
        initSocket();
    }

    navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
        isVoiceChatActive = true;
        if (voiceChatBtn) {
            voiceChatBtn.innerHTML = '<i class="fas fa-headset"></i> 停止实时对话';
            voiceChatBtn.classList.replace('btn-info', 'btn-danger');
        }
        if (pauseVoiceBtn) {
            pauseVoiceBtn.style.display = 'inline-block';
            pauseVoiceBtn.innerHTML = '<i class="fas fa-pause"></i> 暂停对话';
            pauseVoiceBtn.classList.remove('btn-success');
            pauseVoiceBtn.classList.add('btn-warning');
        }
        showToast('实时对话已开始', 'success');

        audioContext = new (window.AudioContext || window.webkitAudioContext)({
            sampleRate: SAMPLE_RATE
        });

        mediaStreamSource = audioContext.createMediaStreamSource(stream);
        scriptProcessor = audioContext.createScriptProcessor(BUFFER_SIZE, 1, 1);

        scriptProcessor.onaudioprocess = (event) => {
            if (!isVoiceChatActive) return;
            const inputData = event.inputBuffer.getChannelData(0);
            // 将float32转换为16-bit PCM
            const pcmData = float32To16BitPCM(inputData);
            socket.emit('stream', pcmData);
        };

        mediaStreamSource.connect(scriptProcessor);
        scriptProcessor.connect(audioContext.destination);

        // 实现打断逻辑：如果用户开始说话，停止当前播放
        const vadNode = audioContext.createAnalyser();
        vadNode.fftSize = 512;
        mediaStreamSource.connect(vadNode);
        const vadBuffer = new Uint8Array(vadNode.frequencyBinCount);
        let speaking = false;
        setInterval(() => {
            vadNode.getByteFrequencyData(vadBuffer);
            const sum = vadBuffer.reduce((a, b) => a + b, 0);
            if (sum > 500) { // 简单的能量检测
                if (!speaking) {
                    speaking = true;
                    console.log("用户开始说话，打断TTS");
                    stopAllAudio();
                }
            } else {
                speaking = false;
            }
        }, 100);

    })
        .catch(err => {
            console.error('无法获取麦克风:', err);
            showToast('无法获取麦克风权限', 'error');
        });
}

function stopVoiceChat() {
    if (isVoiceChatActive) {
        isVoiceChatActive = false;

        // 发送强制停止信号给服务器
        if (socket && socket.connected) {
            socket.emit('force_stop');
        }

        if (scriptProcessor) {
            scriptProcessor.disconnect();
            scriptProcessor = null;
        }
        if (mediaStreamSource) {
            mediaStreamSource.disconnect();
            mediaStreamSource.mediaStream.getTracks().forEach(track => track.stop());
            mediaStreamSource = null;
        }
        if (audioContext) {
            audioContext.close();
            audioContext = null;
        } if (voiceChatBtn) {
            voiceChatBtn.innerHTML = '<i class="fas fa-headset"></i> 开始实时对话';
            voiceChatBtn.classList.replace('btn-danger', 'btn-info');
            voiceChatBtn.disabled = false;
        }
        if (pauseVoiceBtn) {
            pauseVoiceBtn.style.display = 'none';
        }
        showToast('实时对话已结束');
    }
}

// 更新语音按钮状态
function updateVoiceChatButtonStatus(status) {
    if (!voiceChatBtn) return;

    switch (status) {
        case 'speaking':
            voiceChatBtn.innerHTML = '<i class="fas fa-microphone animate__animated animate__pulse animate__infinite"></i> 正在说话...';
            voiceChatBtn.disabled = false;
            break;
        case 'processing':
            voiceChatBtn.innerHTML = '<i class="fas fa-cog fa-spin"></i> 正在处理...';
            voiceChatBtn.disabled = true;
            break;
        case 'idle':
            voiceChatBtn.innerHTML = '<i class="fas fa-headset"></i> 停止实时对话';
            voiceChatBtn.disabled = false;
            break;
        default:
            voiceChatBtn.innerHTML = '<i class="fas fa-headset"></i> 开始实时对话';
            voiceChatBtn.disabled = false;
            break;
    }
}

function playFromQueue() {
    if (isPlaying || audioQueue.length === 0) {
        return;
    }
    isPlaying = true;
    const audioUrl = audioQueue.shift();
    const audio = new Audio(audioUrl);
    audio.play();
    audio.onended = () => {
        isPlaying = false;
        URL.revokeObjectURL(audioUrl);
        playFromQueue();
    };
}

function stopAllAudio() {
    const audios = document.querySelectorAll('audio');
    audios.forEach(audio => {
        audio.pause();
        audio.currentTime = 0;
    });
    audioQueue.length = 0; // 清空队列
    isPlaying = false;
}

function float32To16BitPCM(float32Array) {
    const pcm16 = new Int16Array(float32Array.length);
    for (let i = 0; i < float32Array.length; i++) {
        let s = Math.max(-1, Math.min(1, float32Array[i]));
        pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
    }
    return pcm16.buffer;
}

function base64ToBytes(base64) {
    const binaryString = window.atob(base64);
    const len = binaryString.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
        bytes[i] = binaryString.charCodeAt(i);
    } return bytes;
}

// 暂停语音对话
function pauseVoiceChat() {
    if (socket && socket.connected) {
        socket.emit('pause_voice');
        if (pauseVoiceBtn) {
            pauseVoiceBtn.innerHTML = '<i class="fas fa-play"></i> 恢复对话';
            pauseVoiceBtn.classList.remove('btn-warning');
            pauseVoiceBtn.classList.add('btn-success');
        }
        showToast('语音对话已暂停', 'warning');
    }
}

// 恢复语音对话
function resumeVoiceChat() {
    if (socket && socket.connected) {
        socket.emit('resume_voice');
        if (pauseVoiceBtn) {
            pauseVoiceBtn.innerHTML = '<i class="fas fa-pause"></i> 暂停对话';
            pauseVoiceBtn.classList.remove('btn-success');
            pauseVoiceBtn.classList.add('btn-warning');
        }
        showToast('语音对话已恢复', 'success');
    }
}
