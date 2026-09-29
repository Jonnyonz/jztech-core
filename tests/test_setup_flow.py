from jztech_core.setup_flow import verify_setup_token


def test_verify_setup_token_matches():
    assert verify_setup_token("abc123", "abc123")


def test_verify_setup_token_rejects_mismatch():
    assert not verify_setup_token("abc123", "otro")


def test_verify_setup_token_rejects_when_not_configured():
    assert not verify_setup_token("", "abc123")
