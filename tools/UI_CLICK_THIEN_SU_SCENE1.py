from pathlib import Path
source=Path(r"D:\STORYBOARD_AI\tools\SWITCH_LIVE_STORYBOARD_TO_THIEN_SU_UI.py").read_text(encoding="utf-8")
exec(source.split("assert user32.GetForegroundWindow()")[0])
assert user32.GetForegroundWindow()==131934
click(651,264)
time.sleep(.9)
ImageGrab.grab().save(r"D:\STORYBOARD_AI\tools\ui_thien_su_after_scene1_select.jpg",quality=84)
print("THIEN_SU_SCENE1_CLICKED_IN_LIVE_UI")
