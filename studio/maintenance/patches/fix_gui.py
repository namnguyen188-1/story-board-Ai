from pathlib import Path
p=Path(r"D:\STORYBOARD_AI\studio\studio_gui.py")
s=p.read_text(encoding="utf-8")
changes={
'self.lang=self.entry(head,"Ngôn ngữ thoại","English",1,0,24)':'self.lang=self.entry(head,"Ngôn ngữ thoại","English",2,0,24)',
'self.model=self.entry(head,"Gemini LLM","gemini-2.5-pro",1,2,24)':'self.model=self.entry(head,"Gemini LLM","gemini-2.5-pro",2,2,24)',
'text="Render").grid(row=1':'text="Render").grid(row=2',
'self.res.grid(row=2':'self.res.grid(row=3',
'text="Số luồng").grid(row=1':'text="Số luồng").grid(row=2',
'self.workers.grid(row=2':'self.workers.grid(row=3'
}
for old,new in changes.items():
    assert old in s,repr(old)
    s=s.replace(old,new,1)
anchor='        inbox=HOME/"inbox";inbox.mkdir(exist_ok=True)'
assert anchor in s
s=s.replace(anchor,
    '        if not offline and not messagebox.askyesno("Xác nhận chi phí API",\\n'
    '                 f"Tập {number}: sẽ có khoảng {int(minutes*2)} cảnh, mỗi cảnh dùng nhiều lượt Gemini (ảnh, TTS, lời thoại). Tiếp tục?"):\\n'
    '            return\\n' + anchor, 1)
# Expand escaped newline for syntactic Python.
s=s.replace('API",\\n','API",\n').replace('tục?"):\\n','tục?"):\n').replace('            return\\n        inbox','            return\n        inbox')
p.write_text(s,encoding="utf-8")
import py_compile
py_compile.compile(str(p),doraise=True)
print("GUI_PATCH_COMPILE_PASS")
