from sqlalchemy import Column, String, Integer, Text, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from backend.app.core.database import Base
from backend.app.models.base import TimestampMixin, generate_uuid

class Language(Base, TimestampMixin):
    __tablename__ = "languages"

    code = Column(String(10), primary_key=True)  # ISO 639-3: hin, sat, unr, hoc
    name = Column(String(100), nullable=False)
    native_name = Column(String(100), nullable=False)
    default_script = Column(String(50), nullable=False)  # Devanagari, Ol Chiki, Warang Chiti, Latin
    is_active = Column(Boolean, default=True)

class Curriculum(Base, TimestampMixin):
    __tablename__ = "curricula"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(200), nullable=False)
    state = Column(String(100), default="Jharkhand", nullable=False)
    board = Column(String(100), default="JCERT", nullable=False)
    class_grade = Column(Integer, nullable=False)  # 1, 2, 3
    subject = Column(String(100), nullable=False)  # Mathematics, Hindi, EVS
    medium = Column(String(50), default="Hindi", nullable=False)
    current_version = Column(Integer, default=1, nullable=False)
    description = Column(Text, nullable=True)

    versions = relationship("CurriculumVersion", back_populates="curriculum", cascade="all, delete-orphan")
    lessons = relationship("Lesson", back_populates="curriculum", cascade="all, delete-orphan")

class CurriculumVersion(Base, TimestampMixin):
    __tablename__ = "curriculum_versions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    curriculum_id = Column(String(36), ForeignKey("curricula.id", ondelete="CASCADE"), nullable=False)
    version_number = Column(Integer, nullable=False)
    checksum = Column(String(64), nullable=False)  # SHA-256
    source_file_path = Column(String(500), nullable=True)
    status = Column(String(50), default="DRAFT", nullable=False)  # DRAFT, PROCESSING, REVIEWED, PUBLISHED
    changelog = Column(Text, nullable=True)

    curriculum = relationship("Curriculum", back_populates="versions")

class Lesson(Base, TimestampMixin):
    __tablename__ = "lessons"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    curriculum_id = Column(String(36), ForeignKey("curricula.id", ondelete="CASCADE"), nullable=False)
    unit_number = Column(Integer, default=1)
    lesson_number = Column(Integer, nullable=False)
    title_hindi = Column(String(200), nullable=False)
    topic = Column(String(200), nullable=False)
    
    # Structured educational components extracted from JCERT texts
    learning_outcomes = Column(JSON, default=list)  # List of string outcomes
    activities = Column(JSON, default=list)         # Classroom instructional activities
    assessments = Column(JSON, default=list)       # Formative assessment prompts
    vocabulary = Column(JSON, default=list)        # Key target vocabulary items
    
    current_version = Column(Integer, default=1, nullable=False)

    curriculum = relationship("Curriculum", back_populates="lessons")
    versions = relationship("LessonVersion", back_populates="lesson", cascade="all, delete-orphan")

class LessonVersion(Base, TimestampMixin):
    __tablename__ = "lesson_versions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    lesson_id = Column(String(36), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    version_number = Column(Integer, nullable=False)
    checksum = Column(String(64), nullable=False)
    content_json = Column(JSON, nullable=False)
    status = Column(String(50), default="PUBLISHED", nullable=False)  # DRAFT, PUBLISHED, ARCHIVED

    lesson = relationship("Lesson", back_populates="versions")
