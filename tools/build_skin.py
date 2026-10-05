"""Rasterize the Ore CSS bevels and register scoped native input templates."""
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'resource_pack/textures/pyreact_ore/skin'
TEX = 'textures/pyreact_ore/skin/'
NS = 'OreUI'


def input_controls(search=False):
    # Leave room for the baked first glyph's bearing while retaining the native
    # editor's previous origin, available width and right inset.
    geometry = {'size': ['default', 'default'], 'min_size': ['100% - 6px', 0],
                'offset': [-3, 0], 'anchor_from': 'right_middle', 'anchor_to': 'right_middle'}
    display = dict(geometry, bindings=[
        {'binding_type': '$text_edit_box_content_binding_type',
         'binding_condition': '$text_edit_box_binding_condition',
         'binding_collection_name': '$text_edit_box_grid_collection_name',
         'binding_name': '$text_edit_box_content_binding_name', 'binding_name_override': '#item_name'},
        {'binding_name': '#newline_refresh'},
        {'binding_type': 'view', 'source_property_name': '#text_edit_selected', 'target_property_name': '#alpha'},
    ])
    return [{'centering_panel': {'type': 'panel', 'size': ['100%', '100%'], 'controls': ([
        {'search_icon': {'type': 'image', 'texture': 'textures/pyreact_ore/reference/reference_search',
            'layer': 4, 'size': [12, 12], 'offset': [7, 1], 'anchor_from': 'left_middle', 'anchor_to': 'left_middle'}}
        ] if search else []) + [
        {'clipper_panel': {'type': 'panel', 'size': ['100% - 28px' if search else '100% - 12px', '100% - 8px'],
            'offset': [8 if search else 0, 0],
            'clips_children': True, 'controls': [
                {'display_text@common.text_edit_box_label': display},
                {'visibility_panel': {'type': 'panel', 'controls': [
                    {'place_holder_control@common.text_edit_box_place_holder_label': dict(geometry)}],
                    'bindings': [{'binding_type': 'view', 'source_control_name': 'display_text',
                        'source_property_name': "(#item_name = '')", 'target_property_name': '#visible',
                        'resolve_sibling_scope': True}]}},
            ]}},
    ]}}, {'default@PyreactBase.edit_box_background_default': {}},
        {'hover@PyreactBase.edit_box_background_hover': {}},
        {'pressed@PyreactBase.edit_box_background_hover': {}},
        {'locked@PyreactBase.edit_box_background_default': {}}]


def bevel(name, fill, edge='#1e1e1f', top='#e6e8eb', bottom='#58585a', size=(12, 12)):
    image = Image.new('RGBA', size, edge)
    draw = ImageDraw.Draw(image)
    w, h = size
    draw.rectangle((1, 1, w - 2, h - 2), fill=fill)
    draw.line((1, 1, w - 2, 1), fill=top)
    draw.rectangle((1, h - 3, w - 2, h - 2), fill=bottom)
    image.save(OUT / (name + '.png'))


def patch(texture, size=('100%', '100%'), slices=(2, 2, 2, 3)):
    return {'type': 'image', 'texture': TEX + texture, 'size': list(size),
            'nineslice_size': list(slices), 'keep_ratio': False}


def reflected(fill, top, bottom, size=(16, 16), raised=True, edge='#1e1e1f'):
    image = Image.new('RGBA', size, edge)
    draw = ImageDraw.Draw(image)
    w, h = size
    base = h - 4 if raised else h - 2
    draw.rectangle((1, 1, w - 2, h - 2), fill=fill)
    draw.line((1, 1, w - 2, 1), fill=top)
    draw.line((1, 1, 1, base), fill=top)
    draw.line((1, base, w - 2, base), fill=bottom)
    draw.line((w - 2, 1, w - 2, base), fill=bottom)
    if raised:
        draw.rectangle((1, h - 3, w - 2, h - 2), fill='#58585a')
    # Reflection borders meet with two half-alpha edges in Gameface.
    corners = {'#d0d1d4': '#f4f4f5', '#b1b2b5': '#f9f9f9', '#8c8d90': '#acadaf', '#3c8527': '#72a763'}
    corner = corners.get(fill, top)
    draw.point((w - 2, 1), fill=corner)
    draw.point((1, base), fill=corner)
    return image


def control_skins():
    for state, fill, top, bottom in (
            ('default', '#d0d1d4', '#ecedee', '#e3e3e5'),
            ('hover', '#b1b2b5', '#eff0f0', '#e0e0e1'),
            ('pressed', '#b1b2b5', '#eff0f0', '#e0e0e1'),
            ('disabled', '#b1b2b5', '#eff0f0', '#e0e0e1')):
        reflected(fill, top, bottom, edge='#58585a' if state == 'disabled' else '#1e1e1f').save(OUT / ('thumb_' + state + '.png'))
        segment = reflected(fill, top, bottom)
        ImageDraw.Draw(segment).rectangle((1, 13, 14, 14), fill='#58585a')
        segment.save(OUT / ('segment_' + state + '.png'))
        for selected in (False, True):
            image = Image.new('RGBA', (30, 16))
            draw = ImageDraw.Draw(image)
            active = selected and state != 'disabled'
            track = reflected('#3c8527' if active else '#8c8d90',
                              '#639d52' if active else '#a3a4a6',
                              '#4f913c' if active else '#97989b', size=(30, 14), raised=False)
            image.paste(track, (0, 2))
            if selected:
                draw.rectangle((7, 6, 7, 11), fill='#ffffff' if active else '#58585a')
            else:
                draw.rectangle((19, 6, 24, 11), outline='#242425')
                draw.point((19, 6), fill='#8c8d90')
                draw.point((24, 6), fill='#8c8d90')
                draw.point((19, 11), fill='#8c8d90')
                draw.point((24, 11), fill='#8c8d90')
            thumb = Image.open(OUT / ('thumb_' + state + '.png'))
            image.paste(thumb, (14 if selected else 0, 0))
            image.save(OUT / ('switch_%s_%s.png' % ('on' if selected else 'off', state)))
        selected = reflected('#3c8527' if state != 'disabled' else '#58585a',
                             '#639d52', '#4f913c', size=(16, 14), raised=False)
        shifted = Image.new('RGBA', (16, 16))
        shifted.paste(selected, (0, 2))
        shifted.save(OUT / ('segment_selected_' + state + '.png'))
        for selected in (False, True):
            fill_nav = '#48494a' if selected or state in ('hover', 'pressed') else '#313233'
            image = Image.new('RGBA', (4, 6), fill_nav)
            if selected:
                edge_rows = ('#1d1e1f', '#2b2c2c', None, None, '#5a5b5c', '#454647')
            elif state in ('hover', 'pressed'):
                edge_rows = ('#454647', '#5a5b5c', None, None, '#2b2c2c', '#1d1e1f')
            else:
                edge_rows = (None,) * 6
            draw = ImageDraw.Draw(image)
            for row, color in enumerate(edge_rows):
                if color:
                    draw.line((0, row, 3, row), fill=color)
            image.save(OUT / ('navigation' + ('_selected' if selected else '') + '_' + state + '.png'))
            tab_fill = '#313233' if selected else '#58585a' if state == 'hover' else '#48494a'
            tab = reflected(tab_fill, '#5a5b5c' if selected else '#6d6d6e',
                '#454647' if selected else '#5a5b5c', raised=not selected,
                size=(16, 14) if selected else (16, 16))
            tab_draw = ImageDraw.Draw(tab)
            if not selected:
                tab_draw.rectangle((1, 13, 14, 14), fill='#313233')
            corner = '#6f7071' if selected else '#7b7b7c'
            tab.putpixel((14, 1), tuple(int(corner[i:i+2], 16) for i in (1, 3, 5)) + (255,))
            tab.putpixel((1, 12), tuple(int(corner[i:i+2], 16) for i in (1, 3, 5)) + (255,))
            if selected:
                lowered = Image.new('RGBA', (16, 16))
                lowered.paste(tab, (0, 2))
                tab = lowered
            tab.save(OUT / ('tab' + ('_selected' if selected else '') + '_' + state + '.png'))
        Image.new('RGBA', (1, 1), '#58585a' if state == 'hover' else '#313233' if state == 'pressed' else (0, 0, 0, 0)).save(OUT / ('icon_' + state + '.png'))
    Image.open(OUT / 'thumb_default.png').save(OUT / 'thumb.png')
    Image.open(OUT / 'thumb_disabled.png').save(OUT / 'thumb_locked.png')
    reflected('#8c8d90', '#a3a4a6', '#97989b', (8, 6), False).save(OUT / 'track.png')
    reflected('#3c8527', '#639d52', '#4f913c', (8, 6), False).save(OUT / 'progress.png')
    Image.open(OUT / 'progress.png').save(OUT / 'progress_hover.png')
    reflected('#48494a', '#707071', '#5a5b5c', raised=False).save(OUT / 'dropdown_header.png')
    for name in ('input', 'input_hover'):
        image = Image.new('RGBA', (8, 8), '#1e1e1f')
        draw = ImageDraw.Draw(image)
        draw.rectangle((1, 1, 6, 6), fill='#313233')
        draw.rectangle((1, 1, 6, 2), fill='#242425')
        image.save(OUT / (name + '.png'))


def radio_skins():
    # Source RadioBox.css: a 2rem square rotated 45 degrees, with base2
    # borders and a checked 0.8rem square split into four reflected tiles.
    for checked in (False, True):
        for state in ('default', 'hover', 'pressed', 'disabled'):
            fill = ('#3c8527' if state == 'default' else '#52a535' if state == 'hover' else '#2a641c') if checked else (
                '#8c8d90' if state == 'default' else '#b1b2b5' if state == 'hover' else '#58585a')
            if state == 'disabled':
                fill = '#d0d1d4'
            square = Image.new('RGBA', (80, 80), '#8c8d90' if state == 'disabled' else '#1e1e1f')
            draw = ImageDraw.Draw(square)
            draw.rectangle((8, 8, 71, 71), fill=fill)
            draw.line((8, 8, 71, 8), fill='#a3d292' if checked and state != 'disabled' else '#c1c1c4')
            draw.line((8, 8, 8, 71), fill='#a3d292' if checked and state != 'disabled' else '#c1c1c4')
            draw.line((71, 8, 71, 71), fill='#2a641c' if checked and state != 'disabled' else '#707071')
            draw.line((8, 71, 71, 71), fill='#2a641c' if checked and state != 'disabled' else '#707071')
            if checked:
                for box, color in (((24, 24, 39, 39), '#ffffff'), ((40, 24, 55, 39), '#e6e8eb'),
                                   ((24, 40, 39, 55), '#e6e8eb'), ((40, 40, 55, 55), '#d0d1d4')):
                    draw.rectangle(box, fill=color)
            diamond = square.rotate(-45, resample=Image.Resampling.BICUBIC, expand=True)
            image = Image.new('RGBA', (128, 128))
            image.paste(diamond, ((128 - diamond.width) // 2, (128 - diamond.height) // 2))
            image.save(OUT / ('radio_%s_%s.png' % ('on' if checked else 'off', state)))


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    for name in ('member', 'operator', 'player_permissions', 'permission_visitor', 'permission_custom',
                 'information', 'add_resource_pack', 'remove_resource_pack', 'chevron_up', 'chevron_down'):
        source = Image.open(OUT.parent / (name + '.png')).convert('RGBA')
        mask = Image.new('RGBA', source.size, '#ffffff')
        mask.putalpha(source.getchannel('A'))
        mask.save(OUT / (name + '_tintable.png'))
    bevel('input', '#313233', top='#1e1e1f', bottom='#58585a')
    bevel('input_hover', '#313233', edge='#ffffff', top='#1e1e1f', bottom='#58585a')
    bevel('track', '#1e1e1f', top='#1e1e1f', bottom='#58585a')
    bevel('progress', '#3c8527', top='#6cc349', bottom='#2a641c')
    bevel('progress_hover', '#52a535', top='#86d562', bottom='#3c8527')
    bevel('thumb', '#d0d1d4')
    bevel('thumb_hover', '#e6e8eb', edge='#ffffff')
    bevel('thumb_locked', '#8b8b8e')
    reflected('#e6e8eb', '#f0f1f3', '#f5f6f7', size=(6, 12), raised=True, edge='#000000').save(OUT / 'scroll_thumb.png')
    Image.new('RGBA', (1, 1)).save(OUT / 'transparent.png')
    Image.new('RGBA', (1, 6), '#1e1e1f').save(OUT / 'step.png')
    Image.new('RGBA', (1, 6), '#8c8d90').save(OUT / 'step_disabled.png')
    control_skins()
    radio_skins()
    for prefix, fill in (('pack', '#48494a'), ('pack_action', '#48494a'),
                          ('pack_group', '#313233'), ('menu_action', '#58585a')):
        for state in ('default', 'hover', 'pressed', 'disabled'):
            color = '#58585a' if state == 'hover' and prefix != 'pack_action' else '#707071' if state == 'hover' else fill
            if prefix == 'pack_group' and state == 'hover':
                color = '#48494a'
            if prefix == 'menu_action':
                color = '#48494a' if state == 'hover' else '#313233' if state == 'pressed' else fill
            image = Image.new('RGBA', (8, 8), '#1e1e1f')
            draw = ImageDraw.Draw(image)
            draw.rectangle((1, 1, 6, 6), fill=color)
            draw.rectangle((1, 1, 6, 1), fill='#8c8d90' if prefix == 'menu_action' else '#5a5b5c')
            draw.rectangle((1, 6, 6, 6), fill='#8c8d90' if prefix == 'menu_action' else '#454647')
            if prefix == 'menu_action':
                draw.rectangle((1, 1, 6, 6), outline='#8c8d90')
            elif prefix in ('pack', 'pack_action'):
                image = reflected(color, '#5a5b5c', '#323334', size=(8, 8), raised=False)
                image.putpixel((6, 1), (71, 71, 72, 255))
                image.putpixel((1, 6), (71, 71, 72, 255))
            elif prefix == 'pack_group':
                image = Image.new('RGBA', (8, 8), color)
                draw = ImageDraw.Draw(image)
                draw.line((0, 0, 7, 0), fill='#454647' if state != 'hover' else '#5a5b5c')
                draw.line((0, 0, 0, 7), fill='#454647' if state != 'hover' else '#5a5b5c')
                draw.line((7, 0, 7, 7), fill='#1d1e1f' if state != 'hover' else '#2b2c2c')
                draw.line((0, 7, 7, 7), fill='#1d1e1f' if state != 'hover' else '#2b2c2c')
                draw.point((7, 0), fill='#292a2b' if state != 'hover' else '#363737')
                draw.point((0, 7), fill='#292a2b' if state != 'hover' else '#363737')
            image.save(OUT / (prefix + '_' + state + '.png'))
    image = Image.new('RGBA', (2, 8))
    draw = ImageDraw.Draw(image)
    for y in (0, 3, 6):
        draw.rectangle((0, y, 1, y + 1), fill='white')
    image.save(OUT / 'more_vertical.png')
    for state in ('default', 'hover'):
        strip = Image.new('RGBA', (8, 6), '#3c8527')
        for y, color in ((0, '#1e1e1f'), (1, '#639d52'), (4, '#4f913c'), (5, '#1e1e1f')):
            ImageDraw.Draw(strip).line((0, y, 7, y), fill=color)
        strip.save(OUT / ('progress' + ('_hover' if state == 'hover' else '') + '.png'))
    disabled_track = reflected('#b1b2b5', '#c1c1c4', '#b9babc', (8, 6), False, '#8c8d90')
    disabled_track.putpixel((6, 1), (199, 199, 202, 255))
    disabled_track.putpixel((1, 4), (199, 199, 202, 255))
    disabled_track.save(OUT / 'track_disabled.png')
    disabled_thumb = reflected('#b1b2b5', '#e0e0e1', '#d0d1d3', edge='#58585a')
    disabled_thumb.putpixel((14, 1), (236, 236, 237, 255))
    disabled_thumb.putpixel((1, 12), (236, 236, 237, 255))
    ImageDraw.Draw(disabled_thumb).rectangle((1, 13, 14, 14), fill='#8c8d90')
    disabled_thumb.save(OUT / 'thumb_disabled.png')
    Image.new('RGBA', (1, 6), '#58585a').save(OUT / 'cap_disabled.png')
    disabled_progress = Image.new('RGBA', (8, 6), '#b1b2b5')
    for row, color in ((0, '#58585a'), (1, '#c1c1c4'), (4, '#b9babc'), (5, '#58585a')):
        ImageDraw.Draw(disabled_progress).line((0, row, 7, row), fill=color)
    disabled_progress.save(OUT / 'progress_disabled.png')
    Image.new('RGBA', (1, 1), '#58585a').save(OUT / 'scroll_track.png')
    menu_header = Image.new('RGBA', (8, 8), '#48494a')
    header_draw = ImageDraw.Draw(menu_header)
    header_draw.line((0, 0, 7, 0), fill='#6d6d6e')
    header_draw.line((0, 0, 0, 7), fill='#6d6d6e')
    header_draw.line((7, 0, 7, 7), fill='#5a5b5c')
    header_draw.line((0, 7, 7, 7), fill='#5a5b5c')
    header_draw.point((7, 0), fill='#7b7b7c')
    header_draw.point((0, 7), fill='#7b7b7c')
    menu_header.save(OUT / 'menu_header.png')
    skin = {'namespace': NS, 'glyph@PyreactBase.image': {'bilinear': True},
            'step@PyreactBase.image': {'texture': TEX + 'step', 'layer': 5},
            'field_text@PyreactBase.label': {'bindings': [{'binding_type': 'view',
                'source_control_name': 'display_text', 'source_property_name': '(not #text_edit_selected)',
                'target_property_name': '#visible', 'resolve_sibling_scope': True}]},
            'input@PyreactBase.input': {'$edit_box_default_texture': TEX + 'input',
                # JSON orders cuts left, top, right, bottom; the SDK API uses
                # left, right, top, bottom instead.
                '$edit_box_hover_texture': TEX + 'input_hover', '$nineslice_size': [1, 3, 1, 1],
                '$place_holder_text': '', '$font_scale_factor': 1.0,
                '$text_box_text_color': [1, 1, 1], 'controls': input_controls()},
            'scroll_thumb': patch('scroll_thumb'),
            'scroll_track': patch('scroll_track', (2, '100%'), (0, 0, 0, 0)),
            'scroll@PyreactBase.scrollBase': {'$scroll_size': [6, '100%'],
                '$scroll_size_touch': [6, '100%'],
                '$scroll_box_mouse_image_control': NS + '.scroll_thumb',
                '$scroll_box_touch_image_control': NS + '.scroll_thumb',
                '$scroll_track_image_control': NS + '.scroll_track'},
            'slider@PyreactBase.slider': {'$slider_box_size': [16, 16]}}
    # Each bevel has two texture rows in one logical pixel. Native nine-slice
    # cuts tie source rows to destination thickness, so use fixed-height UV
    # strips instead. They retain their thickness for custom navigation heights.
    skin['navigation_state@PyreactBase.image'] = {
        'size': ['100%', '100%'], 'layer': 0, 'bilinear': False,
        'texture': TEX + 'navigation_default', 'uv': [0, 2], 'uv_size': [4, 2],
        'controls': [{name: {'type': 'image', 'texture': TEX + 'navigation_default',
            'layer': 1, 'size': ['100%', 1], 'uv': [0, row], 'uv_size': [4, 2],
            'keep_ratio': False, 'bilinear': False,
            'anchor_from': anchor, 'anchor_to': anchor}}
            for name, row, anchor in (('top_edge', 0, 'top_left'), ('bottom_edge', 4, 'bottom_left'))]}
    skin['navigation@PyreactBase.button'] = {'controls': [
        {state + '@OreUI.navigation_state': {}} for state in ('default', 'hover', 'pressed')]}
    skin['search_input@OreUI.input'] = {'controls': input_controls(search=True)}
    slider = skin['slider@PyreactBase.slider']
    for state in ('default', 'hover'):
        names = ('slider_background', 'slider_progress') if state == 'default' else ('slider_background_hover', 'slider_progress_hover')
        skin['slider_bar_' + state] = {'type': 'image', 'texture': TEX + 'transparent',
            'size': ['100%', '100%'], 'controls': [{'sizing_panel': {'type': 'panel',
                'size': ['100% + 16px', '100%'], 'controls': [
                    {names[0] + '@OreUI.background_' + state: {'layer': 1}},
                    {names[1] + '@OreUI.progress_' + state: {'clip_direction': 'left', 'clip_pixelperfect': False, 'layer': 3}},
                    {'progress_left_cap': {'type': 'image', 'texture': TEX + 'step', 'size': [1, 6],
                        'anchor_from': 'left_middle', 'anchor_to': 'left_middle', 'layer': 5}},
                ]}}]}
    slider['controls'] = [
        {'slider_box@common.slider_box': {'$slider_box_layout': '$slider_box_layout',
            '$slider_box_size': '$slider_box_size', '$slider_track_button': '$slider_name', 'layer': 10}},
        {'slider_bar_default@OreUI.slider_bar_default': {}},
        {'slider_bar_hover@OreUI.slider_bar_hover': {'visible': False}},
    ]
    for state in ('default', 'hover'):
        for kind, texture in [('background', 'track'), ('progress', 'progress' + ('_hover' if state == 'hover' else ''))]:
            name = kind + '_' + state
            skin[name] = patch(texture, ('100%', 6), (2, 2, 2, 2))
            if kind == 'progress':
                skin[name] = dict(type='image', texture=TEX + 'progress' + ('_hover' if state == 'hover' else ''),
                                  size=['100%', 6], keep_ratio=False)
            slider['$' + name + '_control'] = NS + '.' + name
    for suffix, texture in [('', 'thumb'), ('_hover', 'thumb_hover'), ('_locked', 'thumb_locked'), ('_indent', 'thumb_hover')]:
        name = 'slider_box' + suffix
        skin[name] = patch(texture, slices=(2, 2, 2, 4))
        slider['$slider_box' + suffix + '_layout'] = NS + '.' + name
    for suffix, texture in [('', 'track'), ('_hover', 'track'), ('_progress', 'progress'), ('_progress_hover', 'progress_hover')]:
        name = 'slider_step' + suffix
        skin[name] = dict(type='image', texture=TEX + 'transparent', size=[1, 6],
                          layer=4, offset='$step_offset')
    slider['$slider_step_factory_control_ids'] = dict(
        ('slider_step' + suffix, '@' + NS + '.slider_step' + suffix)
        for suffix in ('', '_hover', '_progress', '_progress_hover'))
    output = ROOT / 'resource_pack/ui/OreUI.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(skin, indent=2) + '\n', encoding='utf8')


if __name__ == '__main__':
    build()
