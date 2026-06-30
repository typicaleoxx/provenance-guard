# Sample Requests

Run the app first, then use these commands in another terminal.

## GET /health

```bash
curl http://localhost:5000/health
```

## POST /submit with likely generated text

```bash
curl -X POST http://localhost:5000/submit \
  -H "Content-Type: application/json" \
  -d '{"text": "In todays fast paced world, leveraging synergistic solutions is essential. Furthermore, it is important to note that optimizing workflows enhances productivity. In conclusion, embracing innovation drives sustainable success across all domains.", "creator_id": "test-user-1"}'
```

## POST /submit with likely human text

```bash
curl -X POST http://localhost:5000/submit \
  -H "Content-Type: application/json" \
  -d '{"text": "ok so i finally tried that ramen place near the station lol. honestly kinda mid. broth was good but they forgot my egg and i was too shy to ask again. might go back tho, the guy was nice.", "creator_id": "test-user-2"}'
```

## GET /log

```bash
curl http://localhost:5000/log
```
