# TDD – CargoLens-AI

## 1. Project Overview

CargoLens-AI is a shipment document processing and validation system. It allows users to manage shipments, upload documents, extract information, validate extracted fields, and export results as CSV files.

## 2. Testing Objectives

The main objectives are to:

- Verify user registration and login.
- Check role-based access for managers and executives.
- Verify shipment creation and retrieval.
- Validate PDF document uploads.
- Check data extraction from uploaded documents.
- Identify mismatches between shipment documents.
- Verify duplicate document prevention.
- Check CSV export functionality.
- Verify audit log functionality.

## 3. Testing Approach

The project uses the following testing approaches:

- **Functional Testing:** Verify that each feature works as expected.
- **API Testing:** Test backend endpoints using FastAPI Swagger UI.
- **Validation Testing:** Check extracted information across multiple documents.
- **Negative Testing:** Test invalid inputs, unsupported files, and duplicate uploads.
- **Integration Testing:** Verify that frontend and backend features work together.

## 4. Test Cases

| Test ID | Feature | Test Scenario | Expected Result |
|---|---|---|---|
| TC-01 | Registration | Register with valid details | User account is created |
| TC-02 | Login | Login with valid credentials | Authentication succeeds |
| TC-03 | Login | Login with invalid credentials | Error message is returned |
| TC-04 | Role Access | Access manager dashboard with manager account | Dashboard is accessible |
| TC-05 | Shipment | Create a shipment with valid details | Shipment is created |
| TC-06 | Shipment | Retrieve shipment details | Correct shipment details are displayed |
| TC-07 | Document Upload | Upload a valid PDF | Document is uploaded |
| TC-08 | Document Upload | Upload an unsupported file | Upload is rejected |
| TC-09 | Document Upload | Upload a duplicate document type | Duplicate upload is rejected |
| TC-10 | Extraction | Extract information from a text-based PDF | Available fields are extracted |
| TC-11 | Validation | Compare fields across three documents | Matching and mismatching fields are identified |
| TC-12 | CSV Export | Export shipment extraction data | CSV file is downloaded |
| TC-13 | Audit Logs | Perform a shipment-related action | Corresponding activity is logged |
| TC-14 | Document Delete | Delete an uploaded document | Document is removed |

## 5. Validation Scenarios

A sample shipment, SHP-24811, is used for cross-document validation.

The sample documents contain the following gross weight values:

| Document | Gross Weight |
|---|---:|
| Invoice | 3120 kg |
| Packing List | 3165 kg |
| Bill of Lading | 3120 kg |

**Expected Result:** The system should identify the gross-weight mismatch and flag it for review.

## 6. Test Environment

- Operating System: Windows
- Backend: Python, FastAPI
- Database: SQLite
- Frontend: React and Vite
- API Testing: FastAPI Swagger UI
- Document Processing: PyMuPDF

## 7. Test Execution Record

Record the actual result after running each test.

| Test ID | Actual Result | Status |
|---|---|---|
| TC-01 to TC-14 | To be recorded during final verification | Pending |

## 8. Known Limitations

- OCR for scanned PDF documents is not implemented.
- Data extraction currently uses rule-based and regex-based logic.
- Extraction confidence values are heuristic.
- SQLite is used for local development.

## 9. Conclusion

This test document defines the functional, API, validation, and integration scenarios for CargoLens-AI. These tests help verify the correctness of shipment management, document processing, validation, and export features.