#!/bin/bash

# Kuleshov Lab - Start Script
# Inicia el backend y el frontend simultáneamente

echo "🎬 Starting Kuleshov Lab..."
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Función para limpiar procesos al salir
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Iniciar Backend
echo "🚀 Starting Backend (port 8000)..."
cd backend
python -m uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!
cd ..

# Esperar un momento para que el backend inicie
sleep 2

# Iniciar Frontend
echo "🎨 Starting Frontend (port 3001)..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Services started!"
echo ""
echo "📍 Frontend: http://localhost:3001"
echo "📍 Backend:  http://localhost:8000"
echo "📍 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Mantener el script corriendo
wait

