"""Rasterize the Ore CSS bevels and register scoped native input templates."""
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'resource_pack/textures/pyreact_ore/skin'
TEX = 'textures/pyreact_ore/skin/'
NS = 'OreUI'


def scroll_controls():
    # Preserve common.scrolling_panel's touch variables. Only the mouse
    # ScrollView changes speed; input and clipping remain engine-managed.
    touch = {'ignored': '(not $touch)', 'size': '$pane_size_touch',
        'offset': '$scrolling_pane_offset', '$use_touch_mode': True,
        '$scroll_track_image_control': 'common.empty_panel',
        '$allow_scroll_even_when_content_fits': '$allow_scrolling_even_when_content_fits',
        'variables': [{'requires': '$wider_scroll_area', '$pane_size_touch': '$scrolling_pane_size_touch'},
                      {'requires': '(not $wider_scroll_area)', '$pane_size_touch': '$scrolling_pane_size'}]}
    for name in ('scroll_bar_contained', 'scroll_box_visible', 'background_size', 'background_offset',
                 'scroll_view_port_size', 'scroll_view_port_max_size', 'scroll_view_port_offset',
                 'scroll_bar_left_padding_size', 'scroll_bar_right_padding_size', 'view_port_size', 'scroll_size'):
        touch['$' + name] = '$' + name + '_touch'
    mouse = {'ignored': '$touch', 'size': '$scrolling_pane_size', 'offset': '$scrolling_pane_offset',
        'controls': [{'scroll_view@common.scroll_view_control': {
            'allow_scroll_even_when_content_fits': '$allow_scroll_even_when_content_fits', 'scroll_speed': 40}}]}
    return [{'scroll_touch@common.scrolling_panel_base': touch},
            {'scroll_mouse@common.scrolling_panel_base': mouse}]


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
        segment = reflected(fill, top, bottom, raised=state != 'pressed')
        if state != 'pressed':
            ImageDraw.Draw(segment).rectangle((1, 13, 14, 14), fill='#58585a')
        segment.save(OUT / ('segment_' + state + '.png'))
        for selected in (False, True):
            image = Image.new('RGBA', (30, 16))
            draw = ImageDraw.Draw(image)
            active = selected and state != 'disabled'
            track = reflected('#3c8527' if active else '#8c8d90',
                              '#639d52' if active else '#a3a4a6',
                              '#4f913c' if active else '#97989b', size=(30, 14), raised=False)
            if state == 'disabled':
                track = Image.new('RGBA', (30, 14), '#8c8d90')
                ImageDraw.Draw(track).rectangle((1, 1, 28, 12), fill='#b1b2b5')
            image.paste(track, (0, 2))
            if selected:
                draw.rectangle((7, 6, 7, 11), fill='#ffffff' if active else '#6d6d6d')
            else:
                draw.rectangle((19, 6, 24, 11), outline='#6d6d6d' if state=='disabled' else '#242425')
                for point in ((19,6),(24,6),(19,11),(24,11)):
                    draw.point(point, fill='#b1b2b5' if state=='disabled' else '#8c8d90')
            thumb = Image.open(OUT / ('thumb_' + state + '.png'))
            if state == 'disabled':
                thumb = Image.new('RGBA', (16,16), '#58585a')
                thumb_draw=ImageDraw.Draw(thumb)
                thumb_draw.rectangle((1,1,14,12),fill='#b1b2b5')
                thumb_draw.rectangle((1,13,14,14),fill='#8c8d90')
            image.paste(thumb, (14 if selected else 0, 0))
            image.save(OUT / ('switch_%s_%s.png' % ('on' if selected else 'off', state)))
        selected = reflected('#3c8527' if state != 'disabled' else '#58585a',
                             '#639d52', '#4f913c', size=(16, 14), raised=False)
        shifted = Image.new('RGBA', (16, 16))
        shifted.paste(selected, (0, 2))
        shifted.save(OUT / ('segment_selected_' + state + '.png'))
        for selected in (False, True):
            fill_nav = '#48494a' if selected or state == 'hover' else '#242425' if state == 'pressed' else '#313233'
            image = Image.new('RGBA', (4, 6), fill_nav)
            if selected:
                edge_rows = ('#1d1e1f', '#2b2c2c', None, None, '#5a5b5c', '#454647')
            elif state == 'pressed':
                edge_rows = ('#0a0a0a', '#070707', None, None, '#39393a', '#454647')
            elif state == 'hover':
                edge_rows = ('#454647', '#5a5b5c', None, None, '#2b2c2c', '#1d1e1f')
            else:
                edge_rows = (None,) * 6
            draw = ImageDraw.Draw(image)
            for row, color in enumerate(edge_rows):
                if color:
                    draw.line((0, row, 3, row), fill=color)
            image.save(OUT / ('navigation' + ('_selected' if selected else '') + '_' + state + '.png'))
            flat_tab = selected or state == 'pressed'
            tab_fill = '#313233' if flat_tab else '#58585a' if state == 'hover' else '#48494a'
            tab = reflected(tab_fill, '#5a5b5c' if flat_tab else '#79797b' if state == 'hover' else '#6d6d6e',
                '#454647' if flat_tab else '#68686a' if state == 'hover' else '#5a5b5c', raised=not flat_tab,
                size=(16, 14) if selected else (16, 16))
            tab_draw = ImageDraw.Draw(tab)
            if not flat_tab:
                tab_draw.rectangle((1, 13, 14, 14), fill='#313233')
            corner = '#6a6b6c' if flat_tab else '#868688' if state == 'hover' else '#7b7b7c'
            tab.putpixel((14, 1), tuple(int(corner[i:i+2], 16) for i in (1, 3, 5)) + (255,))
            tab.putpixel((1, tab.height - 2 if flat_tab else 12), tuple(int(corner[i:i+2], 16) for i in (1, 3, 5)) + (255,))
            if selected:
                lowered = Image.new('RGBA', (16, 16))
                lowered.paste(tab, (0, 2))
                tab = lowered
            tab.save(OUT / ('tab' + ('_selected' if selected else '') + '_' + state + '.png'))
        Image.new('RGBA', (1, 1), '#58585a' if state == 'hover' else '#313233' if state == 'pressed' else (0, 0, 0, 0)).save(OUT / ('icon_' + state + '.png'))
        Image.new('RGBA', (1, 1), '#f4f6f9' if state == 'hover' else '#d0d1d4' if state == 'pressed' else (0, 0, 0, 0)).save(OUT / ('icon_light_' + state + '.png'))
    # Measured international button faces. The original ZIP uses different
    # reflection colors for several pressed edges, including secondary.
    palettes = {
        'secondary': [('default', '#d0d1d4', '#ecedee', '#e3e3e5', '#f4f4f5'),
                      ('hover', '#b1b2b5', '#eff0f0', '#e0e0e1', '#f9f9f9'),
                      ('pressed', '#b1b2b5', '#eff0f0', '#e0e0e1', '#f9f9f9')],
        'primary': [('default', '#3c8527', '#639d52', '#4f913c', '#72a763'),
                    ('hover', '#2a641c', '#7fa277', '#699260', '#a5bea0'),
                    ('pressed', '#1d4d13', '#779471', '#608259', '#a0b49b')],
    }
    for variant, palette in palettes.items():
        for raised in (False, True):
            for state, fill, top, bottom, corner in palette:
                elevated = raised and state != 'pressed'
                image = reflected(fill, top, bottom, raised=elevated)
                if elevated:
                    ImageDraw.Draw(image).rectangle((1, 13, 14, 14), fill='#1d4d13' if variant == 'primary' else '#58585a')
                rgba = tuple(int(corner[i:i+2], 16) for i in (1, 3, 5)) + (255,)
                image.putpixel((14, 1), rgba)
                image.putpixel((1, 12 if elevated else 14), rgba)
                image.save(OUT / ('button_' + variant + ('_raised' if raised else '') + '_' + state + '.png'))
    Image.open(OUT / 'thumb_default.png').save(OUT / 'thumb.png')
    Image.open(OUT / 'thumb_disabled.png').save(OUT / 'thumb_locked.png')
    reflected('#8c8d90', '#a3a4a6', '#97989b', (8, 6), False).save(OUT / 'track.png')
    reflected('#3c8527', '#639d52', '#4f913c', (8, 6), False).save(OUT / 'progress.png')
    Image.open(OUT / 'progress.png').save(OUT / 'progress_hover.png')
    header=reflected('#48494a', '#6d6d6e', '#5a5b5c', raised=False)
    header.putpixel((14,1),(123,123,124,255))
    header.putpixel((1,14),(123,123,124,255))
    header.save(OUT / 'dropdown_header.png')
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
                 'information', 'add_resource_pack', 'remove_resource_pack', 'chevron_up', 'chevron_down', 'edit'):
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
    scroll_thumb = reflected('#e6e8eb', '#f5f6f7', '#f0f1f3', size=(6, 12), raised=True, edge='#000000')
    scroll_thumb.putpixel((1, 8), (249, 250, 250, 255))
    scroll_thumb.putpixel((4, 1), (249, 250, 250, 255))
    scroll_thumb.save(OUT / 'scroll_thumb.png')
    Image.new('RGBA', (1, 1)).save(OUT / 'transparent.png')
    Image.new('RGBA', (1, 6), '#1e1e1f').save(OUT / 'step.png')
    Image.new('RGBA', (1, 6), '#8c8d90').save(OUT / 'step_disabled.png')
    control_skins()
    radio_skins()
    for state in ('default', 'hover', 'pressed', 'disabled'):
        binding = Image.new('RGBA', (8, 8), '#ffffff' if state in ('hover','pressed') else '#1e1e1f')
        draw = ImageDraw.Draw(binding)
        draw.rectangle((1, 1, 6, 6), fill='#b1b2b5' if state == 'disabled' else '#313233')
        draw.line((1, 1, 6, 1), fill='#a1a2a5' if state == 'disabled' else '#242425')
        binding.save(OUT / ('binding_' + state + '.png'))
    for prefix, fill in (('pack', '#48494a'), ('pack_action', '#48494a'),
                          ('pack_group', '#313233'), ('menu_action', '#58585a')):
        for state in ('default', 'hover', 'pressed', 'disabled'):
            color = '#58585a' if state == 'hover' else '#313233' if state == 'pressed' else fill
            if prefix == 'pack_group' and state == 'hover':
                color = '#48494a'
            if prefix == 'pack_group' and state == 'pressed':
                color = '#242425'
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
                top, bottom, corner = ('#68686a', '#3e3e3f', '#49494a') if state == 'hover' else (
                    '#454647', '#222324', '#303132') if state == 'pressed' else ('#5a5b5c', '#333334', '#3f4041')
                image = reflected(color, top, bottom, size=(8, 8), raised=False)
                rgba = tuple(int(corner[i:i+2], 16) for i in (1, 3, 5)) + (255,)
                image.putpixel((6, 1), rgba)
                image.putpixel((1, 6), rgba)
            elif prefix == 'pack_group':
                image = Image.new('RGBA', (8, 8), color)
                draw = ImageDraw.Draw(image)
                draw.line((0, 0, 7, 0), fill='#454647' if state != 'hover' else '#5a5b5c')
                draw.line((0, 0, 0, 7), fill='#454647' if state != 'hover' else '#5a5b5c')
                draw.line((7, 0, 7, 7), fill='#1d1e1f' if state != 'hover' else '#2b2c2c')
                draw.line((0, 7, 7, 7), fill='#1d1e1f' if state != 'hover' else '#2b2c2c')
                draw.point((7, 0), fill='#292a2b' if state != 'hover' else '#363737')
                draw.point((0, 7), fill='#292a2b' if state != 'hover' else '#363737')
                if state == 'pressed':
                    draw.line((0, 0, 7, 0), fill='#070707')
                    draw.line((0, 0, 0, 7), fill='#070707')
                    draw.line((7, 0, 7, 7), fill='#39393a')
                    draw.line((0, 7, 7, 7), fill='#39393a')
                    draw.point((7, 0), fill='#1f1f1f')
                    draw.point((0, 7), fill='#1f1f1f')
            image.save(OUT / (prefix + '_' + state + '.png'))
    # Joined cells have bevels but no private black border. Their row owns it.
    for prefix in ('player_cell', 'player_options', 'pack_cell', 'pack_options'):
        for state in ('default', 'hover', 'pressed', 'disabled'):
            fill = '#58585a' if state == 'hover' else '#313233' if state == 'pressed' else '#48494a'
            player = prefix.startswith('player')
            top = ('#69696b' if player else '#68686a') if state == 'hover' else ('#464747' if player else '#454647') if state == 'pressed' else '#5a5b5c'
            bottom = '#3e3e3f' if state == 'hover' else '#222324' if state == 'pressed' else '#323334' if player else '#333334'
            image = reflected(fill, top, bottom, size=(8, 8), raised=False)
            corner_hex = ('#515152' if player else '#49494a') if state == 'hover' else ('#38393a' if player else '#303132') if state == 'pressed' else '#474748' if player else '#3f4041'
            corner = tuple(int(corner_hex[i:i+2], 16) for i in (1, 3, 5)) + (255,)
            image.putpixel((6, 1), corner)
            image.putpixel((1, 6), corner)
            image.crop((1, 1, 7, 7)).save(OUT / (prefix + '_' + state + '.png'))
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
            'scroll_thumb': patch('scroll_thumb', slices=(2, 2, 2, 4)),
            'scroll_track': patch('scroll_track', (2, '100%'), (0, 0, 0, 0)),
            'scroll@PyreactBase.scrollBase': {'$scroll_size': [6, '100%'],
                '$scroll_size_touch': [6, '100%'],
                '$scroll_box_mouse_image_control': NS + '.scroll_thumb',
                '$scroll_box_touch_image_control': NS + '.scroll_thumb',
                '$scroll_track_image_control': NS + '.scroll_track',
                'controls': scroll_controls()},
            'slider@PyreactBase.slider': {'$slider_box_size': [16, 16]}}
    skin['scroll_thumb']['controls'] = [{'bottom_shadow': {
        'type': 'image', 'texture': 'textures/ui/white_bg', 'color': [0, 0, 0],
        'alpha': 0.2, 'size': [6, 1], 'offset': [0, 0], 'keep_ratio': False,
        'anchor_from': 'bottom_left', 'anchor_to': 'top_left', 'layer': 1}}]
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
    skin['pressable@PyreactBase.button'] = {'is_handle_button_move_event': True, 'controls': [
        {state + '@PyreactBase.image': {'size': ['100%', '100%'], 'layer': 0}}
        for state in ('default', 'hover', 'pressed')] + [
        {'content': {'type': 'panel', 'size': ['100%', '100%'], 'layer': 1,
                     'anchor_from': 'top_left', 'anchor_to': 'top_left'}}]}
    skin['search_input@OreUI.input'] = {'controls': input_controls(search=True)}
    for name, search in (('readonly_input', False), ('readonly_search_input', True)):
        content = input_controls(search=search)[0]
        content['centering_panel']['controls'][-1]['clipper_panel']['controls'] = []
        skin[name + '@PyreactBase.panel'] = {'controls': [
            {'frame@PyreactBase.image': {'visible': True, 'layer': 0,
                'texture': TEX + 'input', 'size': ['100%', '100%'],
                'nineslice_size': [1, 3, 1, 1]}}, content]}
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
                    {'progress_right_cap': {'type': 'image', 'texture': TEX + 'step', 'size': [1, 6],
                        'anchor_from': 'right_middle', 'anchor_to': 'right_middle', 'layer': 5}},
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
