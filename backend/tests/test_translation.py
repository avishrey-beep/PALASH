from backend.app.services.translation_service import TranslationService

def test_translation_pipeline_exact_cache(client, db):
    # Seed a verified phrase
    TranslationService.add_verified_phrase(
        db,
        source_text="यहाँ बैठो",
        target_text="ᱱᱚᱸᱰᱮ ᱫᱩᱲᱩᱵ ᱢᱮ",
        source_lang="hin",
        target_lang="sat"
    )

    # Translate
    res = client.post("/api/v1/translation/translate", json={
        "text": "यहाँ बैठो",
        "source_lang": "hin",
        "target_lang": "sat"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["target_text"] == "ᱱᱚᱸᱰᱮ ᱫᱩᱲᱩᱵ ᱢᱮ"
    assert data["confidence"] == 1.0
    assert "cache" in data["tier"]
    assert data["latency_ms"] < 100.0  # Fast cache retrieval

def test_human_review_workflow(client, reviewer_auth_headers, db):
    # Submit review task
    task = TranslationService.submit_for_review(
        db,
        source_text="कक्षा में शांति रखो",
        model_translation="ᱠᱞᱟᱥ ᱨᱮ ᱥᱟᱱᱛ ᱛᱟᱦᱮᱸᱱ ᱢᱮ",
        source_lang="hin",
        target_lang="sat"
    )

    # Reviewer approves with edit
    decision_payload = {
        "decision": "EDIT",
        "corrected_translation": "ᱠᱞᱟᱥ ᱨᱮ ᱛᱷᱤᱨ ᱛᱟᱦᱮᱸᱱ ᱢᱮ",
        "reason": "Corrected dialectal term for quiet/peaceful"
    }
    dec_res = client.post(
        f"/api/v1/translation/review/tasks/{task.id}/decision",
        json=decision_payload,
        headers=reviewer_auth_headers
    )
    assert dec_res.status_code == 200
    dec_data = dec_res.json()
    assert dec_data["decision"] == "EDIT"
    assert dec_data["approved_target"] == "ᱠᱞᱟᱥ ᱨᱮ ᱛᱷᱤᱨ ᱛᱟᱦᱮᱸᱱ ᱢᱮ"

    # Now translating the same phrase hits the newly verified cache!
    trans_res = client.post("/api/v1/translation/translate", json={
        "text": "कक्षा में शांति रखो",
        "source_lang": "hin",
        "target_lang": "sat"
    })
    assert trans_res.status_code == 200
    assert trans_res.json()["target_text"] == "ᱠᱞᱟᱥ ᱨᱮ ᱛᱷᱤᱨ ᱛᱟᱦᱮᱸᱱ ᱢᱮ"
