
from database import SessionLocal
from models import User
from auth import hash_password

db = SessionLocal()

try:
    email = "tanuchandravanshi9@gmail.com"

    user = db.query(User).filter(User.email == email).first()

    if not user:
        print("Manager account not found.")
    else:
        new_password = input("Enter new manager password: ")

        if len(new_password) < 8:
            print("Password must contain at least 8 characters.")
        else:
            user.hashed_password = hash_password(new_password)
            db.commit()
            print("Manager password reset successfully!")

finally:
    db.close()
