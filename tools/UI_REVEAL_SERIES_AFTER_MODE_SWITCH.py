from pathlib import Path
source=Path(r"D:\STORYBOARD_AI\tools\SWITCH_LIVE_STORYBOARD_TO_THIEN_SU_UI.py").read_text(encoding="utf-8")
exec(source.split("assert user32.GetForegroundWindow()")[0])
assert user32.GetForegroundWindow()==131934
# Restore accidental "1" typed into idea input, not a valid project change
click(360,345)
all_select()
send_key(VK_BACK);send_key(VK_BACK,flags=2)
time.sleep(.25)
user32.SetCursorPos(380,395)
user32.mouse_event(0x0800,0,0,120*12,0)
time.sleep(.8)
ImageGrab.grab().save(r"D:\STORYBOARD_AI\tools\ui_storyboard_ready_to_select_series.jpg",quality=82)
print("IDEA_INPUT_CLEARED_AND_TOP_SETTINGS_REVEALED")
