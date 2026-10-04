"""Extract the provided local Web preview and capture it with Playwright."""
import argparse
import json
import zipfile
from pathlib import Path


def extract(source, target):
    with zipfile.ZipFile(source) as archive:
        for info in archive.infolist():
            if not info.filename.startswith('test/') or info.is_dir():
                continue
            output = (target / info.filename).resolve()
            if not output.is_relative_to(target.resolve()):
                raise ValueError('Archive member escapes preview directory')
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(archive.read(info))


def capture(target):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={'width': 1440, 'height': 1000}, device_scale_factor=1)
        page.goto((target / 'test/oreui-test.html').as_uri())
        page.wait_for_function('window.ORE_PREVIEW && window.ORE_PREVIEW.ready')
        page.add_style_tag(content='html{scroll-behavior:auto!important}')
        page.evaluate('document.fonts.ready')
        print(json.dumps(page.evaluate('window.ORE_PREVIEW'), ensure_ascii=False))
        page.screenshot(path=str(target / 'web-overview.png'))
        for name in ('Button', 'Checkbox', 'Dropdown', 'Card', 'TextField'):
            section = page.locator('#component-' + name)
            section.scroll_into_view_if_needed()
            page.wait_for_timeout(200)
            page.screenshot(path=str(target / ('web-' + name.lower() + '.png')))
        browser.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    parser.add_argument('--output', type=Path, default=Path('.runtime/reference-web'))
    parser.add_argument('--capture', action='store_true')
    args = parser.parse_args()
    extract(args.source, args.output)
    if args.capture:
        capture(args.output.resolve())
