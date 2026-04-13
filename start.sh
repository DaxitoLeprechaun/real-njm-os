#!/usr/bin/env bash
# NJM OS — Levanta backend (FastAPI :8000) y frontend (Next.js :3000) en paralelo.
# Uso: ./start.sh
# Requiere: backend/.env con ANTHROPIC_API_KEY=sk-ant-...

set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

# ── Colores ────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log()  { echo -e "${CYAN}[NJM OS]${NC} $1"; }
ok()   { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
err()  { echo -e "${RED}[ERROR]${NC} $1"; }

# ── Guardia: .env ──────────────────────────────────────────────────
if [ ! -f "$BACKEND_DIR/.env" ]; then
  err "Falta $BACKEND_DIR/.env"
  echo "  Crea el archivo con:"
  echo "    echo 'ANTHROPIC_API_KEY=sk-ant-...' > backend/.env"
  exit 1
fi

if ! grep -q "ANTHROPIC_API_KEY" "$BACKEND_DIR/.env"; then
  warn "backend/.env existe pero no contiene ANTHROPIC_API_KEY."
fi

# ── Guardia: venv ──────────────────────────────────────────────────
PYTHON_BIN="$BACKEND_DIR/.venv/bin/python3"
UVICORN_BIN="$BACKEND_DIR/.venv/bin/uvicorn"

if [ ! -f "$UVICORN_BIN" ]; then
  err "No se encontró uvicorn en $BACKEND_DIR/.venv/bin/"
  echo "  Crea el entorno virtual e instala dependencias:"
  echo "    cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
  exit 1
fi

# ── Guardia: node_modules ──────────────────────────────────────────
if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
  err "node_modules no encontrado en frontend/."
  echo "  Instala dependencias con:"
  echo "    cd frontend && npm install"
  exit 1
fi

# ── Cleanup al salir (Ctrl+C mata ambos procesos) ──────────────────
cleanup() {
  log "Deteniendo servidores..."
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
  wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
  log "Servidores detenidos."
}
trap cleanup INT TERM

# ── Lanzar FastAPI ─────────────────────────────────────────────────
log "Iniciando FastAPI en http://localhost:8000 ..."
cd "$BACKEND_DIR"
# Cargar .env manualmente para que uvicorn lo herede
set -a; source .env; set +a
"$UVICORN_BIN" main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
ok "Backend PID: $BACKEND_PID"

# ── Lanzar Next.js ─────────────────────────────────────────────────
log "Iniciando Next.js en http://localhost:3000 ..."
cd "$FRONTEND_DIR"
npm run dev -- --port 3000 &
FRONTEND_PID=$!
ok "Frontend PID: $FRONTEND_PID"

# ── Info final ─────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "  Backend  → ${CYAN}http://localhost:8000${NC}       (FastAPI + LangGraph)"
echo -e "  Frontend → ${CYAN}http://localhost:3000${NC}       (Next.js 14)"
echo -e "  API Docs → ${CYAN}http://localhost:8000/docs${NC}  (Swagger UI)"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "  Ctrl+C para detener ambos servidores."
echo ""

# ── Esperar a que alguno muera ─────────────────────────────────────
wait "$BACKEND_PID" "$FRONTEND_PID"
