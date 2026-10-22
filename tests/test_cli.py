import sys

from llama_scan.cli import cli


def test_missing_pdf_exits(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(
        sys, "argv", ["llama-scan", str(tmp_path / "missing.pdf"), "-o", str(tmp_path)]
    )

    try:
        cli()
    except SystemExit as exc:
        assert exc.code == 1
    else:
        raise AssertionError("expected SystemExit")

    assert "PDF file not found" in capsys.readouterr().err


def test_help_lists_prompt_and_dpi(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["llama-scan", "--help"])

    try:
        cli()
    except SystemExit as exc:
        assert exc.code == 0
    else:
        raise AssertionError("expected SystemExit")

    help_text = capsys.readouterr().out
    assert "--prompt" in help_text
    assert "--dpi" in help_text
