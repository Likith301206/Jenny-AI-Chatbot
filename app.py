from flask import (
    Flask, render_template, request, jsonify,
    session, redirect, url_for
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from functools import wraps

from google import genai
from dotenv import load_dotenv

import os
import uuid
import requests
import base64

from database.db import get_db_connection, create_tables


# =====================================
# CONFIGURATION
# =====================================

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    "jenny-development-key"
)

# Create database tables
create_tables()

# Initialize Gemini
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None


# =====================================
# LOGIN REQUIRED DECORATOR
# =====================================

def login_required(route_function):

    @wraps(route_function)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:
            return redirect(url_for("login"))

        return route_function(*args, **kwargs)

    return wrapper


# =====================================
# HOME
# =====================================

@app.route("/")
@login_required
def home():

    return render_template(
        "index.html",
        user_name=session.get("user_name")
    )


# =====================================
# SIGNUP
# =====================================

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if "user_id" in session:
        return redirect(url_for("home"))

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            return render_template(
                "signup.html",
                error="All fields are required."
            )

        if len(name) > 100 or len(email) > 254:
            return render_template(
                "signup.html",
                error="Name or email is too long."
            )

        if len(password) < 8:
            return render_template(
                "signup.html",
                error="Password must contain at least 8 characters."
            )

        hashed_password = generate_password_hash(password)

        connection = get_db_connection()

        try:

            connection.execute("""
                INSERT INTO users (name, email, password)
                VALUES (?, ?, ?)
            """, (name, email, hashed_password))

            connection.commit()

            user = connection.execute("""
                SELECT id, name
                FROM users
                WHERE email = ?
            """, (email,)).fetchone()

            session.clear()

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]

            return redirect(url_for("home"))

        except Exception as e:

            if "UNIQUE constraint failed" in str(e):

                error = "This email is already registered."

            else:

                app.logger.exception("Signup error")
                error = "Unable to create account."

            return render_template(
                "signup.html",
                error=error
            )

        finally:
            connection.close()

    return render_template("signup.html")


# =====================================
# LOGIN
# =====================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if "user_id" in session:
        return redirect(url_for("home"))

    if request.method == "POST":

        email = request.form.get(
            "email", ""
        ).strip().lower()

        password = request.form.get("password", "")

        connection = get_db_connection()

        user = connection.execute("""
            SELECT *
            FROM users
            WHERE email = ?
        """, (email,)).fetchone()

        connection.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            session.clear()

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]

            return redirect(url_for("home"))

        return render_template(
            "login.html",
            error="Invalid email or password."
        )

    return render_template("login.html")


# =====================================
# LOGOUT
# =====================================

@app.route("/logout", methods=["POST"])
@login_required
def logout():

    session.clear()

    return redirect(url_for("login"))


# =====================================
# NEW CHAT
# =====================================

@app.route("/new-chat", methods=["POST"])
@login_required
def new_chat():

    session.pop("conversation_id", None)

    return jsonify({
        "message": "New chat started"
    })


# =====================================
# CHAT
# =====================================

@app.route("/chat", methods=["POST"])
@login_required
def chat():

    data = request.get_json(silent=True) or {}

    user_message = data.get("message", "").strip()
    history = data.get("history", [])

    if not isinstance(user_message, str) or not user_message:
        return jsonify({
            "error": "Message cannot be empty"
        }), 400

    if not isinstance(history, list):
        return jsonify({
            "error": "Invalid conversation history"
        }), 400

    if not client:
        return jsonify({
            "error": "Gemini API key is missing"
        }), 500

    try:

        contents = []

        for item in history:

            if (
                isinstance(item, dict)
                and item.get("role") in ["user", "model"]
                and isinstance(item.get("text"), str)
            ):

                contents.append({
                    "role": item["role"],
                    "parts": [{"text": item["text"]}]
                })

        contents.append({
            "role": "user",
            "parts": [{"text": user_message}]
        })

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
                - Use headings and bullet points for longer answers.
                - Give code examples in properly formatted code blocks.
                - Give short and direct answers for simple questions.
                - Be friendly, helpful and easy to understand.
                """
            }
        )

        ai_reply = response.text

        if not ai_reply:
            raise Exception("Empty Gemini response")

        connection = get_db_connection()

        try:

            conversation_id = session.get("conversation_id")

            # Verify that the current conversation belongs to this user
            if conversation_id:

                existing = connection.execute("""
                    SELECT id
                    FROM chats
                    WHERE conversation_id = ?
                    AND user_id = ?
                    LIMIT 1
                """, (
                    conversation_id,
                    session["user_id"]
                )).fetchone()

                if not existing:
                    conversation_id = None

            if not conversation_id:

                conversation_id = str(uuid.uuid4())
                session["conversation_id"] = conversation_id

            connection.execute("""
                INSERT INTO chats (
                    conversation_id,
                    user_message,
                    ai_response,
                    user_id
                )
                VALUES (?, ?, ?, ?)
            """, (
                conversation_id,
                user_message,
                ai_reply,
                session["user_id"]
            ))

            connection.commit()

        finally:
            connection.close()

        return jsonify({
            "reply": ai_reply
        })

    except Exception:

        app.logger.exception("Gemini Error")

        return jsonify({
            "error": "Jenny is unable to respond right now."
        }), 500


# =====================================
# CHAT HISTORY
# =====================================

@app.route("/chat-history", methods=["GET"])
@login_required
def chat_history():

    connection = get_db_connection()

    chats = connection.execute("""
        SELECT *
        FROM chats
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (session["user_id"],)).fetchall()

    connection.close()

    return jsonify([
        dict(row) for row in chats
    ])


# =====================================
# CONVERSATIONS
# =====================================

@app.route("/conversations", methods=["GET"])
@login_required
def get_conversations():

    connection = get_db_connection()

    conversations = connection.execute("""
        SELECT
            conversation_id,

            (
                SELECT user_message
                FROM chats AS c2
                WHERE c2.conversation_id = c1.conversation_id
                AND c2.user_id = c1.user_id
                ORDER BY id ASC
                LIMIT 1
            ) AS title,

            MAX(created_at) AS last_updated,
            COUNT(*) AS message_count

        FROM chats AS c1

        WHERE user_id = ?

        GROUP BY conversation_id

        ORDER BY MAX(id) DESC
    """, (session["user_id"],)).fetchall()

    connection.close()

    return jsonify([
        dict(row) for row in conversations
    ])


# =====================================
# OPEN INDIVIDUAL CONVERSATION
# =====================================

@app.route("/conversation/<conversation_id>", methods=["GET"])
@login_required
def get_conversation(conversation_id):

    connection = get_db_connection()

    messages = connection.execute("""
        SELECT user_message, ai_response
        FROM chats
        WHERE conversation_id = ?
        AND user_id = ?
        ORDER BY id ASC
    """, (
        conversation_id,
        session["user_id"]
    )).fetchall()

    connection.close()

    if messages:

        session["conversation_id"] = conversation_id

    return jsonify([
        dict(row) for row in messages
    ])


# =====================================
# DELETE INDIVIDUAL CONVERSATION
# =====================================

@app.route("/conversation/<conversation_id>", methods=["DELETE"])
@login_required
def delete_conversation(conversation_id):

    connection = get_db_connection()

    cursor = connection.execute("""
        DELETE FROM chats
        WHERE conversation_id = ?
        AND user_id = ?
    """, (
        conversation_id,
        session["user_id"]
    ))

    deleted_count = cursor.rowcount

    connection.commit()
    connection.close()

    if deleted_count == 0:

        return jsonify({
            "error": "Conversation not found"
        }), 404

    if session.get("conversation_id") == conversation_id:

        session.pop("conversation_id", None)

    return jsonify({
        "message": "Conversation deleted successfully"
    })


# =====================================
# CLEAR ALL CHATS
# =====================================

@app.route("/clear-chats", methods=["DELETE"])
@login_required
def clear_chats():

    try:

        connection = get_db_connection()

        connection.execute("""
            DELETE FROM chats
            WHERE user_id = ?
        """, (session["user_id"],))

        connection.commit()
        connection.close()

        session.pop("conversation_id", None)

        return jsonify({
            "success": True,
            "message": "All chats cleared successfully."
        })

    except Exception:

        app.logger.exception("Clear chats error")

        return jsonify({
            "success": False,
            "error": "Unable to clear chats."
        }), 500


# =====================================
# IMAGE GENERATION
# =====================================

@app.route("/generate-image", methods=["POST"])
@login_required
def generate_image():

    data = request.get_json(silent=True) or {}

    prompt = data.get("prompt", "").strip()

    if not isinstance(prompt, str) or not prompt:
        return jsonify({
            "error": "Please enter an image prompt"
        }), 400

    account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
    api_token = os.getenv("CLOUDFLARE_API_TOKEN")

    if not account_id or not api_token:

        return jsonify({
            "error": "Cloudflare credentials missing"
        }), 500

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
                "error": "Image generation failed"
            }), 502

        content_type = response.headers.get("Content-Type", "")

        if "image/" in content_type:

            image_data = response.content

        else:

            result = response.json()

            image_data = base64.b64decode(
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

        os.makedirs(
            os.path.dirname(image_path),
            exist_ok=True
        )

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


# =====================================
# RUN APPLICATION
# =====================================

if __name__ == "__main__":

    app.run(debug=True)