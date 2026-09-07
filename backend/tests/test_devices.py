def test_device_registration_and_heartbeat(client):
    reg_payload = {
        "device_id": "TEST_TAB_DUMKA_999",
        "installation_id": "INST_TEST_999",
        "school_id": "GPS_DUMKA_01",
        "device_model": "Lava T81n",
        "android_version": "9.0 (API 28)",
        "app_version": "1.0.0",
        "total_ram_mb": 2048,
        "available_storage_mb": 5120,
        "supported_languages": ["hin", "sat"]
    }
    reg_res = client.post("/api/v1/devices/register", json=reg_payload)
    assert reg_res.status_code == 200
    reg_data = reg_res.json()
    assert "device_token" in reg_data
    assert reg_data["device"]["device_id"] == "TEST_TAB_DUMKA_999"

    # Send heartbeat
    hb_payload = {
        "device_id": "TEST_TAB_DUMKA_999",
        "available_storage_mb": 4900,
        "installed_models": {"nmt": "1.0.0", "asr": "1.0.0"}
    }
    hb_res = client.post("/api/v1/devices/heartbeat", json=hb_payload)
    assert hb_res.status_code == 200
    assert hb_res.json()["status"] == "HEARTBEAT_ACK"
