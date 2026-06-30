def combine_scores(semantic_score, stylometric_score, repetition_score):
    combined = (
        semantic_score * 0.50
        + stylometric_score * 0.30
        + repetition_score * 0.20
    )
    return round(combined, 2)


def get_attribution(combined_score):
    if combined_score >= 0.70:
        return "likely_ai"
    if combined_score <= 0.30:
        return "likely_human"
    return "uncertain"


def get_confidence(combined_score, attribution):
    if attribution == "likely_ai":
        confidence = combined_score
    elif attribution == "likely_human":
        confidence = 1 - combined_score
    else:
        confidence = 1 - abs(combined_score - 0.50)
    return round(confidence, 2)
