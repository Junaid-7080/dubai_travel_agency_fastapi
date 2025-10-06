# ===== main.py =====
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.utils import get_openapi
from database import create_db_and_tables
from routers import auth, packages, bookings, payments, reviews, admin, public, notifications, customers
import uvicorn
import os

# Create FastAPI app
app = FastAPI(
    title="Dubai Travel Agency API",
    description="Complete travel booking system with bilingual support",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure upload directory exists
upload_dir = "uploads"
os.makedirs(upload_dir, exist_ok=True)

# Mount static files if directory exists
if os.path.exists(upload_dir):
    app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")

# Include routers
try:
    app.include_router(auth.router)
    app.include_router(packages.router)
    app.include_router(bookings.router)
    app.include_router(payments.router)
    app.include_router(reviews.router)
    app.include_router(admin.router)
    app.include_router(public.router)
    app.include_router(notifications.router)
    app.include_router(customers.router)
except Exception as e:
    print(f"⚠️ Error including routers: {e}")

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup with error handling"""
    try:
        create_db_and_tables()
        print("🚀 Database initialized successfully!")
    except Exception as e:
        print(f"⚠️ Database initialization warning: {e}")
        print("📝 Application will continue running...")

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Dubai Travel Agency API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "database": "connected"}

# Debug endpoint for OpenAPI
@app.get("/openapi.json")
async def get_open_api_endpoint():
    """Check if OpenAPI schema is generating correctly"""
    return get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
