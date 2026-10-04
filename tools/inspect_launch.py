"""Read-only diagnostics when a managed launch has not reached ready state."""
import argparse
import base64
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.agents/skills/pyreact-debugging/scripts'))
from _session import load_session, process_identity
from mcdk import Client


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', required=True)
    parser.add_argument('--owner', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    session = load_session(args.session, args.owner, live=False)
    for kind in ('mcdk', 'game'):
        pid = session.get(kind + '_pid')
        if not pid or process_identity(pid) != session.get(kind + '_identity'):
            raise RuntimeError('Managed launch process identity changed: ' + kind)
    args.output.mkdir(parents=True, exist_ok=True)
    with Client(session['mcp_url'], timeout=15, bind_session=False) as client:
        results = {}
        for name in ('get_latest_logs', 'get_latest_error_logs', 'capture_game_window'):
            arguments = {} if name == 'capture_game_window' else {'max_count': 50, 'order': 'asc'}
            result = client.call(name, arguments)
            for content in result.get('content', []):
                if content.get('type') == 'image':
                    (args.output / 'capture.jpg').write_bytes(base64.b64decode(content['data']))
                    content['data'] = '<saved as capture.jpg>'
            results[name] = result
        (args.output / 'launch-diagnostics.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps(results, ensure_ascii=False, indent=2))
