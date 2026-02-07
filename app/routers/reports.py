from fastapi import APIRouter, Request, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
import csv
import io
import json

from app.database import get_db
from app.models import Change
from app.auth import require_admin
from app.services import AuditService

router = APIRouter(prefix="/reports", tags=["reports"])


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request."""
    forwarded = request.headers.get('X-Forwarded-For')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.client.host if request.client else 'unknown'


@router.get("/changes.csv")
async def export_changes_csv(
    request: Request,
    start: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end: str = Query(..., description="End date in YYYY-MM-DD format"),
    db: Session = Depends(get_db),
    user: dict = Depends(require_admin)
):
    """
    Export changes to CSV for a date range (admin only).
    
    Args:
        start: Start date (YYYY-MM-DD)
        end: End date (YYYY-MM-DD)
    """
    # Parse dates
    try:
        start_date = datetime.strptime(start, '%Y-%m-%d')
        end_date = datetime.strptime(end, '%Y-%m-%d')
        
        # Set end date to end of day
        end_date = end_date.replace(hour=23, minute=59, second=59)
        
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date format. Use YYYY-MM-DD"
        )
    
    if start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="Start date must be before end date"
        )
    
    # Query changes in date range
    changes = db.query(Change).filter(
        Change.created_at >= start_date,
        Change.created_at <= end_date
    ).order_by(Change.created_at).all()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'ID',
        'Created At',
        'Created By',
        'Updated At',
        'Title',
        'Category',
        'Systems Affected',
        'Planned Start',
        'Planned End',
        'Implementer',
        'Impact Level',
        'User Impact',
        'Maintenance Window',
        'Backout Plan',
        'What Changed',
        'Ticket/Issue ID',
        'Links',
        'Status',
        'Outcome Notes',
        'Post-Change Issues'
    ])
    
    # Write data rows
    for change in changes:
        # Parse JSON fields
        systems = ', '.join(json.loads(change.systems_affected))
        links = ', '.join(json.loads(change.links)) if change.links else ''
        
        writer.writerow([
            change.id,
            change.created_at.strftime('%Y-%m-%d %H:%M:%S') if change.created_at else '',
            change.created_by,
            change.updated_at.strftime('%Y-%m-%d %H:%M:%S') if change.updated_at else '',
            change.title,
            change.category.value,
            systems,
            change.planned_start.strftime('%Y-%m-%d %H:%M:%S') if change.planned_start else '',
            change.planned_end.strftime('%Y-%m-%d %H:%M:%S') if change.planned_end else '',
            change.implementer,
            change.impact_level.value,
            change.user_impact.value,
            'Yes' if change.maintenance_window else 'No',
            change.backout_plan or '',
            change.what_changed,
            change.ticket_id or '',
            links,
            change.status.value,
            change.outcome_notes or '',
            change.post_change_issues or ''
        ])
    
    # Audit log
    AuditService.log_export(
        db=db,
        user=user,
        export_type='csv',
        details={
            'start_date': start,
            'end_date': end,
            'record_count': len(changes)
        },
        ip_address=get_client_ip(request)
    )
    
    # Prepare response
    output.seek(0)
    filename = f"changekeeper_export_{start}_to_{end}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
