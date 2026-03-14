# 🏙️ City Name Generator

A fantasy/medieval/sci-fi/ancient city name generator with random picks and AI-generated names via [Featherless AI](https://featherless.ai).

## Features

- **Random mode** — 2,000+ curated names across 4 styles (Fantasy, Medieval, Sci-Fi, Ancient)
- **AI mode** — describe your city, get 2 unique names with lore explanations
- Dark teal/map UI theme

## Setup

```bash
cp .env.example .env
# Add your FEATHERLESS_API_KEY

# Docker
docker compose up -d --build

# Or run directly
pip install flask
python3 app.py
```

App runs on port **5558**.
