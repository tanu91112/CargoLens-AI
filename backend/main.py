import os
import csv
import io
import uuid
from pathlib import Path
from extractor import extract_document
import jwt
import pymupdf
from validator import validate_documents
from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    status,
    UploadFile,
    File
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database import Base, engine, get_db
from models import User, Shipment, ShipmentDocument, AuditLog

from schemas import (
    UserRegister,
    UserLogin,
    UserResponse,
    TokenResponse,
    ShipmentCreate,
    ShipmentResponse,
    DocumentResponse
)

from auth import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token
)

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="CargoLens AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

def create_audit_log(
    db: Session,
    shipment_id: int,
    user_id: int,
    action: str,
    details: str = None
):
    log = AuditLog(
        shipment_id=shipment_id,
        user_id=user_id,
        action=action,
        details=details
    )

    db.add(log)
    db.commit()


@app.get("/")
def home():
    return {
        "message": "Welcome to CargoLens AI",
        "status": "running"
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register(user_data: UserRegister, db: Session = Depends(get_db)):

    if len(user_data.password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must contain at least 8 characters"
        )

    existing_user = db.query(User).filter(
        User.email == user_data.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    new_user = User(
        name=user_data.name,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        role="executive"
    )

    db.add(new_user)

    try:
        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    return new_user


@app.post("/auth/login", response_model=TokenResponse)
def login(user_data: UserLogin, db: Session = Depends(get_db)):

    user = db.query(User).filter(
        User.email == user_data.email
    ).first()

    if not user or not verify_password(
        user_data.password,
        user.hashed_password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    token = create_access_token({
        "sub": str(user.id),
        "role": user.role
    })

    return {
        "access_token": token,
        "token_type": "bearer"
    }


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials

    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub"))
    except (jwt.InvalidTokenError, TypeError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    return user


@app.get("/auth/me", response_model=UserResponse)
def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    return current_user


@app.get("/manager/dashboard")
def manager_dashboard(
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "manager":
        raise HTTPException(
            status_code=403,
            detail="Manager access required"
        )

    return {"message": "Welcome to the Manager Dashboard"}


@app.post("/shipments", response_model=ShipmentResponse, status_code=201)
def create_shipment(
    shipment: ShipmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing_shipment = db.query(Shipment).filter(
        Shipment.shipment_number == shipment.shipment_number
    ).first()

    if existing_shipment:
        raise HTTPException(
            status_code=409,
            detail="Shipment number already exists"
        )

    new_shipment = Shipment(
        shipment_number=shipment.shipment_number,
        supplier_name=shipment.supplier_name,
        origin_country=shipment.origin_country,
        created_by=current_user.id
    )

    db.add(new_shipment)
    db.commit()
    db.refresh(new_shipment)

    create_audit_log(
        db=db,
        shipment_id=new_shipment.id,
        user_id=current_user.id,
        action="shipment_created",
        details=f"Shipment {new_shipment.shipment_number} created"
    )

    return new_shipment


@app.get("/shipments", response_model=list[ShipmentResponse])
def get_shipments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Shipment).order_by(Shipment.created_at.desc()).all()


@app.get("/shipments/{shipment_id}", response_model=ShipmentResponse)
def get_shipment(
    shipment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    shipment = db.query(Shipment).filter(
        Shipment.id == shipment_id
    ).first()

    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    return shipment


@app.patch("/shipments/{shipment_id}/status", response_model=ShipmentResponse)
def update_shipment_status(
    shipment_id: int,
    new_status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    allowed_statuses = [
        "pending_documents",
        "processing",
        "needs_review",
        "approved"
    ]

    if new_status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail="Invalid shipment status"
        )

    shipment = db.query(Shipment).filter(
        Shipment.id == shipment_id
    ).first()

    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    shipment.status = new_status
    db.commit()
    create_audit_log(
        db=db,
        shipment_id=shipment.id,
        user_id=current_user.id,
        action="status_updated",
        details=f"Shipment status changed to {new_status}"
    )
    db.refresh(shipment)

    return shipment


UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@app.post(
    "/shipments/{shipment_id}/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED
)
async def upload_document(
    shipment_id: int,
    document_type: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Validate document type
    allowed_types = [
        "invoice",
        "packing_list",
        "bill_of_lading"
    ]

    if document_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Invalid document type"
        )

    # 2. Check whether shipment exists
    shipment = db.query(Shipment).filter(
        Shipment.id == shipment_id
    ).first()

    if not shipment:
        raise HTTPException(
            status_code=404,
            detail="Shipment not found"
        )

    # 2b. Prevent duplicate document types for the same shipment
    existing_document = db.query(ShipmentDocument).filter(
        ShipmentDocument.shipment_id == shipment_id,
        ShipmentDocument.document_type == document_type
    ).first()

    if existing_document:
        raise HTTPException(
            status_code=409,
            detail=(
                f"A {document_type.replace('_', ' ')} already exists "
                f"for this shipment."
            )
        )

    # 3. Validate PDF extension
    original_filename = os.path.basename(file.filename or "")

    if not original_filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )

    # 4. Read and validate file size
    file_content = await file.read(MAX_FILE_SIZE + 1)

    if not file_content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty"
        )

    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="File size cannot exceed 10 MB"
        )

    # 5. Validate PDF file signature
    if not file_content.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=400,
            detail="Invalid PDF file"
        )

    # 6. Extract text from PDF
    try:
        with pymupdf.open(
            stream=file_content,
            filetype="pdf"
        ) as pdf:
            extracted_text = "\n".join(
                page.get_text() for page in pdf
            )

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Unable to read PDF file"
        )

    # 7. Generate a safe unique filename
    stored_filename = f"{uuid.uuid4().hex}.pdf"
    file_path = UPLOAD_DIR / stored_filename

    # 8. Save PDF securely
    try:
        with open(file_path, "wb") as saved_file:
            saved_file.write(file_content)

        # 9. Save document information in database
        document = ShipmentDocument(
            shipment_id=shipment_id,
            document_type=document_type,
            original_filename=original_filename,
            stored_filename=stored_filename,
            file_path=str(file_path),
            extracted_text=extracted_text,
            processing_status=(
                "text_extracted"
                if extracted_text.strip()
                else "ocr_required"
            ),
            uploaded_by=current_user.id
        )
        db.add(document)
        db.commit()
        db.refresh(document)

        create_audit_log(
            db=db,
            shipment_id=shipment_id,
            user_id=current_user.id,
            action="document_uploaded",
            details=f"{document_type} uploaded: {original_filename}"
        )

        return document

    except Exception:
        db.rollback()

        if file_path.exists():
            file_path.unlink()

        raise HTTPException(
            status_code=500,
            detail="Failed to save document"
        )


@app.get("/shipments/{shipment_id}/extractions")
def get_shipment_extractions(
    shipment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    shipment = db.query(Shipment).filter(
        Shipment.id == shipment_id
    ).first()

    if not shipment:
        raise HTTPException(
            status_code=404,
            detail="Shipment not found"
        )

    documents = db.query(ShipmentDocument).filter(
        ShipmentDocument.shipment_id == shipment_id
    ).order_by(ShipmentDocument.id).all()

    results = []

    for document in documents:
        extraction = extract_document(
            document.extracted_text or "",
            document.document_type
        )

        results.append({
            "document_id": document.id,
            "document_type": document.document_type,
            "filename": document.original_filename,
            "extraction": extraction
        })

    return {
        "shipment_id": shipment_id,
        "total_documents": len(results),
        "documents": results
    }


@app.delete("/shipments/{shipment_id}/documents/{document_id}")
def delete_document(
    shipment_id: int,
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    document = db.query(ShipmentDocument).filter(
        ShipmentDocument.id == document_id,
        ShipmentDocument.shipment_id == shipment_id
    ).first()

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    file_path = Path(document.file_path)
    filename = document.original_filename
    document_type = document.document_type

    create_audit_log(
        db=db,
        shipment_id=shipment_id,
        user_id=current_user.id,
        action="document_deleted",
        details=f"{document_type} deleted: {filename}"
    )

    db.delete(document)
    db.commit()

    if file_path.exists():
        file_path.unlink()

    return {
        "message": "Document deleted successfully",
        "document_id": document_id
    }


@app.get("/shipments/{shipment_id}/validation")
def validate_shipment_documents(
    shipment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    shipment = db.query(Shipment).filter(
        Shipment.id == shipment_id
    ).first()

    if not shipment:
        raise HTTPException(
            status_code=404,
            detail="Shipment not found"
        )

    documents = db.query(ShipmentDocument).filter(
        ShipmentDocument.shipment_id == shipment_id
    ).all()

    extracted_documents = []

    for document in documents:
        extraction = extract_document(
            document.extracted_text or "",
            document.document_type
        )

        fields = extraction["fields"]

        if fields["shipment_number"] != shipment.shipment_number:
            continue

        extracted_documents.append({
            "document_type": document.document_type,
            "fields": fields
        })

    validation = validate_documents(extracted_documents)

    # NEW: derive shipment status from validation results
    required_types = {"invoice", "packing_list", "bill_of_lading"}
    uploaded_types = {
        d["document_type"] for d in extracted_documents
    }
    all_documents_present = required_types.issubset(uploaded_types)

    has_failed_check = any(
        check["status"] == "fail" for check in validation["checks"]
    )

    if not all_documents_present:
        derived_status = "pending_documents"
    elif has_failed_check:
        derived_status = "needs_review"
    else:
        derived_status = "approved"

    if shipment.status != derived_status:
        shipment.status = derived_status
        db.commit()
        create_audit_log(
            db=db,
            shipment_id=shipment.id,
            user_id=current_user.id,
            action="status_updated",
            details=f"Auto-set to {derived_status} after validation"
        )

    return {
        "shipment_id": shipment.shipment_number,
        "documents_checked": len(extracted_documents),
        **validation
    }


@app.get("/shipments/{shipment_id}/export")
def export_shipment_csv(
    shipment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    shipment = db.query(Shipment).filter(
        Shipment.id == shipment_id
    ).first()

    if not shipment:
        raise HTTPException(
            status_code=404,
            detail="Shipment not found"
        )

    documents = db.query(ShipmentDocument).filter(
        ShipmentDocument.shipment_id == shipment_id
    ).all()

    extracted_documents = []

    for document in documents:
        extraction = extract_document(
            document.extracted_text or "",
            document.document_type
        )

        fields = extraction["fields"]

        if fields["shipment_number"] == shipment.shipment_number:
            extracted_documents.append({
                "document_type": document.document_type,
                "fields": fields
            })

    validation = validate_documents(extracted_documents)

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Shipment Number",
        "Supplier",
        "Origin Country",
        "Field",
        "Document",
        "Extracted Value",
        "Validation Status"
    ])

    for check in validation["checks"]:
        for item in check["values"]:
            writer.writerow([
                shipment.shipment_number,
                shipment.supplier_name,
                shipment.origin_country,
                check["label"],
                item["document_type"],
                item["value"],
                check["status"]
            ])

    from fastapi.responses import StreamingResponse

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition":
                f"attachment; filename={shipment.shipment_number}_report.csv"
        }
    )


@app.get("/shipments/{shipment_id}/audit-logs")
def get_shipment_audit_logs(
    shipment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    shipment = db.query(Shipment).filter(
        Shipment.id == shipment_id
    ).first()

    if not shipment:
        raise HTTPException(
            status_code=404,
            detail="Shipment not found"
        )

    logs = db.query(AuditLog).filter(
        AuditLog.shipment_id == shipment_id
    ).order_by(AuditLog.created_at.desc()).all()

    return [
        {
            "id": log.id,
            "user_id": log.user_id,
            "action": log.action,
            "details": log.details,
            "created_at": log.created_at
        }
        for log in logs
    ]