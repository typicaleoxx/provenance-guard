# Provenance Guard Planning

## Project Goal
Provenance Guard is a Flask backend for a creative writing platform. It accepts text submissions, runs a multi signal attribution pipeline, and returns an attribution result, a confidence score, and a transparency label. Every decision is logged, creators can appeal a label, and the submission endpoint is rate limited.

The system does not try to prove authorship perfectly. Detecting whether text is AI generated or human written is uncertain, so the goal is to communicate that uncertainty honestly. The confidence score and the wide uncertain range exist so that the platform avoids making strong claims it cannot back up, especially against human creators.

## Architecture

### Submission Flow
```
POST /submit
      |
      v
input validation
      |
      v
semantic signal
      |
      v
stylometric signal
      |
      v
repetition signal
      |
      v
weighted ensemble scoring
      |
      v
attribution result and confidence
      |
      v
transparency label
      |
      v
audit log
      |
      v
JSON response
```

### Appeal Flow
```
POST /appeal
      |
      v
validate content_id
      |
      v
capture creator_reasoning
      |
      v
update status to under_review
      |
      v
write appeal event to audit log
      |
      v
JSON response
```

### Analytics Flow
```
GET /analytics
      |
      v
read audit log
      |
      v
count detection patterns
      |
      v
count appeals
      |
      v
calculate appeal rate
      |
      v
calculate average confidence
      |
      v
JSON response
```

## Architecture Narrative
In the submission flow, a request is validated, then passed through three independent signals whose scores are combined into a weighted ensemble score that maps to an attribution result, a confidence value, and a transparency label, all of which are written to the audit log before the response is returned. In the appeal flow, a creator references an existing content_id, supplies their reasoning, and the system updates that decision to under_review and records a separate appeal event in the same audit log. This keeps both the original decision and the human response to it in one place that the analytics flow can later read.

## API Surface

### GET /health
Purpose: simple check that the service is running.
Request body: none.
Response fields:
- status: "ok"

### POST /submit
Purpose: accept a text submission and return an attribution decision.
Request body:
- text: the submitted writing
- creator_id: the id of the creator
Response fields:
- content_id: unique id for this submission
- creator_id: echoed creator id
- attribution: likely_ai, likely_human, or uncertain
- confidence: float from 0.0 to 1.0
- combined_score: weighted ensemble score
- label: transparency label text
- signals: object with semantic_score, stylometric_score, repetition_score
- status: classified

### POST /appeal
Purpose: let a creator contest a previous decision.
Request body:
- content_id: the id of the decision being appealed
- creator_id: the id of the creator
- creator_reasoning: why the creator believes the label is wrong
Response fields:
- content_id: echoed content id
- status: under_review
- message: confirmation that the appeal was logged

### GET /log
Purpose: return recent audit log entries for transparency and grading evidence.
Request body: none.
Response fields:
- entries: list of audit log entries

### GET /analytics
Purpose: summarize detection patterns and appeal activity.
Request body: none.
Response fields:
- total_classifications
- likely_ai_count
- likely_human_count
- uncertain_count
- appeal_count
- appeal_rate
- average_confidence

## Detection Signals

### 1. Semantic attribution signal using Groq
What it measures: it asks a hosted language model to judge how likely the text reads as machine generated based on meaning, phrasing, and coherence patterns.
Why it helps: it captures high level qualities that simple counting cannot, such as overly smooth transitions or generic content.
Output format: a score from 0.0 to 1.0 where higher means more likely AI.
What it misses: it can be fooled by lightly edited generated text, and it may be inconsistent on short samples.

### 2. Stylometric heuristic signal
What it measures: pure Python features of writing style such as average sentence length, variation in sentence length, punctuation variety, and vocabulary richness.
Why it helps: human writing tends to vary more in rhythm and word choice, so low variation can suggest generated text.
Output format: a score from 0.0 to 1.0 where higher means more likely AI.
What it misses: formal or technical human writing can look uniform and score high by mistake.

### 3. Repetition and uniformity signal
What it measures: how often words, phrases, and sentence structures repeat across the text.
Why it helps: generated text sometimes reuses phrasing and structure in a uniform way, while human drafts are messier.
Output format: a score from 0.0 to 1.0 where higher means more likely AI.
What it misses: intentional repetition in poetry or rhetorical writing can raise the score even when a human wrote it.

## Confidence Scoring
combined_score =
semantic_score * 0.50
stylometric_score * 0.30
repetition_score * 0.20

The semantic signal gets the largest weight at 0.50 because it considers meaning and overall coherence, which are the hardest qualities to fake and the most informative. The stylometric signal gets 0.30 because style variation is a useful but noisier indicator that can be skewed by genre. The repetition signal gets the smallest weight at 0.20 because repetition is the easiest pattern to trigger by accident, so it should nudge the result rather than drive it.

## Uncertainty Representation
- 0.60 to 1.00 means likely_ai
- 0.36 to 0.59 means uncertain
- 0.00 to 0.35 means likely_human

The uncertain range is intentionally wide because a false positive against a human creator is more harmful than leaving a result undecided. Wrongly labeling a real writer as AI can damage trust and reputation, so the system only commits to a strong label when the combined score is clearly high or clearly low. Anything in the middle is reported as uncertain.

The original threshold plan was adjusted after testing. The scores varied meaningfully, but the old thresholds placed both generated style and casual human examples into uncertain. The revised thresholds still keep an uncertainty band while making the labels more useful.

## Transparency Label Design

| Attribution | Label text |
| --- | --- |
| High confidence AI | "This content shows strong signs of being AI generated. The system found consistent patterns across multiple detection signals. A creator may appeal this label if they believe it is incorrect." |
| High confidence human | "This content shows strong signs of being human written. The system found natural variation across multiple detection signals, but this label is not a guarantee of authorship." |
| Uncertain | "This content could not be confidently attributed as AI generated or human written. The system found mixed signals, so this result should be treated as uncertain." |

## Appeals Workflow
Any creator who received a decision can appeal it. The creator submits the content_id of the original decision, their creator_id, and creator_reasoning that explains why they think the label is wrong. When an appeal is accepted, the system updates that decision to under_review and writes a separate appeal event to the audit log. A reviewer reading the log would see the original classification entry with its scores and label, followed by the appeal entry with the creator reasoning and the under_review status, so they have both the machine decision and the human response side by side.

## Rate Limiting Plan
- 10 submissions per minute
- 100 submissions per day

These limits fit a writing platform where a real creator submits drafts occasionally rather than hundreds of times in a row. Ten per minute leaves room for quick edits and resubmissions without blocking normal use, while one hundred per day is generous for a single creator but low enough to stop automated abuse. Together they reduce the risk of someone scripting the endpoint to scrape results or overload the semantic signal, which calls an external service.

## Audit Log Plan

### Classification log entry fields
- event_type
- content_id
- creator_id
- timestamp
- attribution
- confidence
- combined_score
- semantic_score
- stylometric_score
- repetition_score
- status

### Appeal log entry fields
- event_type
- content_id
- creator_id
- timestamp
- status
- appeal_reasoning

## Anticipated Edge Cases

### Formal human writing
Academic and professional writing is often uniform in sentence length and vocabulary. The stylometric and repetition signals may read that uniformity as machine like and push the score too high, producing a false positive against a human author.

### Poetry with repetition
Poetry often repeats words, phrases, and structures on purpose for rhythm and effect. The repetition signal is likely to spike on this kind of text, which could move a human written poem toward a likely_ai result.

### Heavily edited generated writing
When a creator generates a draft and then rewrites large parts of it, the text mixes machine and human qualities. The signals may disagree, and the combined score may land in the uncertain range even though part of the text really was generated.

## Stretch Feature Plan

### Ensemble detection with three weighted signals
The full system combines all three signals using the documented weights of 0.50 for semantic, 0.30 for stylometric, and 0.20 for repetition. Using several independent signals reduces the chance that one weak signal decides the outcome, and the weighting reflects how much each signal can be trusted.

### Analytics dashboard
A GET /analytics endpoint reads the audit log and reports total_classifications, likely_ai_count, likely_human_count, uncertain_count, appeal_count, appeal_rate, and average_confidence. This shows detection patterns over time, how often creators contest decisions, and the average confidence of the system, which together help judge whether the thresholds are set well.

### Implementation note
Ensemble detection will be implemented with three weighted signals:
1. semantic attribution score with 50 percent weight
2. stylometric score with 30 percent weight
3. repetition and uniformity score with 20 percent weight

The analytics dashboard will be implemented after the production layer.

## AI Tool Plan
This section is included because the assignment asks for it. It describes how assisted coding will be used across milestones without naming any specific tool.

### M3 submission endpoint plus first signal
Planning sections provided: Project Goal, Architecture submission flow, API Surface for /submit, and Audit Log Plan.
Code requested: the Flask skeleton, the /submit endpoint, and the first detection signal.
Verification: send sample submissions and confirm the response shape, the status code on invalid input, and that an audit entry is written.

### M4 second signal plus confidence scoring
Planning sections provided: Detection Signals, Confidence Scoring, and Uncertainty Representation.
Code requested: the second and third signals and the weighted scoring function that maps the combined score to an attribution result.
Verification: feed clearly human and clearly machine samples and check that the scores and attribution fall in the expected ranges.

### M5 production layer with labels appeals rate limiting and audit log
Planning sections provided: Transparency Label Design, Appeals Workflow, Rate Limiting Plan, and Audit Log Plan.
Code requested: transparency label selection, the /appeal endpoint, rate limiting on /submit, and complete audit logging for both event types.
Verification: trigger each label variant, file an appeal and confirm the status changes to under_review, exceed the rate limit to confirm it blocks, and read the log to confirm entries.

## Implementation Order
1. repo setup and planning
2. Flask skeleton and submit endpoint with first signal
3. second and third signals with confidence scoring
4. transparency labels appeals rate limiting and audit logging
5. stretch analytics endpoint
6. README evidence and walkthrough video
