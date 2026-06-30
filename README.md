# Provenance Guard

## Overview

Provenance Guard is a Flask backend system for creative writing platforms. It accepts submitted text, runs multiple attribution signals, returns an attribution result, confidence score, and transparency label, writes structured audit logs, supports creator appeals, applies rate limiting, and includes an analytics endpoint as a stretch feature.

The goal is not to prove authorship perfectly. The goal is to give a careful signal, show uncertainty when the result is mixed, and give creators a way to appeal.

## Architecture Overview

The main flow starts with `POST /submit`. A creator sends text and a creator id. The app validates the request, creates a content id, and sends the text through three detection signals:

1. semantic attribution score
2. stylometric score
3. repetition and uniformity score

The signal scores are combined into one weighted `combined_score`. That score is mapped to an attribution result of `likely_ai`, `likely_human`, or `uncertain`. The app then creates a confidence score and transparency label. The classification is written to the audit log, and the response is returned to the client.

Appeals use `POST /appeal`. The appeal endpoint checks the original classification, changes its status to `under_review`, and writes a separate appeal event to the audit log.

The log and analytics routes read from the same audit log file. No database is used.

## Features

- `POST /submit` for text classification
- Three detection signals
- Weighted confidence scoring
- Transparency labels
- Structured audit logging
- `POST /appeal` for creator appeals
- `GET /log` for recent audit log entries
- Rate limiting on `POST /submit`
- `GET /analytics` as a stretch feature

## API Endpoints

### GET /health

Checks whether the backend is running.

### POST /submit

Accepts submitted text and a creator id. It returns a content id, attribution result, confidence score, combined score, transparency label, individual signal scores, and status.

### POST /appeal

Accepts a `content_id` and `creator_reasoning`. It marks the original classification as `under_review` and records an appeal entry.

### GET /log

Returns recent audit log entries.

### GET /analytics

Returns a summary of detection patterns, appeal rate, and average confidence.

## Detection Signals

### Semantic Attribution Score

This signal looks at the meaning and style of the submitted text and estimates whether it seems generated or human written.

I chose it because semantic patterns can catch text that sounds polished, generic, or overly uniform.

What it misses: a human can write in a formal or generic style, and generated text can be edited to sound more natural.

### Stylometric Score

This signal looks at writing style patterns such as sentence length, word variety, and structure.

I chose it because human writing often has more uneven rhythm, while generated writing can be smoother and more consistent.

What it misses: some human writers are very consistent, especially in school or professional writing.

### Repetition and Uniformity Score

This signal looks for repeated words, repeated phrasing, and uniform text patterns.

I chose it because generated text can sometimes repeat ideas or use similar sentence shapes.

What it misses: poetry, song-like writing, and intentional repetition can look suspicious even when written by a person.

## Confidence Scoring

The app combines the three signals with this formula:

```text
combined_score =
semantic_score * 0.50
+ stylometric_score * 0.30
+ repetition_score * 0.20
```

The thresholds are:

```text
0.60 to 1.00 means likely_ai
0.36 to 0.59 means uncertain
0.00 to 0.35 means likely_human
```

Uncertainty matters because text attribution is not perfect. A system like this should avoid making a strong claim when the signals are mixed.

The threshold was adjusted after testing because the first version placed too many samples in uncertain. After testing generated style text and casual human text, I changed the threshold so clearly different examples were separated better.

## Example Results

### Example 1: Generated Style Text

```text
attribution: likely_ai
combined_score: 0.61
confidence: 0.61
semantic_score: 0.80
stylometric_score: 0.56
repetition_score: 0.22
```

### Example 2: Casual Human Text

```text
attribution: likely_human
combined_score: 0.33
confidence: 0.67
semantic_score: 0.20
stylometric_score: 0.62
repetition_score: 0.23
```

These examples show that the scores can move in different directions depending on the text.

## Transparency Labels

| Result | Label |
| --- | --- |
| High confidence AI | "This content shows strong signs of being AI generated. The system found consistent patterns across multiple detection signals. A creator may appeal this label if they believe it is incorrect." |
| High confidence human | "This content shows strong signs of being human written. The system found natural variation across multiple detection signals, but this label is not a guarantee of authorship." |
| Uncertain | "This content could not be confidently attributed as AI generated or human written. The system found mixed signals, so this result should be treated as uncertain." |

## Appeals Workflow

`POST /appeal` captures `content_id` and `creator_reasoning`. The endpoint checks that the content id exists in the audit log. If it exists, the original classification status is updated to `under_review`.

The app also writes a new appeal log entry. This keeps the original classification and the creator response in the same audit history.

## Rate Limiting

The submit endpoint uses these limits:

```text
10 submissions per minute
100 submissions per day
```

I chose these limits because a normal creator would not need to submit more than 10 writing samples in one minute. At the same time, an automated script could try to flood the submit endpoint with repeated requests. The minute limit slows down fast abuse, and the daily limit keeps normal testing and active use possible without leaving the endpoint completely open.

Only the submit endpoint is limited. Checking health, reading logs, filing appeals, and viewing analytics are not blocked by this limit.

### Rate Limit Test Output

I tested the limit by sending 12 quick requests to `POST /submit`. The first 10 requests were accepted, and the last 2 were blocked with `429`.

```text
200
200
200
200
200
200
200
200
200
200
429
429
```

## Audit Log Evidence

Each classification log entry records the main request information, scores, attribution result, confidence, and status. Appeal entries record the appeal reasoning and keep a link to the original content id.

Sample classification entry:

```json
{
  "event_type": "classification",
  "content_id": "content-001",
  "creator_id": "creator-123",
  "timestamp": "2026-06-30T12:00:00+00:00",
  "attribution": "likely_ai",
  "confidence": 0.61,
  "combined_score": 0.61,
  "semantic_score": 0.8,
  "stylometric_score": 0.56,
  "repetition_score": 0.22,
  "status": "classified"
}
```

Sample human classification entry:

```json
{
  "event_type": "classification",
  "content_id": "content-002",
  "creator_id": "creator-456",
  "timestamp": "2026-06-30T12:05:00+00:00",
  "attribution": "likely_human",
  "confidence": 0.67,
  "combined_score": 0.33,
  "semantic_score": 0.2,
  "stylometric_score": 0.62,
  "repetition_score": 0.23,
  "status": "classified"
}
```

Sample appeal entry:

```json
{
  "event_type": "appeal",
  "content_id": "content-001",
  "creator_id": "creator-123",
  "timestamp": "2026-06-30T12:10:00+00:00",
  "original_attribution": "likely_ai",
  "original_confidence": 0.61,
  "original_combined_score": 0.61,
  "semantic_score": 0.8,
  "stylometric_score": 0.56,
  "repetition_score": 0.22,
  "status": "under_review",
  "appeal_reasoning": "I wrote this myself and can explain my drafting process."
}
```

## Analytics Dashboard

The analytics dashboard is a backend endpoint, not a frontend page. `GET /analytics` reads the audit log and returns a simple summary.

Example response:

```json
{
  "total_classifications": 5,
  "likely_ai": 1,
  "likely_human": 1,
  "uncertain": 3,
  "appeals": 1,
  "appeal_rate": 0.2,
  "average_confidence": 0.73
}
```

This shows detection patterns, how often creators appeal, and the average confidence score.

## Stretch Features

1. Ensemble detection with three weighted signals
2. Analytics dashboard

When signals disagree, the weighted ensemble resolves the conflict by giving the semantic signal the most influence, the stylometric signal the second most influence, and the repetition signal the least influence.

## Known Limitations

- Formal human writing can be labeled too strongly because it may look polished and consistent.
- Poetry with repetition can look suspicious even when the repetition is intentional.
- Heavily edited generated writing can be harder to detect because the rough patterns may be removed.

## Spec Reflection

The planning spec helped because it gave me a clear map before implementation. I already knew the main routes, the audit log fields, and the scoring flow before writing most of the code.

One way implementation diverged from the spec was the scoring threshold. The first threshold placed too many examples in uncertain, so I adjusted it after testing. This made the output more useful while still keeping an uncertain range for mixed results.

## AI Usage

1. I used AI assistance to help create the first version of the Flask backend structure from my planning document. I asked for routes like `GET /health`, `POST /submit`, and `GET /log`. The output was a starting route structure. I tested the route behavior with curl and revised the response fields and validation to match my API plan.

2. I used AI assistance to help draft the scoring functions for the semantic, stylometric, and repetition signals. The output was a first version of the scoring helpers. After testing, I noticed that too many examples were landing in the uncertain range, so I adjusted the attribution thresholds to better match the actual score outputs.

## How to Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file with:

```text
GROQ_API_KEY=your_key_here
```

Run the app:

```bash
python app.py
```

## Sample Requests

### GET /health

```bash
curl http://localhost:5000/health
```

### POST /submit

```bash
curl -X POST http://localhost:5000/submit \
  -H "Content-Type: application/json" \
  -d '{"creator_id":"creator-123","text":"This is a sample piece of writing to classify."}'
```

### POST /appeal

```bash
curl -X POST http://localhost:5000/appeal \
  -H "Content-Type: application/json" \
  -d '{"content_id":"content-001","creator_reasoning":"I wrote this myself and can explain my drafting process."}'
```

### GET /log

```bash
curl http://localhost:5000/log
```

### GET /analytics

```bash
curl http://localhost:5000/analytics
```

## Walkthrough Video

Video link: add link here
