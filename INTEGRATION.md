# Frontend-Backend Integration Guide

## 🎬 Kuleshov Lab - Full Stack Connection

Este documento explica cómo está conectado el frontend con el backend y cómo usarlo.

## 📋 Arquitectura

```
Frontend (React + Vite)     Backend (FastAPI)
Port: 3000                  Port: 8000
     │                           │
     │    HTTP Requests          │
     ├──────────────────────────>│
     │                           │
     │    JSON Responses         │
     │<──────────────────────────┤
     │                           │
```

## 🔧 Configuración Completada

### 1. Backend (FastAPI)
- ✅ CORS configurado para aceptar peticiones desde `http://localhost:3000`
- ✅ Endpoints API disponibles en `/api/*`
- ✅ Health check en `/health`
- ✅ Puerto: 8000

### 2. Frontend (React + Vite)
- ✅ Proxy configurado en `vite.config.ts` para redirigir `/api` al backend
- ✅ Servicio API creado en `frontend/src/services/api.ts`
- ✅ Hook personalizado `useRecommendations` para manejar estado
- ✅ Componentes integrados con el backend
- ✅ Puerto: 3000

## 🚀 Cómo Usar

### Iniciar el Sistema

1. **Terminal 1 - Backend:**
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

2. **Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Probar la Conexión

1. Abre el navegador en `http://localhost:3000`
2. Ve a la vista "Engine"
3. Escribe un vibe, por ejemplo: "A neon-drenched 80s thriller"
4. Presiona Enter o haz clic en una sugerencia
5. El sistema enviará la petición al backend y mostrará las películas recomendadas

## 📡 Endpoints Disponibles

### GET /health
Verifica que el backend esté funcionando.

**Ejemplo:**
```bash
curl http://localhost:8000/health
```

**Respuesta:**
```json
{
  "status": "healthy"
}
```

### POST /api/recommend/vibe
Obtiene recomendaciones basadas en un "vibe".

**Ejemplo:**
```bash
curl -X POST http://localhost:8000/api/recommend/vibe \
  -H "Content-Type: application/json" \
  -d '{
    "vibe": "A neon-drenched 80s thriller",
    "limit": 10
  }'
```

**Respuesta:**
```json
{
  "vibe": "A neon-drenched 80s thriller",
  "movies": [
    {
      "id": 78,
      "title": "Blade Runner",
      "year": 1982,
      "director": "Ridley Scott",
      "poster_path": "/63N9uy8nd9j7Eog2axPQ8lbr3Wj.jpg",
      "similarity_score": 0.89
    }
  ],
  "total": 10
}
```

### POST /api/movies/{movie_id}/watched
Marca una película como vista/gustada/no gustada.

**Ejemplo:**
```bash
curl -X POST http://localhost:8000/api/movies/78/watched \
  -H "Content-Type: application/json" \
  -d '{
    "status": "liked",
    "rating": 9
  }'
```

### GET /api/user/stats
Obtiene estadísticas del usuario.

**Ejemplo:**
```bash
curl http://localhost:8000/api/user/stats
```

### GET /api/user/watched
Obtiene la lista de películas vistas.

**Ejemplo:**
```bash
curl http://localhost:8000/api/user/watched
```

## 🎨 Componentes Frontend

### Servicio API (`frontend/src/services/api.ts`)
Maneja todas las peticiones HTTP al backend.

```typescript
import { api } from './services/api';

// Obtener recomendaciones
const response = await api.getRecommendationsByVibe({
  vibe: "A melancholic rainy afternoon in Tokyo",
  limit: 20
});

// Marcar película como vista
await api.markMovieWatched(123, { status: 'liked', rating: 8 });

// Obtener estadísticas
const stats = await api.getUserStats();
```

### Hook useRecommendations (`frontend/src/hooks/useRecommendations.ts`)
Hook personalizado para manejar el estado de las recomendaciones.

```typescript
import { useRecommendations } from './hooks/useRecommendations';

function MyComponent() {
  const { movies, loading, error, getRecommendations, markWatched } = useRecommendations();
  
  // Buscar películas
  await getRecommendations("Gothic horror in a sun-bleached desert");
  
  // Marcar como vista
  await markWatched(movieId, 'liked');
}
```

## 🔍 Debugging

### Verificar que el Backend está corriendo:
```bash
curl http://localhost:8000/health
```

### Verificar que el Frontend puede acceder al Backend:
Abre las DevTools del navegador (F12) y ve a la pestaña Network. Deberías ver las peticiones a `/api/*` siendo redirigidas correctamente.

### Logs del Backend:
El backend imprime logs en la terminal donde se ejecuta. Busca mensajes como:
```
🚀 Starting Kuleshov Lab Backend...
✅ Backend ready!
```

### Errores Comunes:

1. **CORS Error**: Verifica que `FRONTEND_URL` en el `.env` del backend sea `http://localhost:3000`

2. **Connection Refused**: Asegúrate de que el backend esté corriendo en el puerto 8000

3. **404 Not Found**: Verifica que el proxy en `vite.config.ts` esté configurado correctamente

## 📝 Variables de Entorno

### Backend (`backend/.env`)
```env
TMDB_API_KEY=tu_api_key_aqui
FRONTEND_URL=http://localhost:3000
HOST=0.0.0.0
PORT=8000
```

### Frontend (`frontend/.env`)
```env
VITE_API_URL=http://localhost:8000
```

## 🎯 Próximos Pasos

- [ ] Implementar autenticación de usuarios
- [ ] Agregar más filtros de búsqueda
- [ ] Implementar la vista Feed con swipe
- [ ] Agregar persistencia de películas vistas en la Vault
- [ ] Implementar sistema de ratings y reviews

## 🐛 Reportar Problemas

Si encuentras algún problema con la integración, verifica:
1. Ambos servidores están corriendo
2. Los puertos 3000 y 8000 están disponibles
3. Las variables de entorno están configuradas correctamente
4. El archivo `.env` del backend tiene las API keys necesarias

---

**Made with ❤️ by Bob**