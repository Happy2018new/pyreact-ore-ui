# -*- coding: utf-8 -*-
"""State images for controls measured from international Bedrock."""
from ..pyreact import Image, ImageAdaptionType, ButtonState


def skin_image(name, slices=(2, 2, 2, 3)):
    return Image(src='textures/pyreact_ore/skin/' + name,
                 imageAdaption=ImageAdaptionType.origin_nine_slice,
                 nineSliceData=slices)


def state_skin(prefix, selected=False, disabled=False, slices=(2, 2, 2, 3)):
    def build(state):
        suffix = 'disabled' if disabled else state
        return skin_image(prefix + ('_selected' if selected else '') + '_' + suffix, slices)
    return build
