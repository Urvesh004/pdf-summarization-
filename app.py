from flask import Flask, render_template, request, send_file, jsonify, session
import os
import uuid
from utils.summarizer import summarize_text

app = Flask(__name__)
app.secret_key = "pdf_summarizer_secret_key_2025"

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

LAST_SUMMARY = ""


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files.get("file")

        if not file or file.filename == "":
            return render_template("index.html", error="Please upload a file")

        if not file.filename.endswith((".pdf", ".docx")):
            return render_template("index.html", error="Only PDF and DOCX files are allowed")

        # Save with unique ID to avoid conflicts
        ext = os.path.splitext(file.filename)[1]
        unique_name = f"{uuid.uuid4().hex}{ext}"
        filepath = os.path.join(UPLOAD_FOLDER, unique_name)
        file.save(filepath)

        # Store file_id in session so /summarize can find it
        session["file_id"] = unique_name
        session["original_name"] = file.filename

        return render_template("loading.html", filename=file.filename)

    return render_template("index.html")


@app.route("/summarize", methods=["POST"])
def summarize():
    """Called by loading page via JS fetch — returns JSON summary."""
    global LAST_SUMMARY

    file_id = session.get("file_id")
    if not file_id:
        return jsonify({"error": "❌ Session expired. Please upload your file again."})

    filepath = os.path.join(UPLOAD_FOLDER, file_id)

    if not os.path.exists(filepath):
        return jsonify({"error": "❌ File not found on server. Please upload again."})

    summary = summarize_text(filepath)

    # Delete file after processing
    try:
        os.remove(filepath)
    except Exception:
        pass

    # Clear session
    session.pop("file_id", None)
    session.pop("original_name", None)

    LAST_SUMMARY = summary["overview"]
    return jsonify({"overview": summary["overview"], "title": summary["title"]})


@app.route("/download")
def download():
    with open("summary.txt", "w", encoding="utf-8") as f:
        f.write(LAST_SUMMARY)
    return send_file("summary.txt", as_attachment=True)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000,debug=True)
