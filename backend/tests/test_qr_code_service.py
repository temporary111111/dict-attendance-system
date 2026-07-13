from app.services.qr_code_service import generate_qr_png, remove_qr_png


def test_generate_and_remove_qr_png(tmp_path):
    qr_path = generate_qr_png(
        "http://frontend.example.test/attendance?event=secure-code",
        tmp_path,
        "event-5-secure-code.png",
    )

    assert qr_path == tmp_path / "event-5-secure-code.png"
    assert qr_path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")

    remove_qr_png(tmp_path, "/media/qr-codes/event-5-secure-code.png")

    assert not qr_path.exists()
