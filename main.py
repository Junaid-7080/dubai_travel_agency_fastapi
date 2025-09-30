# ===== main.py =====
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database import create_db_and_tables
from routers import auth, packages, bookings, payments, reviews, admin, public
import uvicorn

# Create FastAPI app
app = FastAPI(
    title="Dubai Travel Agency API",
    description="Complete travel booking system with bilingual support",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


@app.get("/health")
async def health_check():
    """Health check endpoint for Render"""
    return {
        "status": "healthy",
        "service": "dubai-travel-agency"
    }

@app.get("/")
async def root():
    return {"message": "Dubai Travel Agency API"}

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include routers
app.include_router(auth.router)
app.include_router(packages.router)
app.include_router(bookings.router)
app.include_router(payments.router)
app.include_router(reviews.router)
app.include_router(admin.router)
app.include_router(public.router)

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    create_db_and_tables()

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Dubai Travel Agency API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
