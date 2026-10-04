"""Install the supplied local skills; never copy caches or executables."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def install(pyreact_root, editor_root):
    sources = {}
    for parent in (editor_root, pyreact_root):
        for skill in sorted((parent / '.agents/skills').iterdir()):
            if not (skill / 'SKILL.md').is_file():
                continue
            target = ROOT / '.agents/skills' / skill.name
            for source in skill.rglob('*'):
                if not source.is_file() or source.suffix in ('.pyc', '.exe'):
                    continue
                if '__pycache__' in source.parts or 'bin' in source.parts:
                    continue
                destination = target / source.relative_to(skill)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)
            sources[skill.name] = {
                'repository': parent.name,
                'source_sha256': hashlib.sha256((skill / 'SKILL.md').read_bytes()).hexdigest(),
            }
    # The projection reference remains a reference to the supplied editor, not
    # instructions for this independent library. Pyreact's upstream entry wins.
    projection = ROOT / '.agents/skills/pyreact-debugging/references/projection.md'
    if projection.exists():
        projection.write_text('# Reference project only\n\nThis document describes better-building-editor, not this repository.\n\n' + projection.read_text(encoding='utf-8'), encoding='utf-8')
    for name in ('mc-search', 'mod-workflow'):
        path = ROOT / '.agents/skills' / name / 'SKILL.md'
        body = path.read_text(encoding='utf-8-sig')
        body += '\n\n## 本仓库工具入口\n\n未连接 MCP 时用 `python -X utf8 tools/mcdk_docs.py minecraft_docs --command "help"` 或 `minecraft_py`，见同步记录。\n'
        path.write_text(body, encoding='utf-8')
    destination = ROOT / 'docs/vendor/mcdk-assistant.LICENSE.txt'
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(editor_root / 'docs/vendor/mcdk-assistant.LICENSE.txt', destination)
    (ROOT / 'docs/skills-sources.json').write_text(json.dumps(sources, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'installed': sorted(sources), 'destination': str(ROOT / '.agents/skills')}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--pyreact', type=Path, required=True)
    parser.add_argument('--editor', type=Path, required=True)
    args = parser.parse_args()
    install(args.pyreact.resolve(), args.editor.resolve())
