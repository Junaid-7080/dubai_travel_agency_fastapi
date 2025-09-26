#!/usr/bin/env python3
"""
Dubai Travel Agency FastAPI Application
Run this script to start the development server
"""

import uvicorn
from main import app
from seed_data import create_sample_data

if __name__ == "__main__":
    print("🏜️ Starting Dubai Travel Agency API...")
    print("📊 Creating sample data...")
    create_sample_data()
    print("✅ Sample data created successfully!")
    print("🚀 Starting server on http://localhost:8000")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("📚 ReDoc Documentation: http://localhost:8000/redoc")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
