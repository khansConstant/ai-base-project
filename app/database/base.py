from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from app.config.settings import get_settings
import ssl
import os

settings = get_settings()

# Configure SSL for RDS
ssl_args = {
    'sslmode': 'require',
    'connect_timeout': 5  # 5 seconds timeout
}

# Create engine with SSL configuration
engine = create_engine(
    settings.DATABASE_URL,
    connect_args=ssl_args,
    pool_pre_ping=True,  # Enable connection health checks
    pool_recycle=300,    # Recycle connections after 5 minutes
)

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a base class for models
Base = declarative_base()

# Get the existing leads table
try:
    metadata = MetaData()
    leads_table = Table('leads', metadata, autoload_with=engine)
    
    # Define a model for the existing table
    class Lead(Base):
        __table__ = leads_table
        
except Exception as e:
    print(f"Warning: Could not load 'leads' table: {str(e)}")
    Lead = None

def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
