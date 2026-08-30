from pathlib import Path

from pm_manager_cli.audit import append_audit, read_audit


def test_append_creates_dir_and_roundtrips(tmp_path: Path) -> None:
    path = append_audit(
        tmp_path,
        command="pm-init",
        input_summary="confirm",
        output_summary="draft prd",
    )
    assert path.is_file()
    rows = read_audit(tmp_path)
    assert len(rows) == 1
    assert rows[0]["command"] == "pm-init"
    assert rows[0]["input_summary"] == "confirm"


def test_append_second_line(tmp_path: Path) -> None:
    append_audit(tmp_path, command="a")
    append_audit(tmp_path, command="b", reasoning="because")
    rows = read_audit(tmp_path)
    assert [r["command"] for r in rows] == ["a", "b"]
    assert rows[1]["reasoning"] == "because"
