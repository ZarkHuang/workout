import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
from app.models import user, workout, nutrition
from app.seeds.exercises_seed import seed_exercises
from app.routers import auth, exercises, workouts, nutrition as nutrition_router, ai

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables
    Base.metadata.create_all(bind=engine)
    
    # Seed 40+ golden exercises
    db = SessionLocal()
    try:
        seed_exercises(db)
    finally:
        db.close()
    yield

app = FastAPI(
    title="FitPulse API",
    description="智慧健身訓練與營養追蹤 PWA 後端服務",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://localhost:8080",
    "http://127.0.0.1:5173",
    "https://*.vercel.app",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(exercises.router)
app.include_router(workouts.router)
app.include_router(nutrition_router.router)
app.include_router(ai.router)

from fastapi.responses import Response

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)

@app.get("/")
def root():
    return {
        "status": "healthy",
        "app": "FitPulse API",
        "version": "1.0.0",
        "docs_url": "/docs"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=settings.PORT, reload=True)
