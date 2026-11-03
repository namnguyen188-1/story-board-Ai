# Safe imports for engine tools (optional dependencies do not crash package load)
try:
    from .research import research_tool_fn, web_grounded_research_tool_fn
except ImportError:
    research_tool_fn = None
    web_grounded_research_tool_fn = None

try:
    from .director import director_tool_fn
except ImportError:
    director_tool_fn = None

try:
    from .image_prompt_tool import prompt_tool_fn
except ImportError:
    prompt_tool_fn = None

try:
    from .image_gen import image_gen_tool_fn
except ImportError:
    image_gen_tool_fn = None

try:
    from .tts import generate_tts_audio_tool_fn
except ImportError:
    generate_tts_audio_tool_fn = None

try:
    from .segmentation import segmentation_tool_fn
except ImportError:
    segmentation_tool_fn = None

try:
    from .merge_audio_video import merge_audio_video_tool_fn
except ImportError:
    merge_audio_video_tool_fn = None

try:
    from .concatenate_videos import concatenate_videos_tool_fn
except ImportError:
    concatenate_videos_tool_fn = None

try:
    from .subtitle import add_subtitle_tool_fn
except ImportError:
    add_subtitle_tool_fn = None

try:
    from .video_subtitle import burn_subtitles_to_video_tool_fn
except ImportError:
    burn_subtitles_to_video_tool_fn = None

try:
    from .transcribe_audio import transcribe_audio_tool_fn
except ImportError:
    transcribe_audio_tool_fn = None

try:
    from .narration_refiner import refine_narration_tool_fn
except ImportError:
    refine_narration_tool_fn = None

try:
    from .draw_animation import draw_animation_tool_fn
except ImportError:
    draw_animation_tool_fn = None

try:
    from .utils import set_output_dir, get_video_duration
except ImportError:
    set_output_dir = None
    get_video_duration = None

try:
    from .reference_search import reference_search_tool_fn
except ImportError:
    reference_search_tool_fn = None

try:
    from .video_gen import generate_video_veo_tool_fn
except ImportError:
    generate_video_veo_tool_fn = None

__all__ = [
    "research_tool_fn",
    "web_grounded_research_tool_fn",
    "director_tool_fn",
    "prompt_tool_fn",
    "image_gen_tool_fn",
    "generate_tts_audio_tool_fn",
    "segmentation_tool_fn",
    "merge_audio_video_tool_fn",
    "concatenate_videos_tool_fn",
    "add_subtitle_tool_fn",
    "burn_subtitles_to_video_tool_fn",
    "transcribe_audio_tool_fn",
    "refine_narration_tool_fn",
    "draw_animation_tool_fn",
    "set_output_dir",
    "get_video_duration",
    "reference_search_tool_fn",
    "generate_video_veo_tool_fn"
]
