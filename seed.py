import json
from pathlib import Path
from sqlalchemy.orm import Session
from .models import User, Book
from .security import hash_password

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "bookleaf_sample_data.json"

def seed(db: Session):
    if db.query(User).filter(User.email == "admin@bookleaf.local").first():
        return
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    for a in data["authors"]:
        user = User(author_id=a["author_id"], name=a["name"], email=a["email"], phone=a.get("phone"),
                    city=a.get("city"), joined_date=a.get("joined_date"),
                    password_hash=hash_password("BookLeaf@123"), role="author")
        db.add(user)
        db.flush()
        for b in a["books"]:
            book = Book(book_id=b["book_id"], author_user_id=user.id, title=b["title"], isbn=b["isbn"],
                        genre=b["genre"], publication_date=b["publication_date"], status=b["status"],
                        mrp=b["mrp"], author_royalty_per_copy=b["author_royalty_per_copy"],
                        total_copies_sold=b["total_copies_sold"], total_royalty_earned=b["total_royalty_earned"],
                        royalty_paid=b["royalty_paid"], royalty_pending=b["royalty_pending"],
                        last_royalty_payout_date=b["last_royalty_payout_date"], print_partner=b["print_partner"],
                        available_on_json=json.dumps(b["available_on"]))
            db.add(book)
    db.add(User(name="BookLeaf Admin", email="admin@bookleaf.local", password_hash=hash_password("BookLeaf@123"), role="admin"))
    db.commit()
