from pathlib import Path
p=Path(r"D:\STORYBOARD_AI\studio\web_server.py")
text=p.read_text(encoding="utf-8")
a='''                if action == "create":
                    result = create(body.get("name"))
                elif action == "select":'''
b='''                if action == "create":
                    result = create(body.get("name"))
                    select(result["id"])  # New Studio profile is active immediately.
                elif action == "select":'''
assert a in text,"Account creation anchor missing"
p.write_text(text.replace(a,b,1),encoding="utf-8")
print("ACCOUNT_AUTO_SELECT_PATCH_PASS")
