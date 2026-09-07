import os

def test_language_pack_build_and_delta_sync(client, db, admin_auth_headers):
    # 1. Build language pack
    build_res = client.post(
        "/api/v1/language-packs/build",
        json={"language_code": "sat", "version": "1.0.0", "min_app_version": "1.0.0"},
        headers=admin_auth_headers
    )
    assert build_res.status_code == 200
    pack_data = build_res.json()
    assert os.path.exists(pack_data["file_path"])
    assert "checksum" in pack_data

    # 2. Get server manifest
    manifest_res = client.get("/api/v1/sync/manifest?lang=sat")
    assert manifest_res.status_code == 200
    server_manifest = manifest_res.json()
    assert server_manifest["version"] == "1.0.0"

    # 3. Compute delta sync (simulating client with outdated phrase checksum)
    delta_payload = {
        "client_version": "0.9.0",
        "language_code": "sat",
        "client_checksums": {
            "phrases": "old_outdated_checksum_12345",
            "glossary": server_manifest["manifest"]["section_checksums"]["glossary"],
            "lessons": server_manifest["manifest"]["section_checksums"]["lessons"]
        }
    }
    delta_res = client.post("/api/v1/sync/delta", json=delta_payload)
    assert delta_res.status_code == 200
    delta_data = delta_res.json()
    assert delta_data["is_up_to_date"] is False
    assert delta_data["deltas_required"]["phrases"]["action"] == "UPDATE"
    assert delta_data["deltas_required"]["glossary"]["action"] == "UP_TO_DATE"

    # 4. Upload offline session sync. The device must first be registered, and
    #    the payload now carries the client-generated ids and teacher the
    #    server needs to actually persist the work (not just log a sync event).
    reg_res = client.post(
        "/api/v1/devices/register",
        json={
            "device_id": "TEST_TAB_DUMKA_999",
            "installation_id": "INSTALL_SYNC_TEST",
            "school_id": "GPS_DUMKA_01",
        },
    )
    assert reg_res.status_code == 200

    sync_upload_payload = {
        "device_id": "TEST_TAB_DUMKA_999",
        "offline_sessions": [
            {
                "client_session_id": "offline_sess_abc123",
                "teacher_id": "test_teacher_01",
                "topic": "Addition",
                "class_grade": 2,
                "subject": "Mathematics",
                "target_language": "sat",
            }
        ],
        "offline_utterances": [
            {
                "client_session_id": "offline_sess_abc123",
                "transcription": "बैठ जाओ",
                "translation": "ᱫᱩᱲᱩᱵ ᱢᱮ",
                "tier_used": "cache",
                "total_latency_ms": 25.0,
            }
        ],
    }
    upload_res = client.post("/api/v1/sync/upload", json=sync_upload_payload)
    assert upload_res.status_code == 200
    body = upload_res.json()
    assert body["status"] == "SYNC_MERGED"
    assert body["sessions_created"] == 1
    assert body["utterances_created"] == 1
    assert body["rejected"] == 0

    # 5. The session and utterance must genuinely exist now -- the previous
    #    implementation reported success without persisting anything.
    from backend.app.models.classroom import ClassroomSession, AudioUtterance
    session_row = db.query(ClassroomSession).filter_by(id="offline_sess_abc123").first()
    assert session_row is not None
    assert session_row.topic == "Addition"
    utter_rows = db.query(AudioUtterance).filter_by(session_id="offline_sess_abc123").all()
    assert len(utter_rows) == 1
    assert utter_rows[0].transcription == "बैठ जाओ"

    # 6. Re-uploading the same batch is idempotent, not duplicative.
    replay_res = client.post("/api/v1/sync/upload", json=sync_upload_payload)
    assert replay_res.status_code == 200
    replay_body = replay_res.json()
    assert replay_body["sessions_created"] == 0
    assert replay_body["sessions_skipped_already_synced"] == 1
    # The utterance attaches to the already-synced session, not rejected as orphan.
    assert replay_body["utterances_created"] == 1
    assert replay_body["rejected"] == 0

    # 7. An utterance referencing a non-existent session is rejected honestly,
    #    never silently dropped or misattached.
    orphan_res = client.post(
        "/api/v1/sync/upload",
        json={
            "device_id": "TEST_TAB_DUMKA_999",
            "offline_sessions": [],
            "offline_utterances": [
                {
                    "client_session_id": "no_such_session",
                    "transcription": "x",
                    "translation": "y",
                }
            ],
        },
    )
    assert orphan_res.status_code == 200
    orphan_body = orphan_res.json()
    assert orphan_body["status"] == "SYNC_PARTIAL"
    assert orphan_body["utterances_created"] == 0
    assert orphan_body["rejected"] == 1
    assert orphan_body["utterance_errors"][0]["error"] == "ORPHAN_UTTERANCE"
