import pdfplumber
import docx

def extract_text(filepath):
    if filepath.endswith(".pdf"):
        text = ""
        try:
            with pdfplumber.open(filepath) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
        except:
            text = ""
        return text

    elif filepath.endswith(".docx"):
        doc = docx.Document(filepath)
        return "\n".join([para.text for para in doc.paragraphs])

    return ""