from database import SessionLocal
from models import User
from auth import hash_password

db = SessionLocal()

try:
    email = "tanu@example.com"
    user = db.query(User).filter(User.email == email).first()

    if not user:
        print("Executive account not found.")
    else:
        new_password = input("Enter new executive password: ")

        if len(new_password) < 8:
            print("Password must contain at least 8 characters.")
        else:
            user.hashed_password = hash_password(new_password)
            db.commit()
            print("Executive password reset successfully!")

finally:
    db.close()