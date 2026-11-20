"""Fail the build if a protected comparison version was changed or removed."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'config/frozen-versions.json'


def verify():
    manifest = json.loads(MANIFEST.read_text())
    problems = []
    for version in manifest['versions']:
        for relative, expected in version['files'].items():
            path = ROOT / relative
            if not path.is_file():
                problems.append(f'Missing: {relative}')
            elif hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                problems.append(f'Changed: {relative}')
    if problems:
        raise SystemExit('Protected version modified. Restore it before building:\n' + '\n'.join(problems))
    print('Frozen version 3: unchanged.')


if __name__ == '__main__':
    verify()
