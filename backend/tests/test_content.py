import os

def test_worksheet_generation_and_export(client):
    payload = {
        "class_grade": 2,
        "subject": "Mathematics",
        "topic": "Addition up to 20",
        "target_language": "sat",
        "question_count": 3,
        "difficulty": "EASY"
    }
    res = client.post("/api/v1/worksheets/generate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "worksheet_id" in data
    assert len(data["questions"]) == 3
    assert "Q1" in data["answer_key"]
    assert os.path.exists(data["pdf_path"])

    # Test HTML view
    html_res = client.get(f"/api/v1/worksheets/{data['worksheet_id']}/html")
    assert html_res.status_code == 200
    assert "JCERT Jharkhand" in html_res.text

    # Test PDF download
    pdf_res = client.get(f"/api/v1/worksheets/{data['worksheet_id']}/pdf")
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"

def test_flashcard_creation_and_deduplication(client):
    fc_payload = {
        "concept": "two",
        "category": "numbers",
        "hindi_term": "दो",
        "target_language": "sat",
        "target_term": "ᱵᱟᱨ",
        "pronunciation": "bar"
    }
    # 1. Create
    res1 = client.post("/api/v1/flashcards", json=fc_payload)
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["target_term"] == "ᱵᱟᱨ"

    # 2. Re-create same concept returns identical deterministic ID (Zero duplicates)
    res2 = client.post("/api/v1/flashcards", json=fc_payload)
    assert res2.status_code == 200
    assert res2.json()["deterministic_id"] == data1["deterministic_id"]

    # 3. List
    list_res = client.get("/api/v1/flashcards?category=numbers&target_language=sat")
    assert list_res.status_code == 200
    cards = list_res.json()
    assert any(c["concept"] == "two" for c in cards)
