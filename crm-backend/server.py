from fastapi import FastAPI, Depends, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from pydantic import BaseModel, field_validator
from database import SessionLocal, Lead
import re
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
    instagram: Optional[str] = None
    avaliacao: Optional[str] = None

    @field_validator('telefone')
    @classmethod
    def normalize_phone(cls, v: str) -> str:
        return re.sub(r'\D', '', v)

# Estado em Memoria do Motor
BOT_STATUS = {"is_running": False, "is_extracting": False, "logs": []}

@app.get("/api/leads")
def get_leads(db: Session = Depends(get_db)):
    return db.query(Lead).order_by(Lead.id.desc()).all()

@app.post("/api/leads")
def add_lead(lead: LeadCreate, db: Session = Depends(get_db)):
    db_lead = Lead(**lead.model_dump())
    db.add(db_lead)
    try:
        db.commit()
        db.refresh(db_lead)
        return db_lead
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Já existe um lead com este telefone na fila.")

@app.put("/api/leads/{lead_id}/reset")
def reset_lead_status(lead_id: int, db: Session = Depends(get_db)):
    obj = db.query(Lead).filter(Lead.id == lead_id).first()
    if obj:
        obj.status_disparo = "PENDENTE"
        db.commit()
    return {"sucesso": True}

@app.delete("/api/leads/clear")
def clear_leads(db: Session = Depends(get_db)):
    db.query(Lead).delete()
    db.commit()
    return {"sucesso": True}

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

@app.post("/api/bot/extract")
def extract_leads(query: dict):
    if BOT_STATUS["is_extracting"]:
        return {"msg": "Extrator ja esta rodando!"}

    termo = query.get("termo", "")
    if not termo:
        return {"msg": "Termo de busca vazio!"}
    
    BOT_STATUS["is_extracting"] = True
    
    from maps_extractor import run_maps_extraction
    thread = threading.Thread(target=run_maps_extraction, args=(termo,))
    thread.start()
    return {"msg": "Extrator iniciado!"}

@app.post("/api/bot/stop_extract")
def stop_extract():
    BOT_STATUS["is_extracting"] = False
    BOT_STATUS["logs"].append("🛑 Ordem de parada enviada ao Extrator.")
    return {"msg": "Parada solicitada!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
