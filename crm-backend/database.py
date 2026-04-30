from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///./leads_database.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    telefone = Column(String, unique=True, index=True)
    cidade = Column(String)
    tem_site = Column(Boolean, default=False)
    instagram = Column(String, nullable=True)
    avaliacao = Column(String, nullable=True)
    
    # Status pode ser: PENDENTE, ENVIANDO, SUCESSO, ERRO
    status_disparo = Column(String, default="PENDENTE")
    log_erro = Column(String, nullable=True)
    
    criado_em = Column(DateTime, default=datetime.datetime.utcnow)

Base.metadata.create_all(bind=engine)
