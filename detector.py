import json
import os
import re

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

MODEL = "llama-3.3-70b-versatile"

TRANSITIONS = [
    "furthermore",
    "moreover",
    "however",
    "therefore",
    "consequently",
    "in addition",
    "additionally",
    "in conclusion",
    "in summary",
    "for example",
    "as a result",
    "overall",
    "thus",
    "hence",
    "notably",
    "importantly",
]


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


def split_sentences(text):
    parts = re.split(r"[.!?]+", text)
    return [p.strip() for p in parts if p.strip()]


def get_stylometric_score(text):
    words = text.split()
    if len(words) < 5:
        return 0.50

    sentences = split_sentences(text)
    if not sentences:
        return 0.50

    lengths = [len(s.split()) for s in sentences]
    average = sum(lengths) / len(lengths)
    if average == 0:
        length_consistency = 0.5
    else:
        variance = sum((length - average) ** 2 for length in lengths) / len(lengths)
        std = variance ** 0.5
        length_consistency = max(0.0, 1 - std / average)

    unique_words = set(word.lower() for word in words)
    vocabulary_diversity = len(unique_words) / len(words)

    lowered = text.lower()
    transition_hits = sum(1 for phrase in TRANSITIONS if phrase in lowered)
    transition_usage = min(transition_hits / 3.0, 1.0)

    punctuation = text.count(",") + text.count(";")
    punctuation_density = min(punctuation / len(sentences), 1.0)

    score = (
        length_consistency * 0.30
        + transition_usage * 0.35
        + punctuation_density * 0.20
        + vocabulary_diversity * 0.15
    )
    return round(min(max(score, 0.0), 1.0), 2)


def get_repetition_score(text):
    words = [word.lower() for word in text.split()]
    if len(words) < 20:
        return 0.50

    unique_words = set(words)
    repeated_words = 1 - len(unique_words) / len(words)

    sentences = split_sentences(text)
    starts = [s.split()[0].lower() for s in sentences if s.split()]
    if starts:
        repeated_starts = 1 - len(set(starts)) / len(starts)
    else:
        repeated_starts = 0.0

    pairs = [words[i] + " " + words[i + 1] for i in range(len(words) - 1)]
    repeated_pairs = 1 - len(set(pairs)) / len(pairs)

    evidence = repeated_words * 0.4 + repeated_starts * 0.3 + repeated_pairs * 0.3
    score = 0.20 + evidence
    return round(min(max(score, 0.0), 1.0), 2)
