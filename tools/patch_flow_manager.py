from pathlib import Path

def patch():
    p = Path("studio/flow_account_manager.py")
    c = p.read_text(encoding="utf-8").replace("\r\n", "\n")
    t = 'if p_cand.exists() or (p_cand.parent.exists() and "thean" not in str(p_cand).lower() or os.path.exists(r"C:\\Users\\thean")):'
    r = 'if p_cand.exists() or (p_cand.parent.exists() and os.path.exists(str(p_cand.parent))):'
    assert t in c, "target not found"
    c = c.replace(t, r)
    p.write_text(c.replace("\n", "\r\n"), encoding="utf-8")
    print("SUCCESS: studio/flow_account_manager.py patched")

if __name__ == "__main__":
    patch()
