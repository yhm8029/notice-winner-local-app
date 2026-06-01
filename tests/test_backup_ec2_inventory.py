from __future__ import annotations

import json

from scripts.backup_ec2_inventory import build_find_command
from scripts.backup_ec2_inventory import parse_find_output
from scripts.backup_ec2_inventory import write_ec2_inventory


def test_build_find_command_quotes_paths_for_remote_shell():
    command = build_find_command(["/home/ubuntu/app/output", "/home/ubuntu/app/logs"])

    assert "find" in command
    assert "'/home/ubuntu/app/output'" in command
    assert "'/home/ubuntu/app/logs'" in command
    assert "%p\\t%s\\t%TY-%Tm-%TdT%TH:%TM:%TS%Tz\\n" in command


def test_parse_find_output_returns_file_records():
    output = "/app/output/a.xlsx\t123\t2026-06-01T12:30:00.000000000+0900\n"

    rows = parse_find_output(output)

    assert rows == [
        {
            "path": "/app/output/a.xlsx",
            "size_bytes": 123,
            "modified_at": "2026-06-01T12:30:00.000000000+0900",
        }
    ]


def test_write_ec2_inventory_writes_manifest(tmp_path):
    manifest = write_ec2_inventory(
        tmp_path,
        ssh_target="ubuntu@example",
        paths=["/app/output"],
        files=[{"path": "/app/output/a.xlsx", "size_bytes": 123, "modified_at": "2026"}],
        timestamp="20260601_120000",
    )

    assert manifest["ssh_target"] == "ubuntu@example"
    assert manifest["file_count"] == 1
    assert json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))["file_count"] == 1
