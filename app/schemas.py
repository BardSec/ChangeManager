from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, List
from app.models import CategoryEnum, ImpactLevelEnum, UserImpactEnum, StatusEnum


class ChangeBase(BaseModel):
    """Base schema for change records."""
    # Step 1: Basics
    title: str = Field(..., min_length=1, max_length=500)
    category: CategoryEnum
    systems_affected: List[str] = Field(..., min_items=1)
    planned_start: Optional[datetime] = None
    planned_end: Optional[datetime] = None
    implementer: str = Field(..., min_length=1, max_length=255)
    
    # Step 2: Risk
    impact_level: ImpactLevelEnum
    user_impact: UserImpactEnum
    maintenance_window: bool
    backout_plan: Optional[str] = None
    
    # Step 3: Work details
    what_changed: str = Field(..., min_length=1)
    ticket_id: Optional[str] = Field(None, max_length=100)
    links: Optional[List[str]] = None
    
    # Step 4: Completion
    status: StatusEnum
    outcome_notes: Optional[str] = None
    post_change_issues: Optional[str] = None
    
    @field_validator('backout_plan')
    @classmethod
    def validate_backout_plan(cls, v, info):
        """Require backout plan for Medium/High impact changes."""
        if info.data.get('impact_level') in [ImpactLevelEnum.MEDIUM, ImpactLevelEnum.HIGH]:
            if not v or len(v.strip()) == 0:
                raise ValueError('Backout plan is required for Medium or High impact changes')
        return v
    
    @field_validator('links')
    @classmethod
    def validate_links(cls, v):
        """Validate that links are URLs."""
        if v:
            for link in v:
                if not link.startswith(('http://', 'https://')):
                    raise ValueError(f'Invalid URL: {link}')
        return v


class ChangeCreate(ChangeBase):
    """Schema for creating a change record."""
    email_copy: bool = False  # Not stored, used for email trigger
    confirm_no_secrets: bool = False


class ChangeUpdate(BaseModel):
    """Schema for updating a change record (partial updates)."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    category: Optional[CategoryEnum] = None
    systems_affected: Optional[List[str]] = None
    planned_start: Optional[datetime] = None
    planned_end: Optional[datetime] = None
    implementer: Optional[str] = Field(None, min_length=1, max_length=255)
    impact_level: Optional[ImpactLevelEnum] = None
    user_impact: Optional[UserImpactEnum] = None
    maintenance_window: Optional[bool] = None
    backout_plan: Optional[str] = None
    what_changed: Optional[str] = Field(None, min_length=1)
    ticket_id: Optional[str] = Field(None, max_length=100)
    links: Optional[List[str]] = None
    status: Optional[StatusEnum] = None
    outcome_notes: Optional[str] = None
    post_change_issues: Optional[str] = None


class ChangeResponse(ChangeBase):
    """Schema for change record response."""
    id: int
    created_by: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ChangeFilter(BaseModel):
    """Schema for filtering change records."""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    category: Optional[CategoryEnum] = None
    system: Optional[str] = None
    impact_level: Optional[ImpactLevelEnum] = None
    implementer: Optional[str] = None
    status: Optional[StatusEnum] = None
    search: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)


class AuditLogCreate(BaseModel):
    """Schema for creating audit log entries."""
    action: str
    user_email: str
    user_name: Optional[str] = None
    change_id: Optional[int] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None
