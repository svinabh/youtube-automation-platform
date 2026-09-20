from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .config import get_settings
from .models import Base
s=get_settings();engine=create_engine(s.database_url,connect_args={"check_same_thread":False} if s.database_url.startswith("sqlite") else {},pool_pre_ping=True);SessionLocal=sessionmaker(bind=engine)
def init_db():Base.metadata.create_all(engine)
def get_db():
 db=SessionLocal()
 try:yield db
 finally:db.close()
