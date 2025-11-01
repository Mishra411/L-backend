from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import Optional
from . import models, schemas, crud
from .database import engine
from .deps import get_db
from .utils import save_upload_file_local
import os
import openai
from fastapi import Body



# Initialize DB
models.Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI(title="LRT Accessibility Reporter API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Uploads
uploads_dir = os.path.join(os.path.dirname(__file__), "uploads")
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

# OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

async def analyze_ai(text: str) -> str:
    if not openai.api_key:
        return "AI key not set"
    resp = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": f"Analyze this report: {text}"}]
    )
    return resp.choices[0].message.content

# Endpoints
@app.post("/reports", response_model=schemas.ReportOut)
async def create_report(
    station_name: str = Form(...),
    station_city: str = Form(...),
    issue_category: str = Form(...),
    description: str = Form(...),
    urgency_level: str = Form("Medium"),
    reporter_contact: Optional[str] = Form(None),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    created_by: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    photo_url = None
    if file:
        if file.content_type and not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Uploaded file must be an image")
        photo_url = save_upload_file_local(file)

    report_in = schemas.ReportCreate(
        station_name=station_name,
        station_city=station_city,
        issue_category=issue_category,
        description=description,
        photo_url=photo_url,
        urgency_level=schemas.UrgencyLevel(urgency_level),
        reporter_contact=reporter_contact,
        latitude=latitude,
        longitude=longitude,
        created_by=created_by
    )
    r = crud.create_report(db, report_in)

    # AI Analysis
    r.ai_analysis = await analyze_ai(report_in.description)
    db.commit()
    db.refresh(r)

    return r

@app.get("/reports", response_model=list[schemas.ReportOut])
def list_reports(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    urgency: Optional[str] = None,
    city: Optional[str] = None,
    search: Optional[str] = None,
    sort: Optional[str] = "-created_date",
    db: Session = Depends(get_db)
):
    filters = {}
    if status:
        filters["status"] = status
    if urgency:
        filters["urgency"] = urgency
    if city:
        filters["city"] = city
    if search:
        filters["search"] = search
    results = crud.list_reports(db, skip=skip, limit=limit, filters=filters, sort=sort)
    return results

@app.get("/reports/{report_id}", response_model=schemas.ReportOut)
def get_report(report_id: str, db: Session = Depends(get_db)):
    r = crud.get_report(db, report_id)
    if not r:
        raise HTTPException(status_code=404, detail="Report not found")
    return r

@app.patch("/reports/{report_id}", response_model=schemas.ReportOut)
def patch_report(report_id: str, payload: schemas.ReportUpdate, db: Session = Depends(get_db)):
    data = payload.dict(exclude_unset=True)
    r = crud.update_report(db, report_id, data)
    if not r:
        raise HTTPException(status_code=404, detail="Report not found")
    return r

@app.get("/reports/stats", response_model=schemas.StatsOut)
def get_stats(db: Session = Depends(get_db)):
    return crud.stats(db)

# Optional AI-only endpoint
@app.post("/ai/analyze")
async def ai_analyze(description: str = Form(...)):
    result = await analyze_ai(description)
    return {"ai_analysis": result}

@app.post("/auth/register", response_model=schemas.UserOut)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    return crud.create_user(db, user.username, user.password, user.role)

@app.post("/auth/login", response_model=schemas.UserOut)
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = crud.authenticate_user(db, user.username, user.password)
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return db_user

@app.post("/auth/admin/login")
def login_admin_endpoint(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    # REMOVED: from .models import Admin (using models.Admin instead)
    # The Admin model is now correctly accessed via the top-level 'models' import
    admin = db.query(models.Admin).filter(models.Admin.username == username).first()
    if not admin or not admin.verify_password(password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"message": f"Welcome, {username}!"}