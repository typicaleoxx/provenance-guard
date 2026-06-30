import json
import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

MODEL = "llama-3.3-70b-versatile"


def get_semantic_score(text):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return 0.50

    prompt = (
        "Decide if the following writing is AI generated or human written. "
        "Reply with JSON only in the form {\"score\": 0.0} where score is from "
        "0.0 to 1.0 and higher means more likely AI generated.\n\n"
        + text
    )

    try:
        client = Groq(api_key=api_key)
        completion = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        content = completion.choices[0].message.content
        data = json.loads(content)
        score = float(data["score"])
        if score < 0.0:
            return 0.0
        if score > 1.0:
            return 1.0
        return score
    except Exception:
        return 0.50
