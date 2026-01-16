from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
import io
import os
from typing import List, Set

import PyPDF2


app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB


# Simple skill dictionaries (can be expanded easily)
GENERAL_SKILLS = {
    "python", "java", "c++", "javascript", "html", "css", "sql", "git",
    "flask", "django", "react", "node", "pandas", "numpy", "machine learning",
    "data analysis", "communication", "leadership", "project management",
    "docker", "kubernetes", "aws", "azure", "gcp", "linux", "rest",
}

JOB_ROLE_SKILLS = {
    "software_engineer": {
        "python", "java", "c++", "git", "sql", "linux", "rest", "docker",
        "kubernetes", "aws", "html", "css", "javascript",
    },
    "data_scientist": {
        "python", "pandas", "numpy", "machine learning", "data analysis",
        "sql", "communication", "presentation", "statistics",
    },
    "frontend_developer": {
        "javascript", "html", "css", "react", "git", "ui", "ux",
    },
}


def extract_text_from_pdf(file_stream: io.BufferedReader) -> str:
    """Extract raw text from a PDF file stream using PyPDF2."""
    reader = PyPDF2.PdfReader(file_stream)
    texts: List[str] = []
    for page in reader.pages:
        try:
            page_text = page.extract_text() or ""
        except Exception:
            page_text = ""
        texts.append(page_text)
    return "\n".join(texts)


def normalize_text(text: str) -> str:
    return text.lower()


def extract_skills(text: str) -> Set[str]:
    """Very simple keyword-based skill extraction.

    In a real system you might use spaCy or another NLP model. Here we
    just check for presence of known skill keywords in the text.
    """
    text_norm = normalize_text(text)
    found: Set[str] = set()
    for skill in GENERAL_SKILLS:
        if skill in text_norm:
            found.add(skill)
    return found


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        job_role = request.form.get("job_role")
        resume_file = request.files.get("resume")

        if not resume_file or resume_file.filename == "":
            return render_template(
                "index.html",
                error="Please upload a resume file.",
                job_roles=list(JOB_ROLE_SKILLS.keys()),
            )

        filename = secure_filename(resume_file.filename)
        file_ext = os.path.splitext(filename)[1].lower()

        try:
            if file_ext == ".pdf":
                # For PDFs, pass the stream directly
                text = extract_text_from_pdf(resume_file.stream)
            else:
                # Treat as plain text or generic document
                file_bytes = resume_file.read()
                try:
                    text = file_bytes.decode("utf-8", errors="ignore")
                except AttributeError:
                    # In some environments file.read() already returns str
                    text = str(file_bytes)
        except Exception as e:
            return render_template(
                "index.html",
                error=f"Could not read resume: {e}",
                job_roles=list(JOB_ROLE_SKILLS.keys()),
            )

        extracted_skills = extract_skills(text)

        required_skills = JOB_ROLE_SKILLS.get(job_role, set())
        matched_skills = sorted(list(extracted_skills & required_skills))
        missing_skills = sorted(list(required_skills - extracted_skills))
        other_skills = sorted(list(extracted_skills - required_skills))

        return render_template(
            "result.html",
            job_role=job_role,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            other_skills=other_skills,
        )

    return render_template("index.html", job_roles=list(JOB_ROLE_SKILLS.keys()))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
