from pathlib import Path
base=Path(r"D:\STORYBOARD_AI\tools\SWITCH_LIVE_STORYBOARD_TO_THIEN_SU_UI.py").read_text(encoding="utf-8")
exec(base.split("assert user32.GetForegroundWindow()")[0])
assert user32.GetForegroundWindow()==131934
click(380,360)
all_select()
type_unicode("THIÊN SƯ: HUYỀN PHÙ TRẤN QUỶ")
time.sleep(.1)
click(313,408)
all_select()
type_unicode("1")
time.sleep(3.2)
ImageGrab.grab().save(r"D:\STORYBOARD_AI\tools\ui_thien_su_project_switched_actual.jpg",quality=85)
print("ACTUAL_DESKTOP_STORYBOARD_PROJECT_SWITCH_COMPLETE",user32.GetForegroundWindow())
