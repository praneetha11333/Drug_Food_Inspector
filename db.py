import os
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy.sql import func
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Models ---

class Patient(Base):
    __tablename__ = "patients"

    id              = Column(Integer, primary_key=True, index=True)
    name            = Column(String, nullable=False)
    phone           = Column(String, nullable=False, unique=True)
    age             = Column(Integer)
    caregiver_phone = Column(String)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    medications = relationship("Medication", back_populates="patient", cascade="all, delete")
    call_logs   = relationship("CallLog", back_populates="patient", cascade="all, delete")
    escalations = relationship("Escalation", back_populates="patient", cascade="all, delete")


class Medication(Base):
    __tablename__ = "medications"

    id         = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    name       = Column(String, nullable=False)
    dosage     = Column(String)
    schedule   = Column(String, nullable=False)   # e.g. "08:00,20:00"
    active     = Column(Boolean, default=True)

    patient = relationship("Patient", back_populates="medications")


class CallLog(Base):
    __tablename__ = "call_logs"

    id          = Column(Integer, primary_key=True, index=True)
    patient_id  = Column(Integer, ForeignKey("patients.id"), nullable=False)
    called_at   = Column(DateTime(timezone=True), server_default=func.now())
    outcome     = Column(String)    # 'confirmed', 'missed', 'no_answer'
    agent_notes = Column(Text)

    patient = relationship("Patient", back_populates="call_logs")


class Escalation(Base):
    __tablename__ = "escalations"

    id           = Column(Integer, primary_key=True, index=True)
    patient_id   = Column(Integer, ForeignKey("patients.id"), nullable=False)
    reason       = Column(Text, nullable=False)
    escalated_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved     = Column(Boolean, default=False)

    patient = relationship("Patient", back_populates="escalations")


def create_tables():
    Base.metadata.create_all(bind=engine)
    print("All tables created successfully.")


if __name__ == "__main__":
    create_tables()
