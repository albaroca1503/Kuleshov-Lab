# Kuleshov Lab — Backend

FastAPI backend for the Kuleshov Lab cinematic recommendation engine.

## Quick start

```bash
pip install -r requirements.txt
cp .env.example .env
# edit .env with your API keys
uvicorn app.main:app --reload --port 8000
```

API available at `http://localhost:8000` — interactive docs at `/docs`.

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `TMDB_API_KEY` | Yes | [TMDB API key](https://www.themoviedb.org/settings/api) |
| `AI_API_KEY` | No | AI API key — enables re-ranking and Signal |
| `FRONTEND_URL` | No | CORS origin (default: `http://localhost:3000`) |

## Populating the vector store

Before running the app for the first time, index movies from TMDB:

```bash
python ingest_movies.py               # ~1,600 movies
python ingest_movies.py --pages 100   # ~8,000 movies
```

## API endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/recommend/vibe` | Vibe-based recommendations |
| `POST` | `/api/recommend/vault` | Recommendations from taste profile |
| `GET` | `/api/recommend/signal` | Film of the day |
| `POST` | `/api/movies/{id}/watched` | Mark film as watched/liked/disliked |
| `GET` | `/api/movies/{id}/details` | Rich film details (streaming, cast, reviews) |
| `GET` | `/api/user/stats` | Vault statistics |
| `GET` | `/api/user/watched-movies` | Vault film list with posters |
| `GET/PUT` | `/api/user/settings` | Country and streaming subscriptions |

## Architecture

```
app/
├── main.py          # FastAPI app and endpoints
├── recommender.py   # Recommendation engine
├── ai_client.py     # AI re-ranking (optional)
├── embeddings.py    # Sentence-Transformers (local)
├── vector_store.py  # ChromaDB interface
├── tmdb.py          # TMDB API client
├── database.py      # SQLite (user data only)
├── models.py        # Pydantic models
└── config.py        # Settings
```

## License

See [LICENSE](../LICENSE).
