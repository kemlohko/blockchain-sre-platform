import os

from sqlalchemy import Column, DateTime, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import func 

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://blockchain:blockchain@postgres:5432/blockchain"
)

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True)
    type = Column(String, nullable=False)
    tx_hash = Column(String, nullable=False)

    status = Column(
        String,
        nullable=False,
        default="QUEUED"
    )

    result = Column(Text, nullable=True)
    error = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

def create_tables():
    Base.metadata.create_all(bind=engine)