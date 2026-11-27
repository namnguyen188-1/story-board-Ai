"""Flow image model aliases, verified against Google Flow Help 2026-11-08.

Source: https://support.google.com/flow/answer/16352836?hl=en-1
The legacy NANO_BANANA_2 key remains stable in saved client requests.
Video SDK identifiers must be verified independently; do not infer them here.
"""

IMAGE_MODEL_DISPLAY = {
    'NANO_BANANA_PRO': '\U0001f34c Nano Banana Pro',
    'NANO_BANANA_2': '\U0001f34c Nano Banana 2.1',
    'NANO_BANANA_2_LITE': '\U0001f34c Nano Banana 2 Lite',
}


def image_model_key(value):
    if not isinstance(value, str):
        raise ValueError('Unsupported Flow image model')
    key = value.strip().upper()
    key = {'NANO_BANANA_2.1': 'NANO_BANANA_2',
           'NANO_BANANA_2_1': 'NANO_BANANA_2'}.get(key, key)
    if key not in IMAGE_MODEL_DISPLAY:
        raise ValueError('Unsupported Flow image model')
    return key


def image_model_display(value):
    return IMAGE_MODEL_DISPLAY[image_model_key(value)]


VIDEO_MODEL_DISPLAY = {
    'OMNI_1_2_FLASH': 'Omni 1.2 Flash',
    'VEO_3_1_LITE': 'Veo 3.1 - Lite',
    'OMNI_1_1_FLASH': 'Omni 1.1 Flash',
}

def video_model_key(value):
    if not isinstance(value, str):
        raise ValueError('Unsupported Flow video model')
    key = value.strip().upper()
    if key not in VIDEO_MODEL_DISPLAY:
        raise ValueError('Unsupported Flow video model')
    return key

def video_model_display(value):
    return VIDEO_MODEL_DISPLAY[video_model_key(value)]
