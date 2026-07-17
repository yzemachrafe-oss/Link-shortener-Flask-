# Flask Link Shortener

A simple Flask app that shortens URLs and redirects using a persistent SQLite database.

## Run

1) Create and activate a virtual environment (recommended)

Windows (PowerShell):
```bash
python -m venv venv
venv\Scripts\activate
```

2) Install dependencies
```bash
pip install -r requirements.txt
```

3) Start the server
```bash
python app.py
```

Open:
- `http://localhost:5000/`

## API

- Shorten (JSON):
```bash
curl -X POST http://localhost:5000/api/shorten \
  -H "Content-Type: application/json" \
  -d "{\"url\":\"https://example.com\"}"
```

- Redirect:
`GET http://localhost:5000/<code>`

## Storage

Uses `link_shortener.db` (SQLite) inside the `link_shortener/` folder.

