from fastapi import FastAPI, Depends
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

# SQLAlchemy for SQLite
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# ===========================
# Database Setup (SQLite)
# ===========================
DATABASE_URL = "sqlite:///./contacts.db"

Base = declarative_base()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class ContactDB(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    phoneNumber = Column(String, nullable=True)
    email = Column(String, nullable=True)
    linkedId = Column(Integer, nullable=True)  # points to primary
    linkPrecedence = Column(String, default="primary")  # primary or secondary
    createdAt = Column(DateTime, default=datetime.now)
    updatedAt = Column(DateTime, default=datetime.now)
    deletedAt = Column(DateTime, nullable=True)


Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ===========================
# FastAPI App
# ===========================
app = FastAPI(title="Bitespeed Identity Reconciliation API")


class IdentifyRequest(BaseModel):
    email: Optional[str] = None
    phoneNumber: Optional[str] = None


# ===========================
# Helper DB Functions
# ===========================
def find_matching(db: Session, email: Optional[str], phone: Optional[str]):
    """Find contacts matching email or phone"""
    q = db.query(ContactDB)
    if email and phone:
        return q.filter((ContactDB.email == email) | (ContactDB.phoneNumber == phone)).all()
    elif email:
        return q.filter(ContactDB.email == email).all()
    elif phone:
        return q.filter(ContactDB.phoneNumber == phone).all()
    return []


def create_contact(db: Session, email: Optional[str], phone: Optional[str],
                   linkedId: Optional[int] = None, linkPrecedence="primary"):
    """Create a new contact (primary or secondary)"""
    new_contact = ContactDB(
        email=email,
        phoneNumber=phone,
        linkedId=linkedId,
        linkPrecedence=linkPrecedence,
        createdAt=datetime.now(),
        updatedAt=datetime.now()
    )
    db.add(new_contact)
    db.commit()
    db.refresh(new_contact)
    return new_contact


# ===========================
# Identify Endpoint
# ===========================
@app.post("/identify")
def identify(req: IdentifyRequest, db: Session = Depends(get_db)):

    # Step 1: find existing matches
    matches = find_matching(db, req.email, req.phoneNumber)

    # Case 1: No matches → create primary
    if not matches:
        new_primary = create_contact(db, req.email, req.phoneNumber)
        return {
            "contact": {
                "primaryContatctId": new_primary.id,
                "emails": [req.email] if req.email else [],
                "phoneNumbers": [req.phoneNumber] if req.phoneNumber else [],
                "secondaryContactIds": []
            }
        }

    # Case 2: Matches found → get the oldest primary
    primary = min(matches, key=lambda c: c.createdAt if c.createdAt else datetime.now())
    if primary.linkedId:  # if it's secondary, get its actual primary
        primary = db.query(ContactDB).filter(ContactDB.id == primary.linkedId).first()

    # Get all linked contacts for this primary
    linked_contacts = db.query(ContactDB).filter(
        (ContactDB.id == primary.id) | (ContactDB.linkedId == primary.id)
    ).all()

    # Collect all known emails/phones
    all_emails = {c.email for c in linked_contacts if c.email}
    all_phones = {c.phoneNumber for c in linked_contacts if c.phoneNumber}

    # If request contains *new info*, create a secondary contact
    if (req.email and req.email not in all_emails) or (req.phoneNumber and req.phoneNumber not in all_phones):
        new_sec = create_contact(db, req.email, req.phoneNumber,
                                 linkedId=primary.id, linkPrecedence="secondary")
        linked_contacts.append(new_sec)

    # Merge for response
    emails = [primary.email] + [c.email for c in linked_contacts if c.email and c.email != primary.email]
    phones = [primary.phoneNumber] + [c.phoneNumber for c in linked_contacts if c.phoneNumber and c.phoneNumber != primary.phoneNumber]
    secondary_ids = [c.id for c in linked_contacts if c.id != primary.id]

    return {
        "contact": {
            "primaryContatctId": primary.id,
            "emails": list(dict.fromkeys(filter(None, emails))),
            "phoneNumbers": list(dict.fromkeys(filter(None, phones))),
            "secondaryContactIds": secondary_ids
        }
    }


# ===========================
# Debug Endpoint - List all contacts
# ===========================
@app.get("/contacts")
def list_contacts(db: Session = Depends(get_db)):
    contacts = db.query(ContactDB).all()
    return [
        {
            "id": c.id,
            "email": c.email,
            "phoneNumber": c.phoneNumber,
            "linkedId": c.linkedId,
            "linkPrecedence": c.linkPrecedence,
            "createdAt": c.createdAt,
            "updatedAt": c.updatedAt
        }
        for c in contacts
    ]


# Root route just for test
@app.get("/")
def root():
    return {"message": "Bitespeed API running! Use /docs for API documentation."}
