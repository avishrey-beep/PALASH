"""Speech endpoint contract tests, rewritten for the on-device architecture.

The previous tests asserted the mock's behaviour: that ASR echoed the caller's
``expected_text`` back as a "transcription" and that ``/synthesize`` returned a
``wav`` format. Both were confirming the fabrication this project removed, so
they are replaced with tests of the honest contract.
"""


def test_synthesize_returns_speakable_pronunciation_form(client):
    """/synthesize keeps its shape but returns a real speakable form.

    For an Ol Chiki input the Hindi TTS voice cannot pronounce, it must return
    a Devanagari transliteration flagged as approximate.
    """
    res = client.post(
        "/api/v1/speech/synthesize",
        data={"text": "ᱫᱩᱲᱩᱵ ᱢᱮ", "language": "sat"},
    )
    assert res.status_code == 200
    data = res.json()
    # Original contract keys still present.
    for key in ("text", "language", "tier", "latency_ms", "duration_seconds", "format"):
        assert key in data
    # No more fake WAV; it is a pronunciation form now.
    assert data["format"] == "text/pronunciation-deva"
    assert data["transliterated"] is True
    assert data["pronunciation_is_approximate"] is True
    assert data["verified_by_native_speaker"] is False
    assert data["disclaimer"]  # non-empty honesty label
    # The Devanagari the device will actually speak.
    assert data["speech_text"] == "दुड़ुब मे"


def test_synthesize_hindi_needs_no_transliteration(client):
    res = client.post(
        "/api/v1/speech/synthesize",
        data={"text": "बैठ जाओ", "language": "hin"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["transliterated"] is False
    assert data["pronunciation_is_approximate"] is False
    assert data["disclaimer"] is None


def test_voice_to_voice_translate_is_retired_501(client):
    """Server-side ASR is gone; the route must refuse honestly, not fake it."""
    res = client.post(
        "/api/v1/speech/translate",
        files={"audio": ("a.wav", b"\x00\x01\x02", "audio/wav")},
        data={"source_language": "hin", "target_language": "sat"},
    )
    assert res.status_code == 501
    detail = res.json()["detail"]
    assert detail["error"] == "SERVER_SIDE_ASR_REMOVED"
    assert "on_device_path" in detail
