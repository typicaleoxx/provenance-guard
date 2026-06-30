# Provenance Guard

Provenance Guard is a backend system for text attribution analysis on creative writing platforms.

The system will accept submitted writing, run multiple attribution signals, return a confidence score, show a transparency label, support creator appeals, apply rate limiting, and store structured audit logs.

This repo is currently in the planning phase.

## Rate Limiting

The submit endpoint uses the following limits:

```text
10 submissions per minute
100 submissions per day
```

I chose these limits because a normal creator would not need to submit more than 10 writing samples in one minute. At the same time, an automated script could try to flood the submit endpoint with repeated requests. The minute limit slows down fast abuse, and the daily limit keeps normal testing and active use possible without leaving the endpoint completely open. Only the submit endpoint is limited, so checking the health route, reading the log, and filing an appeal are not blocked.

### Evidence

I tested the limit by sending 12 quick requests to POST /submit. The first 10 requests were accepted, and the last 2 were blocked with 429, which shows the submit rate limit is working:

```text
request 1: 200
request 2: 200
request 3: 200
request 4: 200
request 5: 200
request 6: 200
request 7: 200
request 8: 200
request 9: 200
request 10: 200
request 11: 429
request 12: 429
```