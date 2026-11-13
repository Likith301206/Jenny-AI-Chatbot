// ========================================
// DOM ELEMENTS
// ========================================

const chatForm = document.getElementById("chatForm");
const messageInput = document.getElementById("messageInput");
const messagesContainer = document.getElementById("messagesContainer");
const sendBtn = document.getElementById("sendBtn");
const chatArea = document.querySelector(".chat-area");
const newChatBtn = document.getElementById("newChatBtn");
const chatHistory = document.getElementById("chatHistory");

const historyToggleBtn = document.getElementById("historyToggleBtn");
const sidebar = document.getElementById("sidebar");
const historyOverlay = document.getElementById("historyOverlay");

let conversationHistory = [];
let isProcessing = false;

// ========================================
// AUTO SCROLL
// ========================================

function scrollToBottom() {
    requestAnimationFrame(() => {
        chatArea.scrollTo({
            top: chatArea.scrollHeight,
            behavior: "smooth"
        });
    });
}

// ========================================
// DISPLAY MESSAGES
// ========================================

function addMessage(text, sender) {
    const messageDiv = document.createElement("div");
    messageDiv.classList.add("message", `${sender}-message`);

    const messageText = document.createElement("div");
    messageText.classList.add("message-bubble");

    if (sender === "ai") {
        messageText.innerHTML = marked.parse(text);

        messageText.querySelectorAll("pre code").forEach(block => {
            hljs.highlightElement(block);
        });

        messageText.querySelectorAll("pre").forEach(pre => {
            const wrapper = document.createElement("div");
            wrapper.classList.add("code-block-wrapper");

            pre.parentNode.insertBefore(wrapper, pre);
            wrapper.appendChild(pre);

            const copyButton = document.createElement("button");
            copyButton.classList.add("copy-code-btn");
            copyButton.textContent = "Copy";

            copyButton.addEventListener("click", async () => {
                const code = pre.querySelector("code");
                const codeText = code ? code.innerText : pre.innerText;

                try {
                    await navigator.clipboard.writeText(codeText);
                    copyButton.textContent = "Copied!";

                    setTimeout(() => {
                        copyButton.textContent = "Copy";
                    }, 2000);

                } catch (error) {
                    copyButton.textContent = "Failed";
                    console.error(error);
                }
            });

            wrapper.appendChild(copyButton);
        });

    } else {
        messageText.textContent = text;
    }

    messageDiv.appendChild(messageText);
    messagesContainer.appendChild(messageDiv);

    scrollToBottom();
}

// ========================================
// DISPLAY GENERATED IMAGE
// ========================================

function addGeneratedImage(imageUrl, prompt) {
    const messageDiv = document.createElement("div");
    messageDiv.classList.add("message", "ai-message");

    const bubble = document.createElement("div");
    bubble.classList.add("message-bubble");

    const heading = document.createElement("p");
    heading.textContent = "Here's your generated image!";

    const image = document.createElement("img");
    image.src = imageUrl;
    image.alt = prompt;
    image.loading = "lazy";

    image.style.width = "100%";
    image.style.maxWidth = "450px";
    image.style.borderRadius = "12px";
    image.style.display = "block";
    image.style.marginTop = "12px";

    const downloadLink = document.createElement("a");
    downloadLink.href = imageUrl;
    downloadLink.download = "jenny-generated-image.jpg";
    downloadLink.textContent = "Download Image";
    downloadLink.classList.add("download-image-btn");

    downloadLink.style.display = "inline-block";
    downloadLink.style.marginTop = "12px";
    downloadLink.style.padding = "10px 16px";
    downloadLink.style.background = "#1677F2";
    downloadLink.style.color = "#FFFFFF";
    downloadLink.style.borderRadius = "8px";
    downloadLink.style.textDecoration = "none";

    bubble.appendChild(heading);
    bubble.appendChild(image);
    bubble.appendChild(downloadLink);

    messageDiv.appendChild(bubble);
    messagesContainer.appendChild(messageDiv);

    scrollToBottom();
}

// ========================================
// SMART IMAGE REQUEST DETECTION
// ========================================

function isImageRequest(message) {
    const text = message.toLowerCase().trim();

    if (/^(how to|what is|explain|why|can you explain)\b/.test(text)) {
        return false;
    }

    const imagePatterns = [
        /\b(generate|create|draw|paint|make|produce)\b.*\b(image|picture|photo|illustration|artwork)\b/,
        /\b(image|picture|photo|illustration)\s+of\b/,
        /\b(generate|create|draw|paint)\b.*\bof\b/
    ];

    return imagePatterns.some(pattern => pattern.test(text));
}

// ========================================
// LOADING ANIMATION
// ========================================

function showLoading(message) {
    const loadingDiv = document.createElement("div");

    loadingDiv.classList.add(
        "message",
        "ai-message",
        "thinking-message"
    );

    loadingDiv.innerHTML = `
        <div class="message-bubble thinking-bubble">
            <div class="thinking-text">${message}</div>
            <div class="thinking-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;

    messagesContainer.appendChild(loadingDiv);
    scrollToBottom();

    return loadingDiv;
}

// ========================================
// GENERATE IMAGE WITH CLOUDFLARE
// ========================================

async function generateImage(prompt) {

    addMessage(prompt, "user");

    messageInput.value = "";

    sendBtn.disabled = true;

    const loadingDiv = showLoading(
        "Jenny is creating your image..."
    );

    try {
        const response = await fetch("/generate-image", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                prompt: prompt
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.error || "Image generation failed"
            );
        }

        if (!data.image_url) {
            throw new Error("No image was returned");
        }

        loadingDiv.remove();

        addGeneratedImage(data.image_url, prompt);

    } catch (error) {
        loadingDiv.remove();

        addMessage(
            `Sorry! I couldn't generate your image. ${error.message}`,
            "ai"
        );

        console.error("Image Generation Error:", error);

    } finally {
        sendBtn.disabled = false;
        isProcessing = false;
        messageInput.focus();
    }
}

// ========================================
// SEND MESSAGE TO GEMINI OR CLOUDFLARE
// ========================================

chatForm.addEventListener("submit", async function(event) {
    event.preventDefault();

    if (isProcessing) return;

    const message = messageInput.value.trim();

    if (!message) return;

    isProcessing = true;

    // Automatically detect image requests
    if (isImageRequest(message)) {
        await generateImage(message);
        return;
    }

    addMessage(message, "user");

    messageInput.value = "";
    sendBtn.disabled = true;

    const thinkingDiv = showLoading("Jenny is thinking...");

    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: message,
                history: conversationHistory
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Something went wrong");
        }

        thinkingDiv.remove();

        addMessage(data.reply, "ai");

        conversationHistory.push(
            {
                role: "user",
                text: message
            },
            {
                role: "model",
                text: data.reply
            }
        );

        await loadChatHistory();

    } catch (error) {
        thinkingDiv.remove();

        addMessage(
            "Sorry! Something went wrong. Please try again.",
            "ai"
        );

        console.error("Chat Error:", error);

    } finally {
        sendBtn.disabled = false;
        isProcessing = false;
        messageInput.focus();
    }
});

// ========================================
// SUGGESTION CARDS
// ========================================

document.querySelectorAll(".suggestion-card").forEach(card => {
    card.addEventListener("click", function() {
        const heading = card.querySelector("h4");

        if (heading) {
            messageInput.value = heading.textContent.trim();
            messageInput.focus();
        }
    });
});

// ========================================
// NEW CHAT
// ========================================

if (newChatBtn) {
    newChatBtn.addEventListener("click", async function() {
        try {
            const response = await fetch("/new-chat", {
                method: "POST"
            });

            if (!response.ok) {
                throw new Error("Unable to start a new chat");
            }

            conversationHistory = [];
            messagesContainer.innerHTML = "";
            messageInput.value = "";

            document.querySelectorAll(".history-item").forEach(item => {
                item.classList.remove("active");
            });

            messageInput.focus();
            scrollToBottom();

        } catch (error) {
            console.error("New Chat Error:", error);
        }
    });
}

// ========================================
// LOAD CHAT HISTORY
// ========================================

async function loadChatHistory() {
    try {
        const response = await fetch("/conversations");

        if (!response.ok) {
            throw new Error("Unable to load conversations");
        }

        const conversations = await response.json();

        chatHistory.innerHTML = "";

        conversations.forEach(conversation => {
            const historyItem = document.createElement("div");
            historyItem.classList.add("history-item");

            historyItem.dataset.conversationId =
                conversation.conversation_id;

            const icon = document.createElement("span");
            icon.textContent = "▢";

            const title = document.createElement("p");
            title.textContent = conversation.title || "New Chat";

            const deleteButton = document.createElement("button");
            deleteButton.classList.add("delete-chat-btn");
            deleteButton.textContent = "×";
            deleteButton.title = "Delete conversation";
            deleteButton.type = "button";

            deleteButton.setAttribute(
                "aria-label",
                "Delete this conversation"
            );

            historyItem.appendChild(icon);
            historyItem.appendChild(title);
            historyItem.appendChild(deleteButton);

            chatHistory.appendChild(historyItem);
        });

    } catch (error) {
        console.error("History Loading Error:", error);
    }
}

// ========================================
// OPEN OR DELETE PREVIOUS CONVERSATION
// ========================================

chatHistory.addEventListener("click", async function(event) {

    const deleteButton = event.target.closest(".delete-chat-btn");

    if (deleteButton) {
        event.stopPropagation();

        const historyItem = deleteButton.closest(".history-item");
        const conversationId = historyItem.dataset.conversationId;

        const confirmed = confirm(
            "Are you sure you want to delete this conversation? This cannot be undone."
        );

        if (!confirmed) return;

        try {
            const response = await fetch(
                `/conversation/${encodeURIComponent(conversationId)}`,
                {
                    method: "DELETE"
                }
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Unable to delete conversation");
            }

            if (historyItem.classList.contains("active")) {
                conversationHistory = [];
                messagesContainer.innerHTML = "";
                messageInput.value = "";
            }

            await loadChatHistory();

        } catch (error) {
            console.error("Delete Error:", error);
            alert("Unable to delete this conversation. Please try again.");
        }

        return;
    }

    const historyItem = event.target.closest(".history-item");

    if (!historyItem) return;

    const conversationId = historyItem.dataset.conversationId;

    if (!conversationId) return;

    try {
        const response = await fetch(
            `/conversation/${encodeURIComponent(conversationId)}`
        );

        if (!response.ok) {
            throw new Error("Unable to load conversation");
        }

        const messages = await response.json();

        messagesContainer.innerHTML = "";
        conversationHistory = [];

        messages.forEach(message => {
            addMessage(message.user_message, "user");
            addMessage(message.ai_response, "ai");

            conversationHistory.push(
                {
                    role: "user",
                    text: message.user_message
                },
                {
                    role: "model",
                    text: message.ai_response
                }
            );
        });

        document.querySelectorAll(".history-item").forEach(item => {
            item.classList.remove("active");
        });

        historyItem.classList.add("active");

        scrollToBottom();

    } catch (error) {
        console.error("Conversation Loading Error:", error);
    }
});

// ========================================
// MOBILE SLIDING CHAT HISTORY
// ========================================

function openHistorySidebar() {
    if (!sidebar || !historyOverlay || !historyToggleBtn) return;

    sidebar.classList.add("open");
    historyOverlay.classList.add("active");

    historyToggleBtn.setAttribute("aria-expanded", "true");
    document.body.style.overflow = "hidden";
}

function closeHistorySidebar() {
    if (!sidebar || !historyOverlay || !historyToggleBtn) return;

    sidebar.classList.remove("open");
    historyOverlay.classList.remove("active");

    historyToggleBtn.setAttribute("aria-expanded", "false");
    document.body.style.overflow = "";
}

if (historyToggleBtn) {
    historyToggleBtn.addEventListener("click", function() {
        if (sidebar.classList.contains("open")) {
            closeHistorySidebar();
        } else {
            openHistorySidebar();
        }
    });
}

if (historyOverlay) {
    historyOverlay.addEventListener("click", closeHistorySidebar);
}

chatHistory.addEventListener("click", function(event) {
    if (event.target.closest(".history-item")) {
        closeHistorySidebar();
    }
});

if (newChatBtn) {
    newChatBtn.addEventListener("click", closeHistorySidebar);
}

document.addEventListener("keydown", function(event) {
    if (event.key === "Escape") {
        closeHistorySidebar();
    }
});

// ========================================
// INITIALIZE JENNY
// ========================================

loadChatHistory();

console.log("Jenny AI initialized successfully!");
console.log("Gemini chat enabled!");
console.log("Cloudflare image generation enabled!");
console.log("Conversation memory enabled!");
console.log("Auto-scroll enabled!");
console.log("Mobile sidebar enabled!");
// Clear all chats
const clearChatsBtn = document.getElementById("clearChatsBtn");

if (clearChatsBtn) {
    clearChatsBtn.addEventListener("click", async () => {
        const confirmClear = confirm(
            "Are you sure you want to delete ALL chat history? This cannot be undone."
        );

        if (!confirmClear) return;

        try {
            const response = await fetch("/clear-chats", {
                method: "DELETE"
            });

            const data = await response.json();

            if (data.success) {
                conversationHistory = [];
                messagesContainer.innerHTML = "";
                loadChatHistory();

document.getElementById("welcomeScreen").style.display = "";
                alert("All chats cleared successfully!");
            } else {
                alert("Failed to clear chats. Please try again.");
            }
        } catch (error) {
            console.error("Clear chats error:", error);
            alert("Something went wrong while clearing chats.");
        }
    });
}
// ========================================
// SETTINGS FUNCTIONALITY
// ========================================

const settingsBtn = document.getElementById("settingsBtn");
const settingsModal = document.getElementById("settingsModal");
const closeSettingsBtn = document.getElementById("closeSettingsBtn");
const themeSelect = document.getElementById("themeSelect");
const enterToSend = document.getElementById("enterToSend");

// Open settings
settingsBtn.addEventListener("click", () => {
    settingsModal.style.display = "flex";
});

// Close settings
closeSettingsBtn.addEventListener("click", () => {
    settingsModal.style.display = "none";
});

// Close when clicking outside
settingsModal.addEventListener("click", (event) => {
    if (event.target === settingsModal) {
        settingsModal.style.display = "none";
    }
});

// Close with Escape
document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
        settingsModal.style.display = "none";
    }
});

// Theme preference
const savedTheme = localStorage.getItem("jennyTheme") || "light";

themeSelect.value = savedTheme;
document.body.classList.toggle("dark-theme", savedTheme === "dark");

themeSelect.addEventListener("change", () => {
    const selectedTheme = themeSelect.value;

    document.body.classList.toggle(
        "dark-theme",
        selectedTheme === "dark"
    );

    localStorage.setItem("jennyTheme", selectedTheme);
});

// Enter to Send preference
const savedEnterPreference = localStorage.getItem("jennyEnterToSend");

if (savedEnterPreference !== null) {
    enterToSend.checked = savedEnterPreference === "true";
}

enterToSend.addEventListener("change", () => {
    localStorage.setItem("jennyEnterToSend", enterToSend.checked);
});

// Handle Enter key
messageInput.addEventListener("keydown", (event) => {
    if (
        event.key === "Enter" &&
        !event.shiftKey &&
        enterToSend.checked
    ) {
        event.preventDefault();
        chatForm.requestSubmit();
    }
});
// Logout
const logoutBtn = document.getElementById("logoutBtn");

if (logoutBtn) {
    logoutBtn.addEventListener("click", async () => {
        const confirmLogout = confirm("Are you sure you want to log out?");

        if (!confirmLogout) return;

        try {
            await fetch("/logout", {
                method: "POST"
            });

            window.location.href = "/login";

        } catch (error) {
            console.error("Logout failed:", error);
            alert("Unable to log out. Please try again.");
        }
    });
}