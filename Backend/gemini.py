import os
import json
import requests
from dotenv import load_dotenv
from fastapi import HTTPException, status

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)


def analyze_report(report_type: str, data: dict) -> str:
    """
    Sends already-calculated report figures to Gemini and asks for a concise
    natural-language summary. Gemini is NEVER asked to calculate numbers -
    all figures in `data` are pre-computed by reports.py.
    """
    if not GEMINI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GEMINI_API_KEY is not configured in .env",
        )

    prompt = (
        "You are a financial analyst assistant for a small furniture business. "
        "You are given ALREADY-CALCULATED accounting figures as JSON. "
        "Do NOT recalculate or second-guess any numbers. "
        "Write a short, clear, plain-language summary (max 150 words) highlighting "
        "key insights, notable trends, or risks based only on the numbers given.\n\n"
        f"Report type: {report_type}\n"
        f"Data:\n{json.dumps(data, indent=2, default=str)}"
    )

    payload = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }

    try:
        response = requests.post(
            f"{GEMINI_URL}?key={GEMINI_API_KEY}",
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        result = response.json()
        text = (
            result["candidates"][0]["content"]["parts"][0]["text"]
        )
        return text.strip()
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Gemini API request failed: {str(e)}",
        )
    except (KeyError, IndexError):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unexpected response format from Gemini API",
        )
