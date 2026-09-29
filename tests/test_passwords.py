from jztech_core.passwords import hash_password, needs_rehash, verify_legacy_password, verify_password


def test_hash_and_verify_roundtrip():
    h = hash_password("Clave-Segura123!")
    assert verify_password("Clave-Segura123!", h)
    assert not verify_password("otra-clave", h)


def test_needs_rehash_false_for_fresh_hash():
    h = hash_password("Clave-Segura123!")
    assert needs_rehash(h) is False


def test_verify_legacy_bcrypt():
    import bcrypt

    stored = bcrypt.hashpw(b"Clave-Segura123!", bcrypt.gensalt()).decode()
    assert verify_legacy_password("Clave-Segura123!", stored)
    assert not verify_legacy_password("otra-clave", stored)


def test_verify_legacy_unknown_format_returns_false():
    assert verify_legacy_password("cualquier-cosa", "esto-no-es-un-hash-valido") is False
