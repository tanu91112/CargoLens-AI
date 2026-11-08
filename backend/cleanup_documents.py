
from pathlib import Path

from database import SessionLocal
from models import Shipment, ShipmentDocument

db = SessionLocal()

try:
    shipment = db.query(Shipment).filter(
        Shipment.shipment_number == "SHP-24811"
    ).first()

    if not shipment:
        raise Exception("SHP-24811 not found.")

    documents = db.query(ShipmentDocument).filter(
        ShipmentDocument.shipment_id == shipment.id
    ).order_by(ShipmentDocument.id).all()

    # Keep only the first correctly classified copy of each document.
    required = {
        "invoice": "SHP-24811_Invoice.pdf",
        "packing_list": "SHP-24811_Packing_List.pdf",
        "bill_of_lading": "SHP-24811_Bill_of_Lading.pdf"
    }

    keep_ids = {}

    for doc_type, filename in required.items():
        matching = [
            doc for doc in documents
            if doc.document_type == doc_type
            and doc.original_filename == filename
        ]

        if not matching:
            raise Exception(f"Required document missing: {filename}")

        keep_ids[doc_type] = matching[0].id

    to_delete = [
        doc for doc in documents
        if doc.id not in keep_ids.values()
    ]

    print("Documents to KEEP:")
    for doc_type, doc_id in keep_ids.items():
        print(f"{doc_type}: document ID {doc_id}")

    print("\nDocuments to REMOVE:")
    for doc in to_delete:
        print(f"ID {doc.id}: {doc.original_filename} ({doc.document_type})")

    # Remove unwanted database records.
    for doc in to_delete:
        db.delete(doc)

    db.commit()

    # Remove their associated stored PDF files.
    for doc in to_delete:
        path = Path(doc.file_path)
        if path.exists():
            path.unlink()

    print("\nCleanup completed successfully.")

except Exception as error:
    db.rollback()
    print("Cleanup stopped:", error)

finally:
    db.close()
