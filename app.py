from flask import Flask, render_template, request, jsonify, session
from google import genai
from dotenv import load_dotenv
import os
import uuid
import requests

from database.db import get_db_connection, create_tables

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure session
app.secret_key = os.getenv("FLASK_SECRET_KEY", "jenny-development-key")

# Create database tables
create_tables()

# Initialize Gemini
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/new-chat", methods=["POST"])
def new_chat():
    session.pop("conversation_id", None)
    return jsonify({"message": "New chat started"})


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()

    user_message = data.get("message", "").strip()
    history = data.get("history", [])

    if not user_message:
        return jsonify({"error": "Message cannot be empty"}), 400

    if not client:
        return jsonify({"error": "Gemini API key is missing"}), 500

    try:
        contents = []

        # Add previous conversation
        for item in history:
            if item.get("role") in ["user", "model"]:
                contents.append({
                    "role": item["role"],
                    "parts": [{"text": item["text"]}]
                })

        # Add current message
        contents.append({
            "role": "user",
            "parts": [{"text": user_message}]
        })

        # Generate AI response
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=contents,
            config={
                "system_instruction": """
                You are Jenny, a friendly and intelligent AI assistant.

                RESPONSE STYLE:
                - Talk naturally, like a real conversation.
                - Avoid dumping large blocks of text.
                - Use short, readable paragraphs.
                - Explain concepts step by step when needed.
                - Use headings and bullet points to organize longer answers.
                - Give code examples in properly formatted code blocks.
                - For simple questions, give short and direct answers.
                - For technical questions, explain clearly with practical examples.
                - Avoid unnecessary introductions and repetitive conclusions.
                - Be friendly, helpful and easy to understand.
                """
            }
        )

        ai_reply = response.text

        # Get or create conversation ID
        if "conversation_id" not in session:
            session["conversation_id"] = str(uuid.uuid4())

        conversation_id = session["conversation_id"]

        # Save conversation to SQLite
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """INSERT INTO chats
            (conversation_id, user_message, ai_response)
            VALUES (?, ?, ?)""",
            (conversation_id, user_message, ai_reply)
        )

        connection.commit()
        connection.close()

        return jsonify({"reply": ai_reply})

    except Exception as e:
        print("Gemini Error:", e)

        return jsonify({
            "error": "Jenny is unable to respond right now."
        }), 500


@app.route("/chat-history", methods=["GET"])
def chat_history():
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT * FROM chats
        ORDER BY created_at DESC
    """)

    chats = [dict(row) for row in cursor.fetchall()]

    connection.close()

    return jsonify(chats)


@app.route("/conversations", methods=["GET"])
def get_conversations():
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            conversation_id,
            (
                SELECT user_message
                FROM chats AS c2
                WHERE c2.conversation_id = c1.conversation_id
                ORDER BY id ASC
                LIMIT 1
            ) AS title,
            MAX(created_at) AS last_updated,
            COUNT(*) AS message_count
        FROM chats AS c1
        GROUP BY conversation_id
        ORDER BY MAX(id) DESC
    """)

    conversations = [dict(row) for row in cursor.fetchall()]

    connection.close()

    return jsonify(conversations)


@app.route("/conversation/<conversation_id>", methods=["GET"])
def get_conversation(conversation_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT user_message, ai_response
        FROM chats
        WHERE conversation_id = ?
        ORDER BY id ASC
    """, (conversation_id,))

    messages = [dict(row) for row in cursor.fetchall()]

    connection.close()

    if messages:
        session["conversation_id"] = conversation_id

    return jsonify(messages)


# DELETE INDIVIDUAL CONVERSATION
@app.route("/conversation/<conversation_id>", methods=["DELETE"])
def delete_conversation(conversation_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM chats WHERE conversation_id = ?",
        (conversation_id,)
    )

    deleted_count = cursor.rowcount

    connection.commit()
    connection.close()

    if deleted_count == 0:
        return jsonify({
            "error": "Conversation not found"
        }), 404

    # Clear active session if the deleted conversation was open
    if session.get("conversation_id") == conversation_id:
        session.pop("conversation_id", None)

    return jsonify({
        "message": "Conversation deleted successfully"
    })
# =====================================
# IMAGE GENERATION
# =====================================

@app.route("/generate-image", methods=["POST"])
def generate_image():

    data = request.get_json()
    prompt = data.get("prompt", "").strip()

    if not prompt:
        return jsonify({"error": "Please enter an image prompt"}), 400

    account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
    api_token = os.getenv("CLOUDFLARE_API_TOKEN")

    if not account_id or not api_token:
        return jsonify({"error": "Cloudflare credentials missing"}), 500

    url = (
        f"https://api.cloudflare.com/client/v4/accounts/"
        f"{account_id}/ai/run/@cf/black-forest-labs/flux-1-schnell"
    )

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json={"prompt": prompt},
            timeout=180
        )

        if response.status_code != 200:
            return jsonify({
                "error": "Image generation failed",
                "details": response.text[:500]
            }), 502

        content_type = response.headers.get("Content-Type", "")

        if "image/" in content_type:
            image_data = response.content
        else:
            result = response.json()
            image_data = __import__("base64").b64decode(
                result["result"]["image"]
            )

        filename = f"{uuid.uuid4().hex}.jpg"

        image_path = os.path.join(
            app.root_path,
            "static",
            "images",
            "generated",
            filename
        )

        os.makedirs(os.path.dirname(image_path), exist_ok=True)

        with open(image_path, "wb") as image_file:
            image_file.write(image_data)

        image_url = f"/static/images/generated/{filename}"

        return jsonify({
            "success": True,
            "image_url": image_url,
            "prompt": prompt
        })

    except requests.RequestException:
        return jsonify({
            "error": "Could not connect to Cloudflare"
        }), 502

    except Exception:
        app.logger.exception("Image generation error")
        return jsonify({
            "error": "Something went wrong while generating the image"
        }), 500


if __name__ == "__main__":
    app.run(debug=True)
