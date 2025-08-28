"""Main FastAPI application."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.config import settings
from app.api.api_v1.api import api_router


# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    redirect_slashes=False,  # Disable to prevent HTTPS->HTTP redirect issues with proxies
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to RetroLens API",
        "version": settings.VERSION,
        "docs": f"{settings.API_V1_STR}/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": settings.VERSION}


@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    print("\n" + "="*50)
    print("🚀 RetroLens API Starting...")
    print("="*50)
    print(f"Version: {settings.VERSION}")
    print(f"Debug: {settings.DEBUG}")
    print(f"CORS Origins: {settings.BACKEND_CORS_ORIGINS}")
    print(f"API Docs: {settings.API_V1_STR}/docs")
    print(f"Supabase URL: {settings.SUPABASE_URL}")
    print(f"Clerk Domain: {settings.CLERK_DOMAIN or 'Not configured'}")
    
    # Test Supabase connection (lazy - won't fail startup)
    try:
        from app.db.supabase import get_supabase_client
        client = get_supabase_client()
        print("✅ Supabase connection successful")
    except Exception as e:
        print(f"⚠️  Supabase connection failed: {e}")
        print("   API will continue but database operations may fail")
    
    print("="*50 + "\n")


# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


# Exception handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors."""
    return JSONResponse(
        status_code=404,
        content={"detail": "Resource not found"}
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle 500 errors."""
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
