def test_classroom_session_and_context_commands(client, teacher_auth_headers):
    # 1. Create active session
    create_res = client.post(
        "/api/v1/classrooms/sessions",
        json={
            "class_grade": 2,
            "subject": "Mathematics",
            "topic": "Addition up to 20",
            "learning_outcome": "Students can add two single-digit numbers",
            "target_language": "sat"
        },
        headers=teacher_auth_headers
    )
    assert create_res.status_code == 200
    session_id = create_res.json()["session_id"]

    # 2. Add dialogue context item
    item_res = client.post(
        f"/api/v1/context/{session_id}/items",
        json={
            "item_type": "dialogue",
            "content": {"speaker": "teacher", "text_hindi": "कंकड़ों को मिलाकर गिनो"}
        }
    )
    assert item_res.status_code == 200

    # 3. Test Context-Aware Command: 'Give me three easy questions'
    cmd_res = client.post(
        f"/api/v1/context/{session_id}/command",
        json={"command": "Give me three easy questions"}
    )
    assert cmd_res.status_code == 200
    cmd_data = cmd_res.json()
    assert cmd_data["action"] == "GENERATE_QUESTIONS"
    assert len(cmd_data["result"]) == 3

    # 4. Test Context-Aware Command: 'Explain this activity in the target language'
    exp_res = client.post(
        f"/api/v1/context/{session_id}/command",
        json={"command": "Explain this activity in the target language"}
    )
    assert exp_res.status_code == 200
    exp_data = exp_res.json()
    assert exp_data["action"] == "EXPLAIN_ACTIVITY"
    assert exp_data["target_language"] == "sat"

    # 5. End session
    end_res = client.post(f"/api/v1/classrooms/sessions/{session_id}/end", headers=teacher_auth_headers)
    assert end_res.status_code == 200
