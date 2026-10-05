# -*- coding: utf-8 -*-
"""State images for controls measured from international Bedrock."""
from ..pyreact import Image, ImageAdaptionType, ButtonState


def skin_image(name, slices=(2, 2, 2, 3)):
    return Image(src='textures/pyreact_ore/skin/' + name,
                 imageAdaption=ImageAdaptionType.origin_nine_slice,
                 nineSliceData=slices)


def state_skin(prefix, selected=False, disabled=False, slices=(2, 2, 2, 3), pressedSlices=None):
    def build(state):
        suffix = 'disabled' if disabled else state
        edges = pressedSlices if state == ButtonState.pressed and not disabled and pressedSlices is not None else slices
        return skin_image(prefix + ('_selected' if selected else '') + '_' + suffix, edges)
    return build
