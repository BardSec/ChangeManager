from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import Optional
from datetime import datetime
import json

from app.database import get_db
from app.models import Change
from app.schemas import ChangeCreate, ChangeFilter
from app.auth import get_current_user, require_write_access, require_admin
from app.services import AuditService, PDFGenerator, EmailService, SecretDetector

router = APIRouter(tags=["changes"])
templates = Jinja2Templates(directory="app/templates")


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request."""
    forwarded = request.headers.get('X-Forwarded-For')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.client.host if request.client else 'unknown'


@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
    category: Optional[str] = None,
    system: Optional[str] = None,
    impact_level: Optional[str] = None,
    implementer: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = 1
):
    """Display dashboard with filterable list of changes."""
    # Build query
    query = db.query(Change)
    
    # Apply filters
    if category:
        query = query.filter(Change.category == category)
    
    if system:
        query = query.filter(Change.systems_affected.contains(system))
    
    if impact_level:
        query = query.filter(Change.impact_level == impact_level)
    
    if implementer:
        query = query.filter(Change.implementer.ilike(f'%{implementer}%'))
    
    if status:
        query = query.filter(Change.status == status)
    
    if search:
        search_term = f'%{search}%'
        query = query.filter(
            or_(
                Change.title.ilike(search_term),
                Change.what_changed.ilike(search_term),
                Change.ticket_id.ilike(search_term)
            )
        )
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
            query = query.filter(Change.created_at >= start_dt)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
            query = query.filter(Change.created_at <= end_dt)
        except ValueError:
            pass
    
    # Order by created_at descending
    query = query.order_by(Change.created_at.desc())
    
    # Pagination
    page_size = 50
    total = query.count()
    total_pages = (total + page_size - 1) // page_size
    offset = (page - 1) * page_size
    
    changes = query.offset(offset).limit(page_size).all()
    
    # Parse JSON fields for display
    for change in changes:
        change.systems_list = json.loads(change.systems_affected)
        if change.links:
            change.links_list = json.loads(change.links)
        else:
            change.links_list = []
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "changes": changes,
        "filters": {
            "category": category,
            "system": system,
            "impact_level": impact_level,
            "implementer": implementer,
            "status": status,
            "search": search,
            "start_date": start_date,
            "end_date": end_date
        },
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "email_enabled": EmailService.is_enabled()
    })


@router.get("/changes/new", response_class=HTMLResponse)
async def new_change_wizard(
    request: Request,
    user: dict = Depends(require_write_access)
):
    """Display multi-step change wizard."""
    return templates.TemplateResponse("change_wizard.html", {
        "request": request,
        "user": user,
        "default_implementer": user.get('email', ''),
        "email_enabled": EmailService.is_enabled()
    })


@router.post("/changes")
async def create_change(
    request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(require_write_access)
):
    """Create a new change record."""
    # Parse form data
    form_data = await request.form()
    
    # Build change data with explicit enum normalization
    # Maps handle both uppercase and correct case variations
    category_map = {
        'NETWORK': 'Network',
        'IDENTITY': 'Identity', 
        'ENDPOINT': 'Endpoint',
        'APPLICATION': 'Application',
        'VENDOR': 'Vendor',
        'OTHER': 'Other',
        'Network': 'Network',
        'Identity': 'Identity',
        'Endpoint': 'Endpoint',
        'Application': 'Application',
        'Vendor': 'Vendor',
        'Other': 'Other'
    }
    
    impact_map = {
        'LOW': 'Low',
        'MEDIUM': 'Medium',
        'HIGH': 'High',
        'Low': 'Low',
        'Medium': 'Medium',
        'High': 'High'
    }
    
    user_impact_map = {
        'NONE': 'None',
        'SOME': 'Some',
        'MANY': 'Many',
        'None': 'None',
        'Some': 'Some',
        'Many': 'Many'
    }
    
    status_map = {
        'PLANNED': 'Planned',
        'IN PROGRESS': 'In Progress',
        'COMPLETED': 'Completed',
        'ROLLED BACK': 'Rolled Back',
        'FAILED': 'Failed',
        'Planned': 'Planned',
        'In Progress': 'In Progress',
        'Completed': 'Completed',
        'Rolled Back': 'Rolled Back',
        'Failed': 'Failed'
    }
    
    # Get raw values from form
    raw_category = form_data.get('category', '')
    raw_impact = form_data.get('impact_level', '')
    raw_user_impact = form_data.get('user_impact', '')
    raw_status = form_data.get('status', '')
    
    # Normalize - try uppercase first, then use as-is as fallback
    category = category_map.get(raw_category.upper(), category_map.get(raw_category, raw_category))
    impact_level = impact_map.get(raw_impact.upper(), impact_map.get(raw_impact, raw_impact))
    user_impact = user_impact_map.get(raw_user_impact.upper(), user_impact_map.get(raw_user_impact, raw_user_impact))
    status = status_map.get(raw_status.upper(), status_map.get(raw_status, raw_status))
    
    change_data = {
        'title': form_data.get('title'),
        'category': category,
        'systems_affected': form_data.getlist('systems_affected'),
        'planned_start': form_data.get('planned_start') or None,
        'planned_end': form_data.get('planned_end') or None,
        'implementer': form_data.get('implementer'),
        'impact_level': impact_level,
        'user_impact': user_impact,
        'maintenance_window': form_data.get('maintenance_window') == 'true',
        'backout_plan': form_data.get('backout_plan') or None,
        'what_changed': form_data.get('what_changed'),
        'ticket_id': form_data.get('ticket_id') or None,
        'links': [link for link in form_data.getlist('links') if link],
        'status': status,
        'outcome_notes': form_data.get('outcome_notes') or None,
        'post_change_issues': form_data.get('post_change_issues') or None,
    }
   
    email_copy = form_data.get('email_copy') == 'true'
    confirm_no_secrets = form_data.get('confirm_no_secrets') == 'true'
    
    # Secret detection
    has_secrets, findings = SecretDetector.has_secrets(change_data)
    if has_secrets and not confirm_no_secrets:
        # Return error with findings
        findings_text = ', '.join([f"{name}: {preview}" for name, preview in findings])
        raise HTTPException(
            status_code=400,
            detail=f"Potential secrets detected: {findings_text}. Please confirm no secrets checkbox to proceed."
        )
    
    # Manual validation (bypassing Pydantic to avoid enum conversion issues)
    if not change_data.get('title'):
        raise HTTPException(status_code=400, detail="Title is required")
    if not change_data.get('category'):
        raise HTTPException(status_code=400, detail="Category is required")
    if not change_data.get('systems_affected'):
        raise HTTPException(status_code=400, detail="At least one system is required")
    if not change_data.get('implementer'):
        raise HTTPException(status_code=400, detail="Implementer is required")
    if not change_data.get('impact_level'):
        raise HTTPException(status_code=400, detail="Impact level is required")
    if not change_data.get('user_impact'):
        raise HTTPException(status_code=400, detail="User impact is required")
    if not change_data.get('what_changed'):
        raise HTTPException(status_code=400, detail="What changed is required")
    if not change_data.get('status'):
        raise HTTPException(status_code=400, detail="Status is required")
    
    # Validate backout plan for Medium/High impact
    if change_data.get('impact_level') in ['Medium', 'High']:
        if not change_data.get('backout_plan') or not change_data.get('backout_plan').strip():
            raise HTTPException(status_code=400, detail="Backout plan is required for Medium or High impact changes")
    
    # Create change record directly with normalized values
    change = Change(
        title=change_data['title'],
        category=change_data['category'],
        systems_affected=json.dumps(change_data['systems_affected']),
        planned_start=change_data.get('planned_start'),
        planned_end=change_data.get('planned_end'),
        implementer=change_data['implementer'],
        impact_level=change_data['impact_level'],
        user_impact=change_data['user_impact'],
        maintenance_window=change_data['maintenance_window'],
        backout_plan=change_data.get('backout_plan'),
        what_changed=change_data['what_changed'],
        ticket_id=change_data.get('ticket_id'),
        links=json.dumps(change_data['links']) if change_data.get('links') else None,
        status=change_data['status'],
        outcome_notes=change_data.get('outcome_notes'),
        post_change_issues=change_data.get('post_change_issues'),
        created_by=user.get('email', '')
    )
    
    db.add(change)
    db.commit()
    db.refresh(change)
    
    # Audit log
    AuditService.log_change_create(
        db=db,
        user=user,
        change_id=change.id,
        ip_address=get_client_ip(request)
    )
    
    # Send email if requested and enabled
    if email_copy and EmailService.is_enabled():
        change_url = str(request.url_for('view_change', change_id=change.id))
        change_dict = {
            'id': change.id,
            'title': change.title,
            'status': str(change.status),
            'category': str(change.category),
            'systems_affected': change.systems_affected,
            'impact_level': str(change.impact_level),
            'implementer': change.implementer
        }
        EmailService.send_change_summary(user.get('email', ''), change_dict, change_url)
    
    # Return the change ID
    return {"success": True, "change_id": change.id}


@router.get("/changes/{change_id}", response_class=HTMLResponse)
async def view_change(
    request: Request,
    change_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """View change detail page."""
    change = db.query(Change).filter(Change.id == change_id).first()
    
    if not change:
        raise HTTPException(status_code=404, detail="Change not found")
    
    # Parse JSON fields
    change.systems_list = json.loads(change.systems_affected)
    if change.links:
        change.links_list = json.loads(change.links)
    else:
        change.links_list = []
    
    return templates.TemplateResponse("change_detail.html", {
        "request": request,
        "user": user,
        "change": change,
        "email_enabled": EmailService.is_enabled()
    })


@router.get("/changes/{change_id}/pdf")
async def download_change_pdf(
    request: Request,
    change_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Generate and download PDF for a change record."""
    change = db.query(Change).filter(Change.id == change_id).first()
    
    if not change:
        raise HTTPException(status_code=404, detail="Change not found")
    
    # Convert to dict for PDF generation
    change_dict = {
        'id': change.id,
        'title': change.title,
        'category': change.category.value,
        'systems_affected': change.systems_affected,
        'planned_start': change.planned_start,
        'planned_end': change.planned_end,
        'implementer': change.implementer,
        'impact_level': change.impact_level.value,
        'user_impact': change.user_impact.value,
        'maintenance_window': change.maintenance_window,
        'backout_plan': change.backout_plan,
        'what_changed': change.what_changed,
        'ticket_id': change.ticket_id,
        'links': change.links,
        'status': change.status.value,
        'outcome_notes': change.outcome_notes,
        'post_change_issues': change.post_change_issues,
        'created_by': change.created_by,
        'created_at': change.created_at
    }
    
    # Generate PDF
    pdf_buffer = PDFGenerator.generate_change_pdf(change_dict)
    
    # Audit log
    AuditService.log_export(
        db=db,
        user=user,
        export_type='pdf',
        details={'change_id': change_id},
        ip_address=get_client_ip(request)
    )
    
    # Return as downloadable file
    filename = f"change_{change_id}_{datetime.now().strftime('%Y%m%d')}.pdf"
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
