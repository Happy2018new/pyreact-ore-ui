"""Stdio client for the separately installed mcdk-assistant."""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def call(binary, tool, command):
    process = subprocess.Popen([str(binary), '--stdio'], cwd=binary.parent,
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL)

    def send(message):
        process.stdin.write((json.dumps(message) + '\n').encode('utf8'))
        process.stdin.flush()

    def receive(identity):
        for line in iter(process.stdout.readline, b''):
            try:
                result = json.loads(line)
            except ValueError:
                continue
            if result.get('id') == identity:
                return result
        raise RuntimeError('mcdk-assistant exited before replying')

    try:
        send({'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {
            'protocolVersion': '2024-11-05', 'capabilities': {},
            'clientInfo': {'name': 'pyreact-ore-ui', 'version': '0.1.0'}}})
        receive(1)
        send({'jsonrpc': '2.0', 'method': 'notifications/initialized'})
        send({'jsonrpc': '2.0', 'id': 2, 'method': 'tools/call', 'params': {
            'name': tool, 'arguments': {'command': command}}})
        return receive(2)
    finally:
        process.terminate()
        process.wait(timeout=10)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('tool', choices=('minecraft_docs', 'minecraft_py'))
    parser.add_argument('--command', required=True)
    parser.add_argument('--exe', default=os.environ.get('MCDK_ASSISTANT_EXE'))
    args = parser.parse_args()
    if not args.exe:
        parser.error('Set MCDK_ASSISTANT_EXE or pass --exe (see docs/MCDK_ASSISTANT_UPSTREAM.md)')
    result = call(Path(args.exe).resolve(), args.tool, args.command)
    sys.stdout.write(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    sys.exit(1 if result.get('error') or result.get('result', {}).get('isError') else 0)
