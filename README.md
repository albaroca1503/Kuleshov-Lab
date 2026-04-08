# Kuleshov Lab

<div align="center">
  <h3>🎬 A sophisticated cinematic curation platform</h3>
  <p>Discover, curate, and experience films through an elegant, film noir-inspired interface</p>
</div>

---

## 📁 Project Structure

```
Kuleshov-Lab/
├── frontend/          # React + TypeScript web application
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── hooks/          # Custom React hooks
│   │   ├── services/       # API services
│   │   ├── App.tsx         # Main application
│   │   └── index.css       # Global styles
│   ├── package.json
│   └── README.md
├── backend/           # FastAPI backend
│   ├── app/
│   │   ├── main.py         # FastAPI application
│   │   ├── models.py       # Data models
│   │   ├── database.py     # Database operations
│   │   ├── recommender.py  # Recommendation engine
│   │   ├── embeddings.py   # Semantic embeddings
│   │   ├── tmdb.py         # TMDB API client
│   │   └── claude.py       # Claude AI integration
│   ├── requirements.txt
│   └── README.md
├── start.sh           # Quick start script
├── INTEGRATION.md     # Integration documentation
└── LICENSE
```

## 🚀 Quick Start

### Option 1: Use the Start Script (Recommended)

```bash
./start.sh
```

This will start both the backend and frontend automatically.

### Option 2: Manual Start

**Terminal 1 - Backend:**
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Access the Application

- **Frontend**: http://localhost:3001
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## ⚙️ Configuration

### Backend Setup

1. Copy the environment file:
```bash
cd backend
cp .env.example .env
```

2. Add your API keys to `.env`:
```env
TMDB_API_KEY=your_tmdb_api_key_here
CLAUDE_API_KEY=your_claude_api_key_here  # Optional, for Phase 3
FRONTEND_URL=http://localhost:3001
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. The frontend is pre-configured to connect to the backend on port 8000.

## 🎨 About Kuleshov Lab

Kuleshov Lab is named after Soviet filmmaker Lev Kuleshov, pioneer of montage theory and the "Kuleshov Effect" - demonstrating how context and juxtaposition create meaning in cinema.

This platform embodies that philosophy by helping users discover films through mood, atmosphere, and cinematic qualities rather than just genres or ratings.

### Key Features

- **🎭 Engine**: Vibe-based film discovery using semantic search
- **🗄️ Vault**: Personal curated collection with statistics
- **📱 Feed**: Swipe-style film recommendations (coming soon)
- **🎞️ Cinematic UI**: Film noir aesthetic with authentic grain overlay
- **🤖 AI-Powered**: Semantic embeddings for intelligent recommendations

## 🛠️ Technology Stack

### Frontend
- React 19 + TypeScript
- Vite for blazing-fast development
- Tailwind CSS 4 for styling
- Motion for smooth animations
- Lucide React for icons

### Backend
- FastAPI (Python)
- SQLite with aiosqlite
- Sentence Transformers for embeddings
- TMDB API for movie data
- Claude AI for intelligent re-ranking (optional)

## 📚 Documentation

- [Frontend Documentation](frontend/README.md)
- [Backend Architecture](BACKEND_ARCHITECTURE.md)
- [Integration Guide](INTEGRATION.md)
- [MVP Plan](MVP_PLAN.md)

## 🎯 How It Works

1. **Describe a Vibe**: Enter a mood or atmosphere (e.g., "A neon-drenched 80s thriller")
2. **Semantic Search**: The system uses AI embeddings to understand your description
3. **Get Recommendations**: Receive curated film suggestions that match your vibe
4. **Build Your Vault**: Save and track films you've watched

## 🐛 Troubleshooting

### Backend not starting?
- Check that port 8000 is available
- Verify your `.env` file has the required API keys
- Ensure Python dependencies are installed

### Frontend not connecting?
- Verify the backend is running on port 8000
- Check browser console for CORS errors
- Ensure you're accessing http://localhost:3001

### No recommendations appearing?
- Check that TMDB_API_KEY is set in backend/.env
- Verify the backend logs for errors
- Try a different search query

For more detailed troubleshooting, see [INTEGRATION.md](INTEGRATION.md)

## 📄 License

See [LICENSE](LICENSE) file for details.

---

<div align="center">
  <p><i>"In the cinema, the combination of shots is the essence of the art."</i></p>
  <p>— Lev Kuleshov</p>
  <br>
  <p><b>Made with ❤️ by Bob</b></p>
</div>