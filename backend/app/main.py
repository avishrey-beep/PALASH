import time
import uuid
from fastapi import FastAPI, Request, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.core.config import settings
from backend.app.core.database import Base, engine
from backend.app.api.v1.api import api_router

# Ensure tables exist
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
## Jharkhand Primary Education Multilingual AI Backend Platform
Enables Hindi-medium primary school teachers to conduct mother-tongue-based education
in indigenous tribal languages (**Santhali**, **Mundari**, **Ho**).

### Core Features:
* **Layered Translation System:** Tier 1 (Phrase Cache), Tier 2 (Translation Memory), Terminology, Tier 3 (Edge Model).
* **Voice-to-Voice Pipeline:** VAD, Chunked ASR, and Speech Synthesis with measured <3s latency target.
* **Classroom Context:** Temporary teacher session management and context-aware command parsing.
* **Content Generation:** Bilingual worksheets (JSON/HTML/PDF) and visual flashcards constrained by JCERT curriculum.
* **Offline-First Synchronization:** Content-addressed delta manifests, language packs, and non-destructive conflict resolution.
* **Security & Privacy:** Role-based access control, cryptographic tokens, and zero retention of raw child speech recordings.
    """,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Observability Middleware: Request ID and Latency tracking
@app.middleware("http")
async def add_process_time_and_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.perf_counter()
    
    response = await call_next(request)
    
    process_time = (time.perf_counter() - start_time) * 1000.0
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-MS"] = f"{process_time:.2f}"
    return response

# Mount v1 API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Backward-compatibility alias routes for /api/users, /api/auth, and /api/v1/users
from backend.app.api.v1.endpoints import auth as auth_endpoint
compat_users_router = APIRouter(tags=["User Profile Compatibility"])
compat_users_router.add_api_route("/me", auth_endpoint.get_current_user_profile, methods=["GET"])
compat_users_router.add_api_route("/me", auth_endpoint.update_current_user_profile, methods=["PATCH"])

app.include_router(compat_users_router, prefix="/api/users")
app.include_router(compat_users_router, prefix=f"{settings.API_V1_STR}/users")
app.include_router(auth_endpoint.router, prefix="/api")

@app.get("/health", tags=["Health"])
def health_check():
    """Health check probe verifying platform status, environment, and version."""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "version": settings.VERSION,
        "supported_languages": settings.SUPPORTED_LANGUAGES,
        "default_target": settings.DEFAULT_TARGET_LANGUAGE
    }

@app.get("/", tags=["Root"])
def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "docs_url": f"{settings.API_V1_STR}/docs",
        "health_url": "/health"
    }
