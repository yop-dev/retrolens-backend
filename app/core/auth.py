"""Authentication module for Clerk integration."""

from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
import jwt
from jwt import PyJWKClient
from app.core.config import settings

# Bearer token scheme
bearer_scheme = HTTPBearer()

# Clerk JWKS endpoint
CLERK_JWKS_URL = f"https://{settings.CLERK_DOMAIN}/.well-known/jwks.json" if hasattr(settings, 'CLERK_DOMAIN') else None


class ClerkAuth:
    """Clerk authentication handler."""
    
    def __init__(self):
        """Initialize Clerk auth with JWKS client."""
        if CLERK_JWKS_URL:
            self.jwks_client = PyJWKClient(CLERK_JWKS_URL)
        else:
            self.jwks_client = None
    
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify a Clerk JWT token."""
        if not self.jwks_client:
            # If Clerk is not configured, return a mock user for development
            return {
                "sub": "dev_user_123",
                "email": "dev@example.com",
                "name": "Development User"
            }
        
        try:
            # Get the signing key from JWKS
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)
            
            # Decode and verify the token with time tolerance for clock skew
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=settings.CLERK_AUDIENCE if hasattr(settings, 'CLERK_AUDIENCE') else None,
                options={"verify_aud": False},  # Skip audience verification if not set
                leeway=60  # Allow 60 seconds of clock skew tolerance
            )
            
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token verification failed: {str(e)}"
            )


# Create a singleton instance
clerk_auth = ClerkAuth()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> Dict[str, Any]:
    """Get the current authenticated user from the token."""
    token = credentials.credentials
    user_data = await clerk_auth.verify_token(token)
    return user_data


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[Dict[str, Any]]:
    """Get the current user if authenticated, otherwise return None."""
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        user_data = await clerk_auth.verify_token(token)
        return user_data
    except HTTPException:
        return None


async def require_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Require an authenticated user."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return current_user
