import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import desc
from .db import Base, engine, get_db, SessionLocal
from .models import User, Book, Ticket, TicketMessage, InternalNote
from .schemas import LoginIn, TicketCreate, TicketUpdate, MessageIn, NoteIn
from .security import verify_password, create_token, current_user, admin_user
from .config import FRONTEND_ORIGIN
from .seed import seed
from .ai_service import classify, draft_reply

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()
    yield

app = FastAPI(title="BookLeaf Author Support API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[FRONTEND_ORIGIN, "http://localhost:5173"],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

def user_out(u):
    return {"id":u.id,"name":u.name,"email":u.email,"role":u.role,"author_id":u.author_id}

def book_out(b):
    return {"id":b.id,"book_id":b.book_id,"title":b.title,"isbn":b.isbn,"genre":b.genre,
            "publication_date":b.publication_date,"status":b.status,"mrp":b.mrp,
            "author_royalty_per_copy":b.author_royalty_per_copy,"total_copies_sold":b.total_copies_sold,
            "total_royalty_earned":b.total_royalty_earned,"royalty_paid":b.royalty_paid,
            "royalty_pending":b.royalty_pending,"last_royalty_payout_date":b.last_royalty_payout_date,
            "print_partner":b.print_partner,"available_on":json.loads(b.available_on_json or "[]")}

def ticket_out(db, t, include_private=False):
    author = db.get(User, t.author_user_id)
    book = db.query(Book).filter(Book.book_id == t.book_id).first() if t.book_id else None
    messages = db.query(TicketMessage).filter(TicketMessage.ticket_id == t.id).order_by(TicketMessage.created_at).all()
    out = {"id":t.id,"author_user_id":t.author_user_id,"author_name":author.name if author else "Unknown",
           "book_id":t.book_id,"book_title":book.title if book else "General / Account Level",
           "subject":t.subject,"description":t.description,"category":t.category,"priority":t.priority,
           "status":t.status,"assigned_admin_id":t.assigned_admin_id,
           "created_at":t.created_at.isoformat() if t.created_at else None,
           "updated_at":t.updated_at.isoformat() if t.updated_at else None,
           "messages":[{"id":m.id,"sender_user_id":m.sender_user_id,"sender_name":(db.get(User,m.sender_user_id).name if db.get(User,m.sender_user_id) else "User"),"message":m.message,"created_at":m.created_at.isoformat() if m.created_at else None} for m in messages]}
    if include_private:
        notes = db.query(InternalNote).filter(InternalNote.ticket_id == t.id).order_by(InternalNote.created_at).all()
        out["internal_notes"]=[{"id":n.id,"admin_user_id":n.admin_user_id,"note":n.note,"created_at":n.created_at.isoformat() if n.created_at else None} for n in notes]
    return out

@app.get("/")
def root():
    return {"message":"BookLeaf Author Support API","docs":"/docs"}

@app.post("/api/auth/login")
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email.lower()).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return {"access_token":create_token(user),"token_type":"bearer","user":user_out(user)}

@app.get("/api/auth/me")
def me(user: User = Depends(current_user)):
    return user_out(user)

@app.get("/api/books")
def my_books(db: Session = Depends(get_db), user: User = Depends(current_user)):
    q = db.query(Book)
    if user.role != "admin":
        q = q.filter(Book.author_user_id == user.id)
    books = q.order_by(Book.book_id).all()
    return {"items":[book_out(b) for b in books]}

@app.post("/api/tickets", status_code=201)
async def create_ticket(data: TicketCreate, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if data.book_id:
        book = db.query(Book).filter(Book.book_id == data.book_id).first()
        if not book:
            raise HTTPException(status_code=422, detail="Selected book was not found")
        if user.role != "admin" and book.author_user_id != user.id:
            raise HTTPException(status_code=403, detail="You cannot create a ticket for another author's book")
    t = Ticket(author_user_id=user.id, book_id=data.book_id, subject=data.subject.strip(), description=data.description.strip())
    db.add(t); db.commit(); db.refresh(t)
    try:
        ai = await classify(t.subject, t.description)
        t.category = ai["category"]; t.priority = ai["priority"]
        db.commit(); db.refresh(t)
    except Exception:
        pass
    return ticket_out(db,t)

@app.get("/api/tickets")
def list_tickets(status: str | None = None, category: str | None = None, priority: str | None = None,
                 db: Session = Depends(get_db), user: User = Depends(current_user)):
    q = db.query(Ticket)
    if user.role != "admin":
        q = q.filter(Ticket.author_user_id == user.id)
    if status: q=q.filter(Ticket.status == status)
    if category: q=q.filter(Ticket.category == category)
    if priority: q=q.filter(Ticket.priority == priority)
    items=q.order_by(desc(Ticket.created_at)).all()
    return {"items":[ticket_out(db,t,include_private=(user.role=="admin")) for t in items]}

@app.get("/api/tickets/{ticket_id}")
def get_ticket(ticket_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    t=db.get(Ticket,ticket_id)
    if not t: raise HTTPException(status_code=404,detail="Ticket not found")
    if user.role != "admin" and t.author_user_id != user.id:
        raise HTTPException(status_code=404,detail="Ticket not found")
    return ticket_out(db,t,include_private=(user.role=="admin"))

@app.patch("/api/admin/tickets/{ticket_id}")
def update_ticket(ticket_id: int, data: TicketUpdate, db: Session = Depends(get_db), admin: User = Depends(admin_user)):
    t=db.get(Ticket,ticket_id)
    if not t: raise HTTPException(status_code=404,detail="Ticket not found")
    updates=data.model_dump(exclude_unset=True)
    if "assigned_admin_id" in updates and updates["assigned_admin_id"] is not None:
        target=db.get(User,updates["assigned_admin_id"])
        if not target or target.role!="admin": raise HTTPException(status_code=422,detail="Assigned user must be an admin")
    for k,v in updates.items(): setattr(t,k,v)
    t.updated_at=datetime.now(timezone.utc)
    db.commit(); db.refresh(t)
    return ticket_out(db,t,include_private=True)

@app.post("/api/admin/tickets/{ticket_id}/draft")
async def generate_draft(ticket_id: int, db: Session = Depends(get_db), admin: User = Depends(admin_user)):
    t=db.get(Ticket,ticket_id)
    if not t: raise HTTPException(status_code=404,detail="Ticket not found")
    book=db.query(Book).filter(Book.book_id==t.book_id).first() if t.book_id else None
    context=""
    if book:
        context=f"Book title={book.title}; status={book.status}; earned={book.total_royalty_earned}; paid={book.royalty_paid}; pending={book.royalty_pending}; last payout={book.last_royalty_payout_date}"
    draft=await draft_reply(t.subject,t.description,context)
    return {"draft":draft}

@app.post("/api/admin/tickets/{ticket_id}/messages", status_code=201)
def send_message(ticket_id: int, data: MessageIn, db: Session = Depends(get_db), admin: User = Depends(admin_user)):
    t=db.get(Ticket,ticket_id)
    if not t: raise HTTPException(status_code=404,detail="Ticket not found")
    m=TicketMessage(ticket_id=t.id,sender_user_id=admin.id,message=data.message.strip())
    db.add(m)
    if t.status in ["Open","In Progress"]: t.status="In Progress"
    t.updated_at=datetime.now(timezone.utc)
    db.commit(); db.refresh(m)
    return {"id":m.id,"ticket_id":m.ticket_id,"sender_user_id":m.sender_user_id,"message":m.message,"created_at":m.created_at.isoformat()}

@app.post("/api/admin/tickets/{ticket_id}/notes", status_code=201)
def add_note(ticket_id: int, data: NoteIn, db: Session = Depends(get_db), admin: User = Depends(admin_user)):
    t=db.get(Ticket,ticket_id)
    if not t: raise HTTPException(status_code=404,detail="Ticket not found")
    n=InternalNote(ticket_id=t.id,admin_user_id=admin.id,note=data.note.strip())
    db.add(n); db.commit(); db.refresh(n)
    return {"id":n.id,"ticket_id":n.ticket_id,"note":n.note,"created_at":n.created_at.isoformat()}

@app.get("/api/admin/users")
def admin_users(db: Session = Depends(get_db), admin: User = Depends(admin_user)):
    users=db.query(User).filter(User.role=="admin").all()
    return {"items":[user_out(u) for u in users]}

@app.get("/api/health")
def health():
    return {"status":"ok"}
