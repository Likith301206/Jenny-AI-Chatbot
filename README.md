# Jenny – AI Chat Assistant

An AI-powered chatbot built using Python, Flask, Google Gemini API, and Cloudflare Workers AI. Jenny provides intelligent conversations, chat history, contextual memory, and AI-powered image generation in a modern, responsive interface.

## Features

- **AI Conversations:** Get intelligent responses powered by Google Gemini.
- **Conversation Memory:** Maintains context throughout an ongoing conversation.
- **Chat History:** Automatically saves conversations using SQLite.
- **New Chat:** Start fresh conversations independently.
- **Delete Conversations:** Remove individual conversations from history.
- **AI Image Generation:** Generate images from text prompts using Cloudflare FLUX.1 Schnell.
- **Image Download:** Download generated images directly from the chat.
- **Markdown Support:** Displays formatted text and code snippets.
- **Code Highlighting:** Syntax highlighting for programming code.
- **Responsive Interface:** Chat interface designed for desktop and mobile devices.
- **Interactive UI:** Includes loading animations and automatic scrolling.

## Tech Stack

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| Flask | Web framework |
| Google Gemini API | AI text generation |
| Cloudflare Workers AI | AI image generation |
| FLUX.1 Schnell | Image generation model |
| SQLite | Conversation storage |
| HTML5 | Frontend structure |
| CSS3 | Styling and responsive design |
| JavaScript | Frontend interactions |
| Git & GitHub | Version control |

## Project Structure

```text
Jenny-AI-Chatbot/
│
├── app.py
├── config.py
├── requirements.txt
├── .env
├── .gitignore
│
├── database/
│   └── db.py
│
├── static/
│   ├── css/
│   │   └── style.css
│   │
│   ├── js/
│   │   └── script.js
│   │
│   └── images/
│       └── generated/
│
├── templates/
│   └── index.html
│
└── README.md
```

## Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Likith301206/Jenny-AI-Chatbot.git
```

### 2. Navigate to the Project

```bash
cd Jenny-AI-Chatbot
```

### 3. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it on Windows:

```powershell
venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Create a `.env` file in the root directory.

Add your own API credentials:

```env
GEMINI_API_KEY=your_gemini_api_key
CLOUDFLARE_ACCOUNT_ID=your_cloudflare_account_id
CLOUDFLARE_API_TOKEN=your_cloudflare_api_token
FLASK_SECRET_KEY=your_secret_key
```

Never upload your `.env` file or expose API credentials publicly.

### 6. Run the Application

```bash
python app.py
```

Open your browser:

```text
http://127.0.0.1:5000/
```

## How It Works

1. Users enter messages through Jenny's chat interface.
2. Flask receives the messages and communicates with Google Gemini.
3. Gemini generates an intelligent response.
4. Conversations are stored in an SQLite database.
5. Image-generation requests are routed to Cloudflare Workers AI.
6. Generated images are displayed in the conversation and can be downloaded.

## AI Services

- **Google Gemini:** Powers natural-language conversations.
- **Cloudflare Workers AI:** Generates images using FLUX.1 Schnell.

## Future Enhancements

- User authentication and personalized accounts.
- Voice input and speech responses.
- Improved conversation management.
- Cloud database integration.
- Production deployment and performance optimization.

## Author

**Likith**

GitHub: [@Likith301206](https://github.com/Likith301206)

Project: [Jenny – AI Chatbot](https://github.com/Likith301206/Jenny-AI-Chatbot)

---

⭐ If you find this project interesting, consider giving the repository a star!