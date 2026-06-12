# Kuleshov Lab

<div align="center">
  <p>AI-powered cinematic curation platform</p>
  <p>Discover films through mood, atmosphere, and vibe — not just genres or ratings</p>
</div>

---

## Features

- **Engine** — describe a vibe in natural language and get a curated list of films that match the feeling, not just the genre
- **Vault** — your personal film archive with stats, taste analysis, and a downloadable dossier
- **Signal** — one film pick per day, chosen by AI based on your taste profile and the time of year

## How it works

1. You describe what you want to feel — *"paranoid surveillance, cold and fractured"* or *"a melancholic rainy afternoon in Tokyo"*
2. The description is embedded as a vector and matched against ~8,000 indexed films in ChromaDB using semantic similarity
3. Liked and disliked films shift the query vector over time (Rocchio algorithm), so results improve as you use the app
4. If an AI API key is configured, the top candidates are re-ranked by a language model that understands cultural context, not just keywords

## Stack

**Frontend:** React 19 + TypeScript + Vite + Tailwind CSS 4  
**Backend:** FastAPI + ChromaDB + SQLite + TMDB API  
**Embeddings:** Sentence-Transformers (local, no API cost)  
**AI re-ranking:** optional — the app works fully without it

## Setup

### Requirements

- Python 3.11+
- Node.js 18+
- [TMDB API key](https://www.themoviedb.org/settings/api) (free)
- AI API key (optional — needed for intelligent re-ranking and Signal)

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and add your keys:

```env
TMDB_API_KEY=your_key_here
AI_API_KEY=your_key_here   # optional
```

### 2. Populate the vector store

The first time you run the app, index movies from TMDB into ChromaDB:

```bash
cd backend
python ingest_movies.py
# default: ~1,600 movies — takes a few minutes
# python ingest_movies.py --pages 100  # ~8,000 movies
```

This downloads movie data from TMDB and generates local embeddings. Only needed once.

### 3. Frontend

```bash
cd frontend
npm install
```

### 4. Run

```bash
./start.sh
```

Or manually:

```bash
# Terminal 1
cd backend && uvicorn app.main:app --reload --port 8000

# Terminal 2
cd frontend && npm run dev
```

- Frontend: [http://localhost:3001](http://localhost:3001)
- API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

## License

See [LICENSE](LICENSE).

---

<div align="center">
  <i>"In the cinema, the combination of shots is the essence of the art."</i><br>
  — Lev Kuleshov
</div>
