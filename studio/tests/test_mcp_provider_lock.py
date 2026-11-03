from pathlib import Path
import sys
root=Path(__file__).parent
sys.path.insert(0,str(root))
from series_studio import parser,run
args=parser().parse_args(["run","--mode","live","--series","Whiteboard Chronicles",
                          "--episode","1","--prompt","Original animation story",
                          "--minutes","2","--image-provider","mcp_v2",
                          "--mcp-max-images","1","--workers","1"])
try:
    run(args)
except RuntimeError as exc:
    assert "Choose a new episode number" in str(exc),str(exc)
    print("PROVIDER_SWITCH_PROTECTION_PASS")
else:
    raise AssertionError("Already completed Episode 1 must not be silently overwritten")
