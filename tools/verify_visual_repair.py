"""Capture repaired pages and assert actual glyph and image geometry."""
import argparse
import json
from pathlib import Path
from verify_atlas import AtlasVerification, PAGES
from live_support import nodes, find_key

PROBE = '''from ore_demo.pyreact import host
from ore_demo.oreui._text import LabelPrimitive
from ore_demo.oreui._image import ImagePrimitive
from ore_demo.oreui.typography import layout
from ore_demo.oreui import OreTag, OreBadge
runtime = host._ACTIVE_HOST[0]
def walk(fiber):
    yield fiber
    for child in fiber.child_fibers:
        for item in walk(child):
            yield item
text_errors = []
image_errors = []
texts = images = 0
for fiber in walk(runtime._root_fiber):
    applied = fiber.primitive_state.get('_layout_applied')
    if not applied:
        continue
    if isinstance(fiber.comp_type, LabelPrimitive):
        texts += 1
        if fiber.props.get('content') and not fiber.props.get('singleLine'):
            pieces, widths = layout(fiber.props['content'], fiber.props['fontSize'], applied[0])
            expected = len(widths) * fiber.props['fontSize'] * 1.5
            if expected > applied[1] + 0.6:
                text_errors.append(dict(text=fiber.props['content'], expected=expected, actual=applied[1]))
        parent = fiber.parent_fiber
        while parent and parent.comp_type not in (OreTag, OreBadge):
            parent = parent.parent_fiber
        if parent:
            surface = next(item for item in walk(parent) if item.native_path)
            bounds = runtime.GetBaseUIControl(surface.native_path)
            control = runtime.GetBaseUIControl(fiber.native_path)
            bx, by = bounds.GetGlobalPosition()
            bw, bh = bounds.GetSize()
            tx, ty = control.GetGlobalPosition()
            tw, th = control.GetSize()
            if tx < bx - .1 or ty < by - .1 or tx + tw > bx + bw + .1 or ty + th > by + bh + .1:
                text_errors.append(dict(text=fiber.props['content'], reason='tag content outside surface'))
    if isinstance(fiber.comp_type, ImagePrimitive) and fiber.props.get('contain'):
        images += 1
        control = runtime.GetBaseUIControl(fiber.native_path)
        width, height = control.GetSize()
        sw, sh = fiber.props['sourceSize']
        if height > 0 and abs(width / height / (float(sw) / sh) - 1) > .01:
            image_errors.append(dict(src=fiber.props['src'], size=[width, height], source=[sw, sh]))
_result = dict(texts=texts, images=images, text_errors=text_errors, image_errors=image_errors)
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', required=True)
    parser.add_argument('--owner', required=True)
    parser.add_argument('--output', type=Path, default=Path('.runtime/repair-visuals'))
    args = parser.parse_args()
    tools = AtlasVerification(args.session, args.owner, args.output)
    tools.mount()
    frame = next(node['layout'] for node in nodes(tools.dump('initial')) if node.get('layout'))
    tools.screen = [frame['width'], frame['height']]
    results = []
    for page in PAGES:
        tree = tools.page(page)
        tools.capture(page)
        probe = tools.code(PROBE, 'geometry-' + page)
        results.append(dict(page=page, probe=probe))
        print(json.dumps(results[-1], ensure_ascii=False), flush=True)
        if page == 'media':
            tools.code("from ore_demo import dev_probe\n_result=dev_probe.reveal('lab_scroll_media_0','asset_a')\n", 'media-thumbnails')
            tools.capture('media-thumbnails')
        if page in ('selection', 'navigation', 'messages', 'media'):
            tools.scroll(page, 100)
            tools.capture(page + '-bottom')
    tools.page('dropdowns')
    tools.tap('lab_dropdown')
    tools.capture('dropdown-open')
    tools.click('ore_dropdown_close')
    tools.page('dialogs')
    for key in ('lab_open_dialog', 'lab_open_progress', 'lab_open_menu', 'lab_open_warning'):
        tools.click(key)
        tools.check(key + ' is visible', find_key(tools.dump(key), 'lab_dialog')['props']['visible'])
        results.append(dict(page=key, probe=tools.code(PROBE, 'geometry-' + key)))
        tools.capture(key)
        tools.click('ore_dialog_close')
    for key in ('lab_drawer_left', 'lab_drawer_right'):
        tools.click(key)
        tools.capture(key)
        tools.click('ore_drawer_close')
    (tools.output / 'geometry.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf8')
    return 1 if any(item['probe']['text_errors'] or item['probe']['image_errors'] for item in results) else 0


if __name__ == '__main__':
    raise SystemExit(main())
