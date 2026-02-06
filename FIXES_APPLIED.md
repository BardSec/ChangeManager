# V2 Fixes Applied

This document details all fixes applied in V2 to address issues discovered during V1 deployment.

## 1. Enum Case Conversion Fix ✅

**Problem**: SQLAlchemy was using enum `.name` (uppercase) instead of `.value` (proper case) when inserting into database.

**Example**:
- Enum defined as: `NETWORK = "Network"`  
- Form sends: `"Network"`
- Database expected: `"Network"`
- SQL Alchemy was inserting: `"NETWORK"` ❌

**Solution** (`app/models.py`):
```python
# Before
category = Column(Enum(CategoryEnum), nullable=False, index=True)

# After  
category = Column(
    Enum(CategoryEnum, values_callable=lambda obj: [e.value for e in obj]),
    nullable=False,
    index=True
)
```

Applied to: `category`, `impact_level`, `user_impact`, `status`

## 2. Cloudflare Tunnel Compatibility ✅

**Problem**: Behind Cloudflare Tunnel, app saw HTTP requests as HTTP even when users connected via HTTPS, breaking OIDC redirect URIs.

**Solution** (`app/main.py`):
```python
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

app.add_middleware(
    ProxyHeadersMiddleware,
    trusted_hosts=["*"]
)
```

This middleware trusts `X-Forwarded-Proto` headers from proxies.

## 3. Session Cookie Configuration ✅

**Problem**: Session cookies weren't persisting across OAuth redirects due to `SameSite=lax` restriction.

**Solution** (`app/main.py`):
```python
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    session_cookie=settings.session_cookie_name,
    max_age=settings.session_max_age,
    same_site='none',  # Changed from 'lax'
    https_only=True    # Changed to True for production
)
```

## 4. Clean Enum Normalization ✅

**Problem**: Form values needed normalization to handle various cases.

**Solution** (`app/routers/changes.py`):
- Added comprehensive mapping dictionaries for all enum types
- Maps handle both uppercase and correct case variations
- Normalized values used directly (bypassing Pydantic enum conversion)

```python
category_map = {
    'NETWORK': 'Network',
    'Network': 'Network',
    # ... all variations
}

# Normalize with fallback
category = category_map.get(
    raw_category.upper(),
    category_map.get(raw_category, raw_category)
)
```

## 5. Direct Value Assignment ✅

**Problem**: Pydantic was converting strings to Enum objects, which SQLAlchemy then mishandled.

**Solution** (`app/routers/changes.py`):
- Bypass Pydantic validation for enum fields
- Use normalized string values directly
- Manual field validation

```python
# Create Change object with normalized strings
change = Change(
    category=change_data['category'],  # String, not Enum
    # ...
)
```

## 6. Documentation Updates ✅

**Added**:
- Cloudflare Tunnel configuration notes
- Troubleshooting section for common issues
- Clear enum fix documentation
- Production deployment best practices

## Testing Performed

- ✅ Change creation with all categories
- ✅ Change creation with all impact levels
- ✅ Change creation with all statuses
- ✅ PDF export
- ✅ Dashboard filters
- ✅ Azure AD authentication flow
- ✅ Cloudflare Tunnel deployment
- ✅ Session persistence

## Files Modified

1. `app/models.py` - Enum column definitions
2. `app/main.py` - Middleware configuration
3. `app/routers/changes.py` - Form handling and validation
4. `README.md` - Complete rewrite with fixes documented
5. `CHANGELOG.md` - Version history

## Upgrade Path from V1

**Recommended**: Fresh deployment of V2

1. Backup V1 database:
   ```bash
   docker-compose exec db pg_dump -U changelog_user changelog > v1_backup.sql
   ```

2. Deploy V2:
   ```bash
   cd changelog-v2
   cp .env.example .env
   # Configure .env
   docker-compose up -d
   ```

3. (Optional) Migrate data:
   ```bash
   docker-compose exec -T db psql -U changelog_user changelog < v1_backup.sql
   ```

## Known Working Configurations

- Docker Compose + Cloudflare Tunnel + Azure AD ✅
- Docker Compose + Nginx + Let's Encrypt + Azure AD ✅
- Localhost development + Azure AD ✅

---

**All fixes tested and verified on production deployment**
