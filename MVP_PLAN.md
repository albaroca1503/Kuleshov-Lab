# Kuleshov Lab - Plan MVP (Versión Simplificada)

## 🎯 Filosofía: Funcionalidad antes que infraestructura

**Objetivo**: Tener recomendaciones por vibe funcionando en **3-5 días**, no 3 semanas.

## 📋 MVP v1.0 - Lo Esencial

### Stack Mínimo
```
FastAPI + SQLite + Sentence-Transformers + TMDB + Claude (limitado)
```

**NO incluye en v1**:
- ❌ Neo4j (añadir en v2 cuando tengamos datos reales)
- ❌ Sistema complejo de caché (solo básico)
- ❌ Algoritmos avanzados de grafo
- ❌ Autenticación compleja

## 🚀 Fases de Implementación

### FASE 1: Vibe Matching (Días 1-2)
**El core diferencial del producto**

```python
# Lo mínimo viable:
1. Endpoint: POST /api/recommend/vibe
   Input: { "vibe": "neon-drenched 80s thriller" }
   Output: [10 películas con scores]

2. Componentes:
   - Cliente TMDB básico (sin caché sofisticado)
   - Sentence-Transformers local
   - Búsqueda por similitud de embeddings
   - SQLite simple para almacenar películas
```

**Flujo simplificado**:
```
Usuario → vibe text → embedding local → 
buscar en SQLite → top 20 por similitud → 
devolver top 10
```

**Sin Claude en esta fase** - Solo embeddings locales para validar el concepto.

### FASE 2: Perfil de Usuario (Días 3-4)
**Tracking básico de películas vistas**

```python
# Añadir:
1. Tabla user_movies (SQLite)
   - user_id, movie_id, status (watched/liked/disliked)
   
2. Endpoint: POST /api/movies/{id}/mark-watched

3. Modificar /api/recommend/vibe:
   - Excluir películas ya vistas
   - Usar historial para ajustar scores
```

**Flujo actualizado**:
```
Usuario → vibe text → embedding → 
buscar candidatas → EXCLUIR vistas → 
ajustar por perfil → top 10
```

### FASE 3: Claude para Explicaciones (Día 5)
**Añadir inteligencia contextual**

```python
# Integrar Claude:
1. Solo para re-ranking final y explicaciones
2. Recibe: top 20 + perfil usuario + vibe
3. Devuelve: top 10 ordenadas + razón por cada una
4. Caché agresivo (7 días)
```

**Flujo final v1**:
```
Usuario → vibe → embedding → candidatas → 
excluir vistas → top 20 → 
Claude re-rankea → top 10 con explicaciones
```

## 📦 Estructura MVP

```
backend/
├── app/
│   ├── main.py              # FastAPI app (50 líneas)
│   ├── config.py            # Settings
│   ├── database.py          # SQLite simple
│   ├── models.py            # Pydantic models
│   ├── tmdb.py              # Cliente TMDB básico
│   ├── embeddings.py        # Sentence-Transformers
│   ├── recommender.py       # Lógica core (100 líneas)
│   └── claude.py            # Claude client (FASE 3)
├── data/
│   └── movies.db            # SQLite
├── requirements.txt
├── .env
└── README.md
```

**Total estimado: ~500 líneas de código**

## 🗄️ Esquema SQLite Mínimo

```sql
-- FASE 1
CREATE TABLE movies (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    overview TEXT,
    release_date TEXT,
    genres TEXT,
    vibe_embedding BLOB,
    tmdb_data TEXT,
    cached_at TIMESTAMP
);

-- FASE 2
CREATE TABLE user_movies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER DEFAULT 1,  -- Single user por ahora
    movie_id INTEGER NOT NULL,
    status TEXT CHECK(status IN ('watched', 'liked', 'disliked')),
    watched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, movie_id)
);

-- FASE 3 (opcional)
CREATE TABLE recommendations_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vibe_hash TEXT NOT NULL,
    user_id INTEGER,
    results TEXT,  -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vibe_hash, user_id)
);
```

## 🔌 API Endpoints MVP

### FASE 1
```
POST /api/recommend/vibe
Body: { "vibe": "string", "limit": 10 }
Response: [{ "id", "title", "overview", "score", "poster_url" }]
```

### FASE 2
```
POST /api/movies/{id}/watched
GET  /api/user/watched
GET  /api/user/stats
```

### FASE 3
```
POST /api/recommend/vibe (mejorado con Claude)
Response: [{ ..., "reason": "Porque te gustó X y tiene Y" }]
```

## 💡 Implementación del Vibe Matching

### Versión Simple (FASE 1)

```python
from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer('all-MiniLM-L6-v2')

def recommend_by_vibe(vibe: str, limit: int = 10):
    # 1. Embedding del vibe
    vibe_vector = model.encode(vibe)
    
    # 2. Buscar películas en SQLite
    movies = db.query("SELECT * FROM movies LIMIT 1000")
    
    # 3. Calcular similitud
    scores = []
    for movie in movies:
        movie_vector = np.frombuffer(movie.vibe_embedding)
        similarity = cosine_similarity(vibe_vector, movie_vector)
        scores.append((movie, similarity))
    
    # 4. Ordenar y devolver top N
    scores.sort(key=lambda x: x[1], reverse=True)
    return [movie for movie, score in scores[:limit]]
```

### Con Perfil de Usuario (FASE 2)

```python
def recommend_by_vibe(vibe: str, user_id: int = 1, limit: int = 10):
    vibe_vector = model.encode(vibe)
    
    # Excluir películas vistas
    watched_ids = db.query(
        "SELECT movie_id FROM user_movies WHERE user_id = ?",
        (user_id,)
    )
    watched_set = {row[0] for row in watched_ids}
    
    # Buscar candidatas
    movies = db.query("SELECT * FROM movies LIMIT 1000")
    
    scores = []
    for movie in movies:
        if movie.id in watched_set:
            continue  # SKIP películas vistas
            
        movie_vector = np.frombuffer(movie.vibe_embedding)
        similarity = cosine_similarity(vibe_vector, movie_vector)
        
        # Ajustar por perfil (simple)
        user_boost = calculate_user_affinity(user_id, movie)
        final_score = 0.7 * similarity + 0.3 * user_boost
        
        scores.append((movie, final_score))
    
    scores.sort(key=lambda x: x[1], reverse=True)
    return [movie for movie, score in scores[:limit]]
```

### Con Claude (FASE 3)

```python
def recommend_by_vibe(vibe: str, user_id: int = 1, limit: int = 10):
    # 1-2. Igual que antes, pero top 20
    candidates = get_candidates_by_vibe(vibe, user_id, limit=20)
    
    # 3. Claude re-rankea
    user_profile = get_user_profile_text(user_id)
    
    prompt = f"""
    Usuario: {user_profile}
    Busca: {vibe}
    
    Candidatas:
    {format_movies(candidates)}
    
    Devuelve las 10 mejores ordenadas con razón breve para cada una.
    """
    
    response = claude.complete(prompt, cache_ttl=604800)  # 7 días
    
    return parse_claude_response(response)
```

## 📊 Flujo Completo (Diagrama del Feedback)

```
┌─────────────────────────────────────────┐
│  POST /api/recommend/vibe               │
│  { vibe, filters?, user_id }            │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  1. Excluir películas vistas            │
│  SELECT movie_id FROM user_movies       │
│  WHERE user_id = X → blacklist          │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  2. Filtros duros (SQL)                 │
│  género IN [...] · año BETWEEN x AND y  │
│  → pool de candidatas válidas           │
└──────────────┬──────────────────────────┘
               │
               ▼
        ┌──────┴──────┐
        │  ¿hay vibe? │
        └──┬───────┬──┘
           │       │
      sí   │       │ no
           │       │
           ▼       ▼
    ┌──────────┐ ┌──────────┐
    │  Vibe    │ │  Perfil  │
    │ embedding│ │ embedding│
    └────┬─────┘ └─────┬────┘
         │             │
         └──────┬──────┘
                ▼
    ┌────────────────────────┐
    │  Combinar scores       │
    │  0.5×perfil + 0.5×vibe │
    │  → top 20              │
    └────────┬───────────────┘
             │
             ▼
    ┌────────────────────────┐
    │  Claude re-rankea      │
    │  top 20 → top 10       │
    │  + explicaciones       │
    └────────┬───────────────┘
             │
             ▼
    ┌────────────────────────┐
    │  Top 10 recomendaciones│
    │  garantizadas: no      │
    │  vistas · con filtros  │
    └────────────────────────┘
```

## 🎯 Criterios de Éxito MVP

### FASE 1 ✅
- [ ] Puedo buscar "neon 80s thriller" y recibo 10 películas relevantes
- [ ] Los embeddings locales funcionan razonablemente bien
- [ ] Respuesta en < 2 segundos

### FASE 2 ✅
- [ ] Puedo marcar películas como vistas
- [ ] Las recomendaciones nunca incluyen películas vistas
- [ ] El perfil de usuario influye en los resultados

### FASE 3 ✅
- [ ] Claude mejora el ranking
- [ ] Cada recomendación tiene una explicación
- [ ] Costo de Claude < $3/mes

## 🚫 Lo que NO haremos en MVP

1. **Neo4j** - Añadir en v2 cuando sepamos qué queries necesitamos
2. **Autenticación compleja** - Single user por ahora
3. **Sistema de caché distribuido** - Solo caché local simple
4. **Algoritmos avanzados** - Solo cosine similarity
5. **UI compleja** - Enfocarse en API funcional
6. **Tests exhaustivos** - Solo tests básicos
7. **Deployment** - Solo local por ahora
8. **Optimizaciones prematuras** - Funcionalidad primero

## 📅 Timeline Realista

| Día | Tarea | Entregable |
|-----|-------|------------|
| 1 | Setup + TMDB + Embeddings | Búsqueda básica funciona |
| 2 | Vibe matching + API | Endpoint /recommend/vibe |
| 3 | User tracking | Marcar vistas + excluir |
| 4 | Perfil de usuario | Ajustar scores por historial |
| 5 | Integrar Claude | Explicaciones + re-ranking |

**Total: 5 días para MVP funcional**

## 🔄 Roadmap Post-MVP

### v1.1 (Semana 2)
- Filtros avanzados (año, duración, idioma)
- Caché mejorado
- Tests básicos

### v2.0 (Semana 3-4)
- **Neo4j** (ahora sí, con datos reales)
- Collaborative filtering
- Múltiples usuarios

### v3.0 (Mes 2)
- Algoritmos de grafo avanzados
- Análisis de gustos profundo
- Deployment en producción

## 💰 Costos Estimados MVP

| Servicio | Uso MVP | Costo |
|----------|---------|-------|
| TMDB | ~500 requests/día | $0 |
| Claude | ~50 requests/día (cached) | $1-2/mes |
| Embeddings | Local | $0 |
| SQLite | Local | $0 |
| **TOTAL** | | **$1-2/mes** |

## 🎬 Próximo Paso

**¿Empezamos con FASE 1?**

Crear:
1. `backend/app/main.py` - FastAPI básico
2. `backend/app/tmdb.py` - Cliente TMDB
3. `backend/app/embeddings.py` - Sentence-Transformers
4. `backend/app/recommender.py` - Lógica de vibe matching

**Objetivo**: En 2 días tener `/api/recommend/vibe` funcionando.

---

**Principio clave**: Construir → Medir → Aprender → Iterar

No optimizar lo que no existe. No escalar lo que no funciona.