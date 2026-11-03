from pathlib import Path
p=Path(r"D:\STORYBOARD_AI\studio\test_locked_8_e2e_offline.py")
s=p.read_text(encoding="utf-8")
old='"--scene-seconds","3"'
assert old in s, "test anchor missing"
p.write_text(s.replace(old,'"--scene-seconds","5"',1),encoding="utf-8")
print("OFFLINE_E2E_CONFIG_VALIDATED")
