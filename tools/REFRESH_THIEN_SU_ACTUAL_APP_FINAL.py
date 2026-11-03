from pathlib import Path
base=Path(r"D:\STORYBOARD_AI\tools\SWITCH_LIVE_STORYBOARD_TO_THIEN_SU_UI.py").read_text(encoding="utf-8")
exec(base.split("assert user32.GetForegroundWindow()")[0])
if user32.GetForegroundWindow()!=131934:
    click(458,1060) # existing Storyboard AI taskbar icon; never relaunch exe
    time.sleep(.45)
assert user32.GetForegroundWindow()==131934,"STORYBOARD_COULD_NOT_BE_FOCUSED_DO_NOT_SEND_KEYS"
send_key(VK_CONTROL);send_key(ord("R"));send_key(ord("R"),flags=2);send_key(VK_CONTROL,flags=2)
time.sleep(4)
ImageGrab.grab().save(r"D:\STORYBOARD_AI\tools\ui_thien_su_correct_mode_and_storyboard.jpg",quality=86)
print("LIVE_STORYBOARD_WINDOW_UPDATED_AND_ON_SCREEN",user32.GetForegroundWindow(),flush=True)
