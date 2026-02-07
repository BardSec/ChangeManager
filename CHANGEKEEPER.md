# Changekeeper

## Version 2.0.0 - Production Ready (2026-02-04)

### 🎉 Major Improvements

**Fixed Issues from V1:**
- ✅ Enum case conversion bug (SQLAlchemy using `.name` instead of `.value`)
- ✅ Cloudflare Tunnel compatibility (proxy header handling)
- ✅ Session state management for OIDC flows
- ✅ Azure AD redirect URI validation

**Code Quality:**
- ✅ Removed all debug code and commented sections
- ✅ Clean, production-ready codebase
- ✅ Comprehensive documentation
- ✅ Optimized for immediate deployment

### 🔧 Technical Changes

**Models (`app/models.py`):**
- Added `values_callable` to all Enum columns to use `.value` instead of `.name`
- Ensures database receives correct case (e.g., "Network" not "NETWORK")

**Main App (`app/main.py`):**
- Added `ProxyHeadersMiddleware` for Cloudflare Tunnel compatibility
- Configured session middleware with `same_site='none'` and `https_only=True`
- Proper X-Forwarded-Proto header handling

**Changes Router (`app/routers/changes.py`):**
- Clean enum normalization with fallback maps
- Manual validation bypassing Pydantic enum conversion
- Direct use of normalized string values for database insertion

**Documentation:**
- Complete setup guide with Cloudflare Tunnel instructions
- Troubleshooting section for common issues
- Production deployment best practices

### 📦 What's Included

- Complete source code (40+ files)
- Docker deployment configuration
- Database migrations
- Comprehensive documentation
- Test suite foundation
- Configuration templates

### 🚀 Deployment

```bash
# Extract and deploy
unzip changekeeper-v2.zip
cd changekeeper-v2
cp .env.example .env
# Edit .env with your Azure AD credentials
docker-compose up -d
```

### ⚠️ Breaking Changes from V1

None - this is a clean rebuild with same functionality + fixes

### 🎯 Tested Environments

- ✅ Docker Compose (development)
- ✅ Docker Compose (production)
- ✅ Cloudflare Tunnel
- ✅ Nginx reverse proxy
- ✅ Azure AD authentication
- ✅ PostgreSQL 15

---

**Upgrade from V1**: Start fresh with V2 for cleanest experience
