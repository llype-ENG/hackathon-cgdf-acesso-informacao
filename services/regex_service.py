import regex as re

CPF_REGEX = re.compile(r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b')
EMAIL_REGEX = re.compile(r'\b[\w\.-]+@[\w\.-]+\.\w{2,}\b')
PHONE_REGEX = re.compile(r'\b(\+55\s?)?(\(?\d{2}\)?\s?)?(9?\d{4})[-\s]?\d{4}\b')
RG_REGEX = re.compile(r'\b\d{1,2}\.?\d{3}\.?\d{3}-?[A-Za-z0-9]\b')

def detect_regex(text: str) -> dict:
    if not text or not isinstance(text, str):
        return {
            "has_personal_data": False,
            "matches": []
        }

    matches = []

    if CPF_REGEX.search(text):
        matches.append("CPF")
    if EMAIL_REGEX.search(text):
        matches.append("EMAIL")
    if PHONE_REGEX.search(text):
        matches.append("PHONE")
    if RG_REGEX.search(text):
        matches.append("RG")

    return {
        "has_personal_data": len(matches) > 0,
        "matches": matches
    }
