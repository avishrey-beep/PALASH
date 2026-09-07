from sqlalchemy import Column, String, Integer, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.app.core.database import Base
from backend.app.models.base import TimestampMixin, generate_uuid

class Worksheet(Base, TimestampMixin):
    """
    Structured, contextual bilingual worksheet generated from lesson topics.
    Outputs JSON, HTML, and printable PDF formats with separate answer key.
    """
    __tablename__ = "worksheets"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    lesson_id = Column(String(36), ForeignKey("lessons.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(200), nullable=False)
    class_grade = Column(Integer, nullable=False)
    subject = Column(String(100), nullable=False)
    topic = Column(String(200), nullable=False)
    learning_outcome = Column(Text, nullable=True)
    target_language = Column(String(10), nullable=False)
    difficulty = Column(String(50), default="EASY")  # EASY, MEDIUM, HARD
    question_count = Column(Integer, default=5)
    
    html_content = Column(Text, nullable=True)
    pdf_path = Column(String(500), nullable=True)
    json_data = Column(JSON, nullable=False)
    answer_key_json = Column(JSON, nullable=False)

    questions = relationship("WorksheetQuestion", back_populates="worksheet", cascade="all, delete-orphan")

class WorksheetQuestion(Base, TimestampMixin):
    __tablename__ = "worksheet_questions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    worksheet_id = Column(String(36), ForeignKey("worksheets.id", ondelete="CASCADE"), nullable=False)
    question_number = Column(Integer, nullable=False)
    question_type = Column(String(50), nullable=False)  # fill_in_the_blanks, matching, multiple_choice, counting, arithmetic
    prompt_hindi = Column(Text, nullable=False)
    prompt_target = Column(Text, nullable=False)
    options = Column(JSON, nullable=True)
    correct_answer = Column(Text, nullable=False)

    worksheet = relationship("Worksheet", back_populates="questions")

class Flashcard(Base, TimestampMixin):
    """
    Multilingual visual flashcard for early vocabulary building.
    Deterministic ID ensures zero duplicate asset generation across devices.
    """
    __tablename__ = "flashcards"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    deterministic_id = Column(String(64), unique=True, index=True, nullable=False)  # SHA-256(category:concept:target_lang)
    concept = Column(String(100), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)  # numbers, animals, fruits, classroom, body_parts
    hindi_term = Column(String(150), nullable=False)
    target_term = Column(String(150), nullable=False)
    target_language = Column(String(10), nullable=False)
    pronunciation = Column(String(150), nullable=True)
    image_asset_path = Column(String(500), nullable=True)
    audio_asset_path = Column(String(500), nullable=True)

class AudioAsset(Base, TimestampMixin):
    """
    Audio asset metadata tracking pre-recorded and synthesized clips.
    """
    __tablename__ = "audio_assets"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    checksum = Column(String(64), unique=True, index=True, nullable=False)
    language = Column(String(10), index=True, nullable=False)
    text = Column(Text, nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size_bytes = Column(Integer, default=0)
    format = Column(String(10), default="wav")  # wav, ogg, mp3
    speaker_gender = Column(String(10), default="female")
    sample_rate_hz = Column(Integer, default=16000)
