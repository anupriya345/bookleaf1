from pydantic import BaseModel, EmailStr, Field
from typing import Literal

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class TicketCreate(BaseModel):
    book_id: str | None = None
    subject: str = Field(min_length=3, max_length=250)
    description: str = Field(min_length=10, max_length=10000)

class TicketUpdate(BaseModel):
    status: Literal["Open", "In Progress", "Resolved", "Closed"] | None = None
    category: Literal["Royalty & Payments", "ISBN & Metadata Issues", "Printing & Quality", "Distribution & Availability", "Book Status & Production Updates", "General Inquiry"] | None = None
    priority: Literal["Critical", "High", "Medium", "Low"] | None = None
    assigned_admin_id: int | None = None

class MessageIn(BaseModel):
    message: str = Field(min_length=1, max_length=10000)

class NoteIn(BaseModel):
    note: str = Field(min_length=1, max_length=5000)

class DraftIn(BaseModel):
    pass
