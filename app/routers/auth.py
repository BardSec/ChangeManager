from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from app.auth import oauth, generate_nonce, generate_state, extract_user_info
from app.config import get_role_config
from authlib.integrations.base_client import OAuthError

router = APIRouter(prefix="/auth", tags=["auth"])
role_config = get_role_config()


@router.get("/login")
async def login(request: Request):
    """Initiate OIDC login flow."""
    # Generate and store nonce and state
    nonce = generate_nonce()
    state = generate_state()
    
    request.session['oauth_nonce'] = nonce
    request.session['oauth_state'] = state
    
    # Redirect to Microsoft login
    redirect_uri = request.url_for('auth_callback')
    return await oauth.microsoft.authorize_redirect(
        request,
        redirect_uri,
        nonce=nonce,
        state=state
    )


@router.get("/callback")
async def auth_callback(request: Request):
    """Handle OIDC callback."""
    try:
        # Verify state parameter
        state = request.query_params.get('state')
        stored_state = request.session.get('oauth_state')
        
        if not state or state != stored_state:
            raise HTTPException(status_code=400, detail="Invalid state parameter")
        
        # Exchange authorization code for token
        token = await oauth.microsoft.authorize_access_token(request)
        
        # Verify nonce
        stored_nonce = request.session.get('oauth_nonce')
        token_nonce = token.get('userinfo', {}).get('nonce')
        
        if stored_nonce and token_nonce and stored_nonce != token_nonce:
            raise HTTPException(status_code=400, detail="Invalid nonce")
        
        # Extract user info
        user_info = extract_user_info(token.get('userinfo', {}))
        
        # Determine user role based on group membership
        group_ids = user_info.get('groups', [])
        role = role_config.get_user_role(group_ids)
        
        # Store user session
        request.session['user'] = {
            'email': user_info['email'],
            'name': user_info['name'],
            'sub': user_info['sub'],
            'role': role
        }
        
        # Clean up OAuth temporary data
        request.session.pop('oauth_nonce', None)
        request.session.pop('oauth_state', None)
        
        # Redirect to dashboard
        return RedirectResponse(url='/', status_code=302)
        
    except OAuthError as e:
        raise HTTPException(status_code=400, detail=f"OAuth error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")


@router.get("/logout")
async def logout(request: Request):
    """Logout and clear session."""
    request.session.clear()
    return RedirectResponse(url='/login', status_code=302)
