# Kuleshov Lab - Backend API

Backend API for the Kuleshov Lab cinematic recommendation engine.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and add your TMDB API key:

```bash
cp .env.example .env
```

Edit `.env`:
```env
TMDB_API_KEY=your_actual_tmdb_api_key_here
```

Get your TMDB API key at: https://www.themoviedb.org/settings/api

**Optional - For FASE 3 (Claude AI):**
```env
CLAUDE_API_KEY=your_actual_claude_api_key_here
```

Get your Claude API key at: https://console.anthropic.com/

> **Note**: Claude is optional. Without it, the system uses only embedding-based recommendations. With Claude, you get intelligent re-ranking and personalized explanations.

### 3. Run the Server

```bash
python -m app.main
```

Or with uvicorn directly:
```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📡 API Endpoints

### Recommendations

#### POST `/api/recommend/vibe`
Get movie recommendations based on vibe description.

**Request:**
```json
{
  "vibe": "neon-drenched 80s thriller",
  "limit": 10,
  "filters": {
    "year_min": 1980,
    "year_max": 1989
  }
}
```

**Response:**
```json
{
  "vibe": "neon-drenched 80s thriller",
  "movies": [
    {
      "id": 78,
      "title": "Blade Runner",
      "overview": "...",
      "release_date": "1982-06-25",
      "genres": ["Science Fiction", "Thriller"],
      "poster_url": "https://image.tmdb.org/t/p/w500/...",
      "score": 0.892
    }
  ],
  "total": 10
}
```

### User Actions

#### POST `/api/movies/{movie_id}/watched`
Mark a movie as watched/liked/disliked.

**Request:**
```json
{
  "status": "watched",
  "rating": 8.5
}
```

#### GET `/api/user/watched`
Get list of watched movies.

#### GET `/api/user/stats`
Get user statistics.

**Response:**
```json
{
  "total_watched": 42,
  "total_liked": 15,
  "total_disliked": 3,
  "favorite_genres": [
    ["Thriller", 12],
    ["Science Fiction", 10]
  ],
  "watch_time_hours": 84.5
}
```

## 🏗️ Architecture

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI app & endpoints
│   ├── config.py         # Configuration
│   ├── models.py         # Pydantic models
│   ├── database.py       # SQLite operations (user data only)
│   ├── tmdb.py           # TMDB API client
│   ├── embeddings.py     # Sentence-Transformers (local)
│   ├── claude.py         # Claude AI client (FASE 3)
│   └── recommender.py    # Recommendation engine
├── data/
│   └── kuleshov.db       # SQLite database (user data only)
├── requirements.txt
├── .env
└── README.md
```

## 🧠 How It Works

### Complete Flow (All Phases Implemented)

1. **User Input**: "something romantic that feels like Mr Darcy"

2. **TMDB Fetch** (FASE 1):
   - Fetch ~1,600 movies from TMDB (4 sources: top rated, popular, recent, box office)
   - Get full details including genres, overview, etc.

3. **Embedding Matching** (FASE 1):
   - Convert vibe to vector using Sentence-Transformers
   - Generate/retrieve embeddings for each movie (cached)
   - Calculate cosine similarity
   - Get top 30 candidates

4. **User Filtering** (FASE 2):
   - Exclude movies already watched
   - Apply any user filters (year, genre, etc.)

5. **Claude Re-ranking** (FASE 3) ⭐:
   - Send top 30 to Claude with user profile
   - Claude understands cultural context ("Mr Darcy" = Jane Austen = Regency era)
   - Re-ranks based on vibe, not just keywords
   - Generates personalized explanation for each recommendation

6. **Return**: Top 10 perfectly matched movies with explanations

### Why This Works Better

**Without Claude**:
- "Mr Darcy" → matches on keywords → random results

**With Claude**:
- "Mr Darcy" → understands Jane Austen → Regency romance → period dramas → Pride & Prejudice, Emma, Sense and Sensibility

## 🔧 Development

### Run Tests
```bash
pytest
```

### Format Code
```bash
black app/
```

### Type Checking
```bash
mypy app/
```

## 📊 Database Schema

**Philosophy**: TMDB is our source of truth for movie data. We only store user-specific data locally.

### user_movies
Tracks what users have watched/liked/disliked.

```sql
CREATE TABLE user_movies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER DEFAULT 1,
    movie_id INTEGER NOT NULL,
    movie_title TEXT,
    status TEXT CHECK(status IN ('watched', 'liked', 'disliked')),
    rating REAL,
    watched_at TIMESTAMP,
    UNIQUE(user_id, movie_id)
);
```

### embedding_cache (optional)
Caches embeddings for performance (in-memory cache is also used).

```sql
CREATE TABLE embedding_cache (
    movie_id INTEGER PRIMARY KEY,
    embedding BLOB NOT NULL,
    cached_at TIMESTAMP
);
```

**Benefits of this approach:**
- ✅ Always fresh movie data from TMDB
- ✅ Minimal local storage (only user data)
- ✅ No need to sync/update movie database
- ✅ Simpler architecture

## 🐛 Troubleshooting

### "Import aiosqlite could not be resolved"
This is a type checking warning. Install dependencies:
```bash
pip install -r requirements.txt
```

### "TMDB API key not found"
Make sure you've created `.env` file with your TMDB API key.

### Slow first request
The first time you search for a vibe, the system needs to:
1. Fetch movies from TMDB
2. Generate embeddings for each movie
3. Calculate similarities

This may take 10-20 seconds. Subsequent requests are faster due to in-memory caching.

## 💰 Cost Optimization

### Without Claude (FASE 1-2)
- **TMDB API**: Free (up to 1M requests/month)
- **Embeddings**: Local (Sentence-Transformers, no API costs)
- **Database**: SQLite (local, minimal storage)
- **Total**: **$0/month**

### With Claude (FASE 3)
- **TMDB API**: Free
- **Embeddings**: Local ($0)
- **Database**: SQLite ($0)
- **Claude API**: ~$0.50-2/month (with prompt caching)
  - ~50 requests/day
  - Prompt caching reduces costs by 90%
  - Only top 30 movies sent per request
- **Total**: **~$0.50-2/month**

**Cost Optimization Strategies:**
1. **Prompt Caching**: System prompt cached (90% discount)
2. **Batch Processing**: Send top 30, not all candidates
3. **Smart Fallback**: Works without Claude if API key not set
4. **In-Memory Cache**: Embeddings cached to reduce TMDB calls

**Why this is efficient:**
- No need to maintain a large movie database
- TMDB handles all movie data updates
- We only cache what we need (embeddings)
- Claude only used for final re-ranking (not search)
- Minimal storage footprint

## 📝 TODO

- [ ] Add caching layer for TMDB responses
- [ ] Implement user authentication
- [ ] Add Claude integration (Phase 3)
- [ ] Add more sophisticated filtering
- [ ] Implement collaborative filtering
- [ ] Add Neo4j knowledge graph (Phase 4)

## 📄 License

See [LICENSE](../LICENSE) file for details.