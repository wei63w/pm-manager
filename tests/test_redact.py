from pm_manager_cli.redact import contains_secret_residue, redact


def test_redacts_aws_key() -> None:
    raw = "key=AKIAIOSFODNN7EXAMPLE leftover"
    out = redact(raw)
    assert "AKIAIOSFODNN7EXAMPLE" not in out
    assert "***" in out
    assert "leftover" in out


def test_redacts_pem_block() -> None:
    pem = "-----BEGIN PRIVATE KEY-----\nMIIHide\n-----END PRIVATE KEY-----"
    out = redact(pem)
    assert "BEGIN PRIVATE KEY" not in out
    assert out.strip() == "***"


def test_plain_text_unchanged() -> None:
    text = "TODO-001 fix the login timeout"
    assert redact(text) == text


def test_empty() -> None:
    assert redact("") == ""


def test_contains_secret_residue() -> None:
    assert contains_secret_residue("AKIAIOSFODNN7EXAMPLE")
    assert contains_secret_residue("-----BEGIN PRIVATE KEY-----")
    assert not contains_secret_residue("TODO-001 leftover")
