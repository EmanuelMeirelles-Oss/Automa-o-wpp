from fastapi import FastAPI, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from database import SessionLocal, Lead
import threading

app = FastAPI(title="CRM Bot Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Permite o Vite/Next bater na API
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class LeadCreate(BaseModel):
    nome: str
    telefone: str
    cidade: str
    tem_site: bool

# Estado em Memoria do Motor
BOT_STATUS = {"is_running": False, "logs": []}

@app.get("/api/leads")
def get_leads(db: Session = Depends(get_db)):
    return db.query(Lead).order_by(Lead.id.desc()).all()

@app.post("/api/leads")
def add_lead(lead: LeadCreate, db: Session = Depends(get_db)):
    db_lead = Lead(**lead.model_dump())
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)
    return db_lead

@app.delete("/api/leads/{lead_id}")
def delete_lead(lead_id: int, db: Session = Depends(get_db)):
    obj = db.query(Lead).filter(Lead.id == lead_id).first()
    if obj:
        db.delete(obj)
        db.commit()
    return {"sucesso": True}

@app.get("/api/bot/status")
def get_bot_status():
    return BOT_STATUS

@app.post("/api/bot/start")
def start_bot(background_tasks: BackgroundTasks):
    if BOT_STATUS["is_running"]:
        return {"msg": "Robo ja esta rodando!"}
    
    BOT_STATUS["is_running"] = True
    BOT_STATUS["logs"].append("Robo foi engatado!")
    
    # Inicia o Loop principal do Robo em segundo plano
    from headless_sender import run_bot_worker
    
    thread = threading.Thread(target=run_bot_worker)
    thread.start()
    return {"msg": "Robo Iniciado com Sucesso"}

@app.post("/api/bot/stop")
def stop_bot():
    BOT_STATUS["is_running"] = False
    BOT_STATUS["logs"].append("Ordem de parada enviada. O Processo parara no proximo checklist humano.")
    return {"msg": "Sinal de parada emitido!"}
