from pathlib import Path
src=Path(r"D:\STORYBOARD_AI\tools\SWITCH_LIVE_STORYBOARD_TO_THIEN_SU_UI.py").read_text(encoding="utf-8")
exec(src.split("assert user32.GetForegroundWindow()")[0])
assert user32.GetForegroundWindow()==131934,"Do not send Ctrl+R to other applications"
send_key(VK_CONTROL)
send_key(ord("R"))
send_key(ord("R"),flags=2)
send_key(VK_CONTROL,flags=2)
time.sleep(4)
ImageGrab.grab().save(r"D:\STORYBOARD_AI\tools\ui_thien_su_visible_final_11min.jpg",quality=84)
print("REAL_DESKTOP_UI_REFRESHED_TO_LIVE_11_MINUTE_SCENES",user32.GetForegroundWindow())
