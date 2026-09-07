import io

def test_curriculum_upload_and_segmentation(client, admin_auth_headers):
    curriculum_txt = """
    TITLE: JCERT Test Math Class 2
    GRADE: 2
    SUBJECT: Mathematics

    LESSON: गिनती और जोड़
    OUTCOME: 1 से 20 तक गिनती समझना
    ACTIVITY: कंकड़ों से गिनना
    ASSESSMENT: कितने कंकड़ हैं?
    VOCAB: जोड़, गिनती
    """
    file_payload = ("test_curriculum.txt", io.BytesIO(curriculum_txt.encode("utf-8")), "text/plain")

    upload_res = client.post(
        "/api/v1/curriculum/upload",
        files={"file": file_payload},
        data={"title": "JCERT Test Math Class 2", "class_grade": 2, "subject": "Mathematics"},
        headers=admin_auth_headers
    )
    assert upload_res.status_code == 200
    data = upload_res.json()
    assert data["status"] == "INGESTED_AND_PUBLISHED"
    assert data["lessons_count"] >= 1

    # List curricula
    list_res = client.get("/api/v1/curriculum?class_grade=2")
    assert list_res.status_code == 200
    curricula = list_res.json()
    assert any(c["title"] == "JCERT Test Math Class 2" for c in curricula)


def test_list_lessons_with_filters_and_pagination(client):
    # The seeded Class 2 Mathematics curriculum has at least one lesson.
    res = client.get("/api/v1/lessons?class_grade=2&subject=Mathematics")
    assert res.status_code == 200
    body = res.json()
    assert "total" in body and "lessons" in body
    assert body["total"] >= 1
    first = body["lessons"][0]
    # List view returns a summary, not the full activities/assessments arrays.
    assert set(first.keys()) >= {
        "id", "curriculum_id", "lesson_number", "title_hindi", "topic",
        "learning_outcomes_count", "vocabulary_count", "version",
    }
    assert "activities" not in first

    # A grade with no seeded lessons returns an empty list, not an error.
    empty = client.get("/api/v1/lessons?class_grade=9")
    assert empty.status_code == 200
    assert empty.json()["total"] == 0

    # Pagination limit is honored.
    limited = client.get("/api/v1/lessons?limit=1")
    assert limited.status_code == 200
    assert len(limited.json()["lessons"]) <= 1

    # The detail route still resolves the id the list returned.
    detail = client.get(f"/api/v1/lessons/{first['id']}")
    assert detail.status_code == 200
    assert detail.json()["id"] == first["id"]
