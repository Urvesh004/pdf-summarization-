import os
import re
import pdfplumber
import requests
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


# ─────────────────────────────────────────────
#  TEXT EXTRACTORS
# ─────────────────────────────────────────────

def extract_text_from_pdf(file_path):
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        return None, f"Failed to read PDF: {str(e)}"
    if not text.strip():
        return None, "No readable text found in PDF. It may be a scanned/image-based PDF."
    return text.strip(), None


def extract_text_from_docx(file_path):
    try:
        import docx
        doc = docx.Document(file_path)
        text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        if not text.strip():
            return None, "No readable text found in DOCX file."
        return text.strip(), None
    except ImportError:
        return None, "python-docx not installed. Run: pip install python-docx"
    except Exception as e:
        return None, f"Failed to read DOCX: {str(e)}"


# ─────────────────────────────────────────────
#  PROMPT  — no emojis, clean bullets
# ─────────────────────────────────────────────

def build_prompt(text):
    body = text[1500:].strip() if len(text) > 2000 else text
    body = body[:6000]
    return f"""You are a professional document summarizer.

Read the document below and return ONLY the structured summary in EXACTLY this format — nothing before it, nothing after it:

[Document Title]

Information:-
[2-3 clear sentences describing what this document is about, who made it, and what it covers.]

About / Background:-
[1-2 sentences about the organization, institution, or context.]

Key Topics Covered:-
- [Topic 1]
- [Topic 2]
- [Topic 3]

Main Work / Project:-
[2-3 sentences describing the core project, system, or findings.]

Limitations:-
- [Limitation 1]
- [Limitation 2]

Conclusion:-
[1-2 sentences on outcome and significance.]

STRICT RULES:
- Use - (hyphen) for ALL bullet points
- Do NOT use any emoji, symbol, or special unicode character anywhere
- Do NOT use * or • or any other bullet style
- Do NOT write "Here is the summary" or any intro/outro text
- Do NOT copy raw section headers from the document like "CHAPTER 4"
- Write in clear, professional English

Document:
{body}"""


# ─────────────────────────────────────────────
#  GROQ API
# ─────────────────────────────────────────────

def call_groq(text):
    if not GROQ_API_KEY:
        return None, None

    prompt = build_prompt(text)

    models = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "llama3-70b-8192",
        "llama3-8b-8192",
        "gemma2-9b-it",
        "mixtral-8x7b-32768",
    ]

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    rate_limited_count = 0

    for model in models:
        try:
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a professional document summarizer. "
                            "Never use emojis or special unicode symbols. "
                            "Follow the output format instructions exactly."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
                "max_tokens": 800,
            }

            r = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30,
            )

            if r.status_code in (401, 403):
                return None, (
                    "Invalid Groq API Key.\n\n"
                    "Please check GROQ_API_KEY in your .env file.\n"
                    "Get a free key at: https://console.groq.com/keys"
                )

            if r.status_code == 429:
                rate_limited_count += 1
                continue

            if r.status_code == 404:
                continue

            if r.status_code != 200:
                continue

            data = r.json()
            output = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
                .strip()
            )
            if output and len(output) > 100:
                return clean_output(output), None

        except Exception:
            continue

    if rate_limited_count == len(models):
        return None, (
            "All Groq models are rate limited right now.\n\n"
            "- Wait a minute and try again (Groq resets quickly)\n"
            "- Get a new free key at: https://console.groq.com/keys"
        )

    return None, None


# ─────────────────────────────────────────────
#  EMOJI + OUTPUT CLEANER
# ─────────────────────────────────────────────

def remove_emojis(text):
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002700-\U000027BF"
        "\U0001F900-\U0001F9FF"
        "\U00002600-\U000026FF"
        "\U00002300-\U000023FF"
        "\U0000FE00-\U0000FE0F"
        "\U0001FA00-\U0001FA6F"
        "\U0001FA70-\U0001FAFF"
        "]+",
        flags=re.UNICODE,
    )
    return emoji_pattern.sub("", text)


def clean_output(text):
    # Strip filler openers
    filler = [
        r"^here'?s?\s+(a\s+)?(concise\s+|structured\s+|professional\s+)?(summary|overview|breakdown)[^\n]*\n+",
        r"^sure[!,.]?\s*[^\n]*\n+",
        r"^of course[!,.]?\s*[^\n]*\n+",
        r"^below is[^\n]*\n+",
        r"^the following[^\n]*\n+",
        r"^based on[^\n]*\n+",
    ]
    for pattern in filler:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    # Strip all emojis / special unicode
    text = remove_emojis(text)

    # Normalise all bullet styles to "- "
    text = re.sub(r"^[\s]*[•*]\s+", "- ", text, flags=re.MULTILINE)

    # Strip raw chapter / section headers from source doc
    text = re.sub(r"(?m)^(CHAPTER\s+\d+[^\n]*)$", "", text)
    text = re.sub(r"(?m)^(\d+\.\d+\s+[A-Z\s]{5,})$", "", text)

    # Collapse excess blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# ─────────────────────────────────────────────
#  MAIN ENTRY
# ─────────────────────────────────────────────

def summarize_text(file_path):
    if file_path.endswith(".docx"):
        text, error = extract_text_from_docx(file_path)
    else:
        text, error = extract_text_from_pdf(file_path)

    if error:
        return {"title": "Extraction Error", "overview": f"Error: {error}", "points": [], "details": []}

    result, groq_err = call_groq(text)
    if result:
        return {"title": "Summary", "overview": result, "points": [], "details": []}

    if groq_err:
        return {"title": "API Error", "overview": groq_err, "points": [], "details": []}

    return {
        "title": "No API Key Found",
        "overview": (
            "No API key configured.\n\n"
            "Add this to your .env file:\n\n"
            "- GROQ_API_KEY=your_key\n"
            "- Get a free key at: https://console.groq.com/keys"
        ),
        "points": [],
        "details": [],
    }
