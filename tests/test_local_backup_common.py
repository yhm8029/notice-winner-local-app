from __future__ import annotations

import json

from scripts.local_backup_common import create_backup_dir
from scripts.local_backup_common import load_env_file
from scripts.local_backup_common import sha256_file
from scripts.local_backup_common import summarize_file
from scripts.local_backup_common import write_json
from scripts.local_backup_common import write_jsonl


def test_load_env_file_sets_missing_values_without_overwriting(tmp_path, monkeypatch):
    env_file = tmp_path / ".env.local-backup"
    env_file.write_text(
        "SUPABASE_URL=https://example.supabase.co\n"
        "SUPABASE_SECRET_KEY='secret-value'\n"
        "EXISTING=from-file\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("EXISTING", "from-env")

    loaded = load_env_file(env_file)

    assert loaded == {
        "SUPABASE_URL": "https://example.supabase.co",
        "SUPABASE_SECRET_KEY": "secret-value",
        "EXISTING": "from-file",
    }
    assert loaded["SUPABASE_SECRET_KEY"] == "secret-value"
    assert loaded["EXISTING"] == "from-file"


def test_write_json_and_jsonl_create_utf8_files(tmp_path):
    json_path = tmp_path / "manifest.json"
    jsonl_path = tmp_path / "rows.jsonl"

    write_json(json_path, {"status": "ok", "count": 2})
    write_jsonl(jsonl_path, [{"id": 1}, {"id": 2}])

    assert json.loads(json_path.read_text(encoding="utf-8")) == {"status": "ok", "count": 2}
    assert jsonl_path.read_text(encoding="utf-8").splitlines() == ['{"id":1}', '{"id":2}']


def test_sha256_and_summarize_file(tmp_path):
    target = tmp_path / "data.txt"
    target.write_text("abc", encoding="utf-8")

    summary = summarize_file(target)

    assert sha256_file(target) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    assert summary["path"] == str(target)
    assert summary["size_bytes"] == 3
    assert summary["sha256"] == sha256_file(target)


def test_create_backup_dir_uses_prefix_and_timestamp(tmp_path):
    backup_dir = create_backup_dir(tmp_path, "supabase", timestamp="20260601_120000")

    assert backup_dir == tmp_path / "supabase" / "20260601_120000"
    assert backup_dir.is_dir()
