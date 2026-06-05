import os
import re
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, Response
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader

from chatbot import get_bot_response
from ai_helper import get_ai_response
from database import (
    init_db,
    register_user,
    login_user,
    get_user_chat_history,
    get_all_chat_history,
    delete_chat_by_id,
    clear_user_chat_history,
    clear_all_chat_history,
    get_user_profile,
    get_total_users_count,
    get_admin_stats,
    save_tool_result,
    get_user_tool_results,
    get_tool_result_by_id,
    save_uploaded_resume,
    get_user_uploaded_resumes,
    get_uploaded_resume_by_id,
    delete_uploaded_resume_by_id
)


load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "careerMate_secret_key_123")

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

init_db()


def login_required():
    return "user_id" in session


def is_admin():
    return session.get("user_email") == ADMIN_EMAIL


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_text_from_pdf(file_path):
    text = ""

    try:
        reader = PdfReader(file_path)

        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

        return text.strip()

    except Exception as e:
        return f"PDF extraction error: {str(e)}"


def extract_score_from_result(result_text):
    match = re.search(r"(\d{1,3})\s*/\s*100", result_text)

    if match:
        score = int(match.group(1))
        return min(score, 100)

    match = re.search(r"score[^0-9]*(\d{1,3})", result_text, re.IGNORECASE)

    if match:
        score = int(match.group(1))
        return min(score, 100)

    return None


@app.route("/")
def home():
    if not login_required():
        return redirect(url_for("login"))

    return redirect(url_for("dashboard"))


@app.route("/dashboard")
def dashboard():
    if not login_required():
        return redirect(url_for("login"))

    user, chat_count, tool_count, resume_count = get_user_profile(session["user_id"])
    recent_chats = get_user_chat_history(session["user_id"])[:5]
    resume_results = get_user_tool_results(session["user_id"], "resume")[:5]
    roadmap_results = get_user_tool_results(session["user_id"], "roadmap")[:5]
    interview_results = get_user_tool_results(session["user_id"], "interview")[:5]

    return render_template(
        "dashboard.html",
        user=user,
        chat_count=chat_count,
        tool_count=tool_count,
        resume_count=resume_count,
        recent_chats=recent_chats,
        resume_results=resume_results,
        roadmap_results=roadmap_results,
        interview_results=interview_results,
        is_admin=is_admin()
    )


@app.route("/chat")
def chat():
    if not login_required():
        return redirect(url_for("login"))

    return render_template(
        "index.html",
        user_name=session.get("user_name"),
        is_admin=is_admin()
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        if not name or not email or not password:
            return render_template("register.html", error="All fields are required.")

        success = register_user(name, email, password)

        if success:
            return redirect(url_for("login"))

        return render_template("register.html", error="Email already registered.")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        user = login_user(email, password)

        if user:
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]

            return redirect(url_for("dashboard"))

        return render_template("login.html", error="Invalid email or password.")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/get", methods=["POST"])
def get_response():
    try:
        if not login_required():
            return jsonify({"response": "Please login first."})

        data = request.get_json()

        if not data:
            return jsonify({"response": "No data received from frontend."})

        user_message = data.get("message", "").strip()

        if user_message == "":
            return jsonify({"response": "Please enter a message."})

        bot_response = get_bot_response(session["user_id"], user_message)

        return jsonify({"response": bot_response})

    except Exception as e:
        print("GET ROUTE ERROR:", e)
        return jsonify({"response": f"Backend error: {str(e)}"})


@app.route("/history")
def history():
    if not login_required():
        return redirect(url_for("login"))

    search_query = request.args.get("q", "").strip()
    chats = get_user_chat_history(session["user_id"], search_query)

    return render_template(
        "history.html",
        chats=chats,
        search_query=search_query,
        user_name=session.get("user_name"),
        is_admin=is_admin()
    )


@app.route("/delete-chat/<int:chat_id>", methods=["POST"])
def delete_chat(chat_id):
    if not login_required():
        return redirect(url_for("login"))

    delete_chat_by_id(chat_id, user_id=session["user_id"], is_admin=is_admin())

    if is_admin() and request.form.get("source") == "admin":
        return redirect(url_for("admin"))

    return redirect(url_for("history"))


@app.route("/clear-history", methods=["POST"])
def clear_history():
    if not login_required():
        return redirect(url_for("login"))

    clear_user_chat_history(session["user_id"])

    return redirect(url_for("history"))


@app.route("/admin")
def admin():
    if not login_required():
        return redirect(url_for("login"))

    if not is_admin():
        return render_template("access_denied.html")

    search_query = request.args.get("q", "").strip()
    chats = get_all_chat_history(search_query)
    stats = get_admin_stats()

    return render_template(
        "admin.html",
        chats=chats,
        stats=stats,
        search_query=search_query
    )


@app.route("/admin/clear-all", methods=["POST"])
def admin_clear_all():
    if not login_required():
        return redirect(url_for("login"))

    if not is_admin():
        return render_template("access_denied.html")

    clear_all_chat_history()

    return redirect(url_for("admin"))


@app.route("/profile")
def profile():
    if not login_required():
        return redirect(url_for("login"))

    user, chat_count, tool_count, resume_count = get_user_profile(session["user_id"])
    uploaded_resumes = get_user_uploaded_resumes(session["user_id"])
    tool_results = get_user_tool_results(session["user_id"])[:10]

    return render_template(
        "profile.html",
        user=user,
        chat_count=chat_count,
        tool_count=tool_count,
        resume_count=resume_count,
        uploaded_resumes=uploaded_resumes,
        tool_results=tool_results,
        is_admin=is_admin()
    )


@app.route("/resume-analyzer", methods=["GET", "POST"])
def resume_analyzer():
    if not login_required():
        return redirect(url_for("login"))

    result = None
    extracted_text = None
    error = None
    result_id = None
    history = get_user_tool_results(session["user_id"], "resume")[:8]
    uploaded_resumes = get_user_uploaded_resumes(session["user_id"])

    if request.method == "POST":
        resume_text = request.form.get("resume_text", "").strip()
        resume_file = request.files.get("resume_file")

        if resume_file and resume_file.filename != "":
            if allowed_file(resume_file.filename):
                original_filename = secure_filename(resume_file.filename)
                saved_filename = f"user_{session['user_id']}_{original_filename}"
                file_path = os.path.join(app.config["UPLOAD_FOLDER"], saved_filename)

                resume_file.save(file_path)
                save_uploaded_resume(session["user_id"], original_filename, saved_filename, file_path)

                extracted_text = extract_text_from_pdf(file_path)

                if extracted_text and not extracted_text.startswith("PDF extraction error"):
                    result = get_ai_response(extracted_text, mode="resume")
                    score = extract_score_from_result(result)
                    result_id = save_tool_result(session["user_id"], "resume", extracted_text, result, score)
                else:
                    error = "Could not extract text from PDF. Try another PDF or paste resume text."
            else:
                error = "Only PDF files are allowed."

        elif resume_text:
            extracted_text = resume_text
            result = get_ai_response(resume_text, mode="resume")
            score = extract_score_from_result(result)
            result_id = save_tool_result(session["user_id"], "resume", resume_text, result, score)

        else:
            error = "Please upload a PDF resume or paste resume text."

    return render_template(
        "resume_analyzer.html",
        result=result,
        extracted_text=extracted_text,
        error=error,
        result_id=result_id,
        history=history,
        uploaded_resumes=uploaded_resumes,
        is_admin=is_admin()
    )


@app.route("/delete-resume/<int:resume_id>", methods=["POST"])
def delete_resume(resume_id):
    if not login_required():
        return redirect(url_for("login"))

    resume = get_uploaded_resume_by_id(resume_id, session["user_id"])

    if resume:
        file_path = resume[3]

        if os.path.exists(file_path):
            os.remove(file_path)

        delete_uploaded_resume_by_id(resume_id, session["user_id"])

    return redirect(url_for("resume_analyzer"))


@app.route("/roadmap", methods=["GET", "POST"])
def roadmap():
    if not login_required():
        return redirect(url_for("login"))

    result = None
    result_id = None
    history = get_user_tool_results(session["user_id"], "roadmap")[:8]

    if request.method == "POST":
        goal = request.form.get("goal", "").strip()
        duration = request.form.get("duration", "").strip()
        current_level = request.form.get("current_level", "").strip()

        if goal and duration and current_level:
            roadmap_input = f"Goal: {goal}\nDuration: {duration}\nCurrent level: {current_level}"
            result = get_ai_response(roadmap_input, mode="roadmap")
            result_id = save_tool_result(session["user_id"], "roadmap", roadmap_input, result)

    return render_template(
        "roadmap.html",
        result=result,
        result_id=result_id,
        history=history,
        is_admin=is_admin()
    )


@app.route("/interview", methods=["GET", "POST"])
def interview():
    if not login_required():
        return redirect(url_for("login"))

    result = None
    result_id = None
    history = get_user_tool_results(session["user_id"], "interview")[:8]

    if request.method == "POST":
        role = request.form.get("role", "").strip()
        level = request.form.get("level", "").strip()

        if role and level:
            interview_input = f"Role: {role}\nLevel: {level}"
            result = get_ai_response(interview_input, mode="interview")
            result_id = save_tool_result(session["user_id"], "interview", interview_input, result)

    return render_template(
        "interview.html",
        result=result,
        result_id=result_id,
        history=history,
        is_admin=is_admin()
    )


@app.route("/download-result/<int:result_id>")
def download_result(result_id):
    if not login_required():
        return redirect(url_for("login"))

    result = get_tool_result_by_id(result_id, user_id=session["user_id"], is_admin=is_admin())

    if not result:
        return "Result not found.", 404

    filename = f"CareerMate_{result[1]}_result.txt"
    text_content = f"""
CareerMate AI Result

Type: {result[1]}
Date: {result[5]}

Input:
{result[2]}

Result:
{result[3]}
"""

    return Response(
        text_content,
        mimetype="text/plain",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )


@app.errorhandler(404)
def page_not_found(error):
    return render_template("access_denied.html"), 404


@app.errorhandler(500)
def server_error(error):
    return "Server error. Please check Flask terminal.", 500


if __name__ == "__main__":
    app.run(debug=True)