
# CargoLens AI


## Frontend
```powershell
cd frontend
npm install
npm run dev
```

## Backend
```powershell
cd backend
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
pip install fastapi uvicorn sqlalchemy python-multipart python-dotenv
uvicorn main:app --reload
```

The Python virtual environment (`venv/`) is intentionally not included in this ZIP.
Create it locally using the commands above.
