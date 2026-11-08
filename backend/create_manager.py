


from database import SessionLocal
from models import User
from auth import hash_password

db = SessionLocal()

try:
    name = input("Manager name: ").strip()
    email = input("Manager email: ").strip().lower()
    password = input("Manager password: ")

    if not name or not email:
        print("Name and email are required.")
    elif len(password) < 8:
        print("Password must contain at least 8 characters.")
    elif db.query(User).filter(User.email == email).first():
        print("This email is already registered.")
    else:
        manager = User(
            name=name,
            email=email,
            hashed_password=hash_password(password),
            role="manager"
        )

        db.add(manager)
        db.commit()

        print("Manager account created successfully!")

except Exception as error:
    db.rollback()
    print("Error:", error)

finally:
    db.close()
