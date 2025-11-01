from sqlalchemy.orm import Session
from . import models, schemas
from sqlalchemy import func
# Removed: from sqlalchemy import Column, String, Integer (since they are unused here)
import hashlib
# Removed: from sqlalchemy.orm import Session (duplicate)
# Removed: from . import models (duplicate)
# Removed: class Admin(Base): ... (The conflicting model definition)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def create_user(db: Session, username: str, password: str, role: str):
    hashed = hash_password(password)
    user = models.User(username=username, password=hashed, role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def authenticate_user(db: Session, username: str, password: str):
    hashed = hash_password(password)
    user = db.query(models.User).filter_by(username=username, password=hashed).first()
    return user

def create_admin(db: Session, username: str, password: str):
    """A new function to create an admin, perhaps for initial setup."""
    hashed = hash_password(password)
    admin = models.Admin(username=username, password=hashed)
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin

# --- Report CRUD functions (No changes needed) ---

def create_report(db: Session, report_in: schemas.ReportCreate):
    db_report = models.Report(
        station_name=report_in.station_name,
        station_city=report_in.station_city,
        issue_category=report_in.issue_category,
        description=report_in.description,
        photo_url=report_in.photo_url,
        urgency_level=report_in.urgency_level.value if report_in.urgency_level else "Medium",
        status=report_in.status.value if report_in.status else "Submitted",
        inspector_notes=report_in.inspector_notes,
        reporter_contact=report_in.reporter_contact,
        latitude=report_in.latitude,
        longitude=report_in.longitude,
        created_by=report_in.created_by
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report

def get_report(db: Session, report_id: str):
    return db.query(models.Report).filter(models.Report.id == report_id).first()

def list_reports(db: Session, skip: int = 0, limit: int = 100, filters: dict = None, sort: str = None):
    q = db.query(models.Report)
    if filters:
        if filters.get("status"):
            q = q.filter(models.Report.status == filters["status"])
        if filters.get("urgency"):
            q = q.filter(models.Report.urgency_level == filters["urgency"])
        if filters.get("city"):
            q = q.filter(models.Report.station_city == filters["city"])
        if filters.get("search"):
            s = f"%{filters['search'].lower()}%"
            q = q.filter(func.lower(models.Report.station_name).like(s) |
                         func.lower(models.Report.description).like(s) |
                         func.lower(models.Report.issue_category).like(s))
    # Sorting
    if sort:
        if sort.startswith("-"):
            col_name = sort[1:]
            col = getattr(models.Report, col_name, models.Report.created_date)
            q = q.order_by(col.desc())
        else:
            col = getattr(models.Report, sort, models.Report.created_date)
            q = q.order_by(col.asc())
    else:
        q = q.order_by(models.Report.created_date.desc())
    return q.offset(skip).limit(limit).all()

def update_report(db: Session, report_id: str, data: dict):
    r = db.query(models.Report).filter(models.Report.id == report_id).first()
    if not r:
        return None
    for k, v in data.items():
        if hasattr(r, k) and v is not None:
            setattr(r, k, v)
    db.commit()
    db.refresh(r)
    return r

def stats(db: Session):
    total = db.query(func.count(models.Report.id)).scalar() or 0
    by_status = dict(db.query(models.Report.status, func.count(models.Report.id)).group_by(models.Report.status).all()) or {}
    by_urgency = dict(db.query(models.Report.urgency_level, func.count(models.Report.id)).group_by(models.Report.urgency_level).all()) or {}
    by_category = dict(db.query(models.Report.issue_category, func.count(models.Report.id)).group_by(models.Report.issue_category).all()) or {}
    by_city = dict(db.query(models.Report.station_city, func.count(models.Report.id)).group_by(models.Report.station_city).all()) or {}
    top_stations_q = db.query(models.Report.station_name, models.Report.station_city, func.count(models.Report.id).label("cnt")) \
        .group_by(models.Report.station_name, models.Report.station_city) \
        .order_by(func.count(models.Report.id).desc()) \
        .limit(10).all()
    top_stations = [{"station": f"{row.station_name} ({row.station_city})", "count": row.cnt} for row in top_stations_q]

    return {
        "total": total,
        "by_status": by_status,
        "by_urgency": by_urgency,
        "by_category": by_category,
        "by_city": by_city,
        "top_stations": top_stations
    }