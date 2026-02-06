# ChangeLog - Quick Start Guide

## 5-Minute Setup

### 1. Prerequisites Check
```bash
# Verify Docker is installed
docker --version
docker-compose --version

# If not installed, visit: https://docs.docker.com/get-docker/
```

### 2. Get the Code
```bash
git clone <your-repo-url>
cd changelog
```

### 3. Configure Microsoft Entra ID

**Azure Portal Setup (5 minutes):**

1. Go to https://portal.azure.com → Azure Active Directory → App registrations
2. Click "New registration"
   - Name: `ChangeLog`
   - Redirect URI: `Web` → `http://localhost:8000/auth/callback`
3. After creation, note these values:
   - Application (client) ID
   - Directory (tenant) ID
4. Go to "Certificates & secrets" → New client secret → Copy the value
5. Go to "API permissions" → Add permission → Microsoft Graph → Delegated:
   - openid, email, profile, User.Read
6. Click "Grant admin consent"

### 4. Configure Environment
```bash
# Copy example environment file
cp .env.example .env

# Generate secret key
openssl rand -hex 32

# Edit .env and add your values:
nano .env
```

Required values in `.env`:
```env
SECRET_KEY=<output-from-openssl-command>
ENTRA_CLIENT_ID=<from-azure-step-3>
ENTRA_CLIENT_SECRET=<from-azure-step-4>
ENTRA_TENANT_ID=<from-azure-step-3>
REDIRECT_URI=http://localhost:8000/auth/callback
```

### 5. Start Application
```bash
docker-compose up --build
```

Wait for:
```
app_1  | INFO:     Application startup complete.
```

### 6. Access Application
Open browser to: **http://localhost:8000**

Click "Sign in with Microsoft" and log in!

## Common Issues

### "Invalid redirect_uri"
- Verify REDIRECT_URI in `.env` exactly matches Azure App registration
- No trailing slash!

### "Database connection error"
```bash
# Wait 30 seconds for database to initialize
# Or restart:
docker-compose restart app
```

### "Invalid client secret"
- Secret expired or wrong
- Create new secret in Azure Portal
- Update .env with new value
- Restart: `docker-compose restart app`

## Next Steps

1. **Configure Roles** (optional):
   - Edit `roles.yaml`
   - Add your Azure AD group Object IDs
   - See README.md for details

2. **Create Your First Change**:
   - Click "New Change"
   - Complete the 4-step wizard
   - Download PDF!

3. **Production Deployment**:
   - See README.md Production section
   - Setup HTTPS with reverse proxy
   - Update redirect URI to https://

## Useful Commands

```bash
# View logs
docker-compose logs -f app

# Stop application
docker-compose down

# Restart after config changes
docker-compose restart app

# Backup database
docker-compose exec db pg_dump -U changelog_user changelog > backup.sql

# Reset everything (⚠️ destroys data)
docker-compose down -v
```

## Getting Help

- Full documentation: See `README.md`
- Check logs: `docker-compose logs app`
- Database logs: `docker-compose logs db`

---

**Security Reminder:** Keep `.env` file secret! Never commit it to Git.
