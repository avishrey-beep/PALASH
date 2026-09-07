from backend.app.core.database import Base
from backend.app.models.user import User, Role, AuditLog, user_roles
from backend.app.models.device import Device, DeviceSyncLog
from backend.app.models.curriculum import Language, Curriculum, CurriculumVersion, Lesson, LessonVersion
from backend.app.models.translation import Phrase, TranslationMemoryItem, GlossaryTerm, ReviewTask, ReviewDecision
from backend.app.models.classroom import ClassroomSession, ContextItem, AudioUtterance
from backend.app.models.content import Worksheet, WorksheetQuestion, Flashcard, AudioAsset
from backend.app.models.pack import LanguagePack, SyncManifest
from backend.app.models.job import BackgroundJob
from backend.app.models.model_registry import AIModelEntry

__all__ = [
    "Base",
    "User",
    "Role",
    "AuditLog",
    "user_roles",
    "Device",
    "DeviceSyncLog",
    "Language",
    "Curriculum",
    "CurriculumVersion",
    "Lesson",
    "LessonVersion",
    "Phrase",
    "TranslationMemoryItem",
    "GlossaryTerm",
    "ReviewTask",
    "ReviewDecision",
    "ClassroomSession",
    "ContextItem",
    "AudioUtterance",
    "Worksheet",
    "WorksheetQuestion",
    "Flashcard",
    "AudioAsset",
    "LanguagePack",
    "SyncManifest",
    "BackgroundJob",
    "AIModelEntry"
]
