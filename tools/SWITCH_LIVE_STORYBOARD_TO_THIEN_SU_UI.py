import ctypes,time
from ctypes import wintypes
from PIL import ImageGrab

user32=ctypes.windll.user32
VK_CONTROL=0x11;VK_A=0x41;VK_BACK=0x08
class KEYBDINPUT(ctypes.Structure):
 _fields_=[("wVk",wintypes.WORD),("wScan",wintypes.WORD),("dwFlags",wintypes.DWORD),("time",wintypes.DWORD),("dwExtraInfo",ctypes.c_void_p)]
class MOUSEINPUT(ctypes.Structure):
 _fields_=[("dx",wintypes.LONG),("dy",wintypes.LONG),("mouseData",wintypes.DWORD),("dwFlags",wintypes.DWORD),("time",wintypes.DWORD),("dwExtraInfo",ctypes.c_void_p)]
class HARDWAREINPUT(ctypes.Structure):
 _fields_=[("uMsg",wintypes.DWORD),("wParamL",wintypes.WORD),("wParamH",wintypes.WORD)]
class U(ctypes.Union):
 _fields_=[("ki",KEYBDINPUT),("mi",MOUSEINPUT),("hi",HARDWAREINPUT)]
class INPUT(ctypes.Structure):
 _fields_=[("type",wintypes.DWORD),("u",U)]

def send_key(vk,scan=0,flags=0):
 x=INPUT(type=1,u=U(ki=KEYBDINPUT(vk,scan,flags,0,None)))
 n=user32.SendInput(1,ctypes.byref(x),ctypes.sizeof(x))
 if n!=1:raise OSError("SEND_INPUT_FAILED")
def click(x,y):
 user32.SetCursorPos(x,y);time.sleep(.12)
 user32.mouse_event(2,0,0,0,0);time.sleep(.05);user32.mouse_event(4,0,0,0,0)
def all_select():
 send_key(VK_CONTROL);send_key(VK_A);send_key(VK_A,flags=2);send_key(VK_CONTROL,flags=2)
def type_unicode(s):
 for c in s:
  if c in "\n\r":continue
  cp=ord(c)
  if cp>0xffff:raise RuntimeError("NON_BMP_INPUT_UNSUPPORTED")
  send_key(0,scan=cp,flags=4)
  send_key(0,scan=cp,flags=6)
  time.sleep(.012)

assert user32.GetForegroundWindow()==131934,"STORYBOARD_APP_NOT_FOREGROUND"
click(450,283)  # Phim kịch đa vai
time.sleep(.5)
click(379,332)  # Tên phim
all_select()
type_unicode("THIÊN SƯ: HUYỀN PHÙ TRẤN QUỶ")
time.sleep(.35)
click(316,381)  # Tập số
all_select()
type_unicode("1")
time.sleep(3)
ImageGrab.grab().save(r"D:\STORYBOARD_AI\tools\ui_storyboard_after_switch_thien_su.jpg",quality=83)
print("UI_INPUTS_SENT_TO_LIVE_APP_FOREGROUND",user32.GetForegroundWindow(),flush=True)
