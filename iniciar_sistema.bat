@echo off
echo Iniciando o Servidor Backend (FastAPI)...
start cmd /k "cd /d %~dp0\crm-backend && python server.py"

echo Iniciando o Painel Frontend (Vite)...
start cmd /k "cd /d %~dp0\crm-dashboard && npm run dev"

echo Tudo iniciado! O painel deve abrir automaticamente ou acesse: http://localhost:5173
pause
