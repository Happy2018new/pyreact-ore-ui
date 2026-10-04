"""Inspect source modules inside the supplied Ore distribution."""
import argparse
import zipfile

parser = argparse.ArgumentParser()
parser.add_argument('archive')
parser.add_argument('terms', nargs='+')
args = parser.parse_args()
with zipfile.ZipFile(args.archive) as archive:
    for path in archive.namelist():
        if path.endswith('.css') and any(
                '/' + term.lower() + '/' in path.lower() for term in args.terms):
            print(path)
            print(archive.read(path).decode('utf8'))
