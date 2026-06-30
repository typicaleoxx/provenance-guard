def build_analytics(entries):
    classifications = [e for e in entries if e.get("event_type") == "classification"]
    appeals = [e for e in entries if e.get("event_type") == "appeal"]

    total_classifications = len(classifications)
    likely_ai = sum(1 for e in classifications if e.get("attribution") == "likely_ai")
    likely_human = sum(1 for e in classifications if e.get("attribution") == "likely_human")
    uncertain = sum(1 for e in classifications if e.get("attribution") == "uncertain")
    appeal_count = len(appeals)

    if total_classifications == 0:
        appeal_rate = 0
        average_confidence = 0
    else:
        appeal_rate = round(appeal_count / total_classifications, 2)
        total_confidence = sum(e.get("confidence", 0) for e in classifications)
        average_confidence = round(total_confidence / total_classifications, 2)

    return {
        "total_classifications": total_classifications,
        "likely_ai": likely_ai,
        "likely_human": likely_human,
        "uncertain": uncertain,
        "appeals": appeal_count,
        "appeal_rate": appeal_rate,
        "average_confidence": average_confidence,
    }
