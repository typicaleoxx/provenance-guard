LABELS = {
    "likely_ai": "This content shows strong signs of being AI generated. The system found consistent patterns across multiple detection signals. A creator may appeal this label if they believe it is incorrect.",
    "likely_human": "This content shows strong signs of being human written. The system found natural variation across multiple detection signals, but this label is not a guarantee of authorship.",
    "uncertain": "This content could not be confidently attributed as AI generated or human written. The system found mixed signals, so this result should be treated as uncertain.",
}


def get_transparency_label(attribution):
    return LABELS[attribution]
