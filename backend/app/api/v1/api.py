from fastapi import APIRouter
from backend.app.api.v1.endpoints import (
    auth,
    devices,
    languages,
    curriculum,
    lessons,
    translation,
    speech,
    classrooms,
    context,
    worksheets,
    flashcards,
    language_packs,
    models,
    sync,
    jobs
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(devices.router)
api_router.include_router(languages.router)
api_router.include_router(curriculum.router)
api_router.include_router(lessons.router)
api_router.include_router(translation.router)
api_router.include_router(speech.router)
api_router.include_router(classrooms.router)
api_router.include_router(context.router)
api_router.include_router(worksheets.router)
api_router.include_router(flashcards.router)
api_router.include_router(language_packs.router)
api_router.include_router(models.router)
api_router.include_router(sync.router)
api_router.include_router(jobs.router)
