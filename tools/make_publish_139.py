from pathlib import Path
p=Path(r"D:\STORYBOARD_AI\dist\publish-muse-138.ps1")
s=p.read_text(encoding="utf-8-sig")
assert s.count("1.3.7")>=1 and s.count("1.3.8")>=7
s=s.replace("1.3.8","__NEWVERSION__").replace("1.3.7","1.3.8").replace("__NEWVERSION__","1.3.9")
assert "v1.3.8' --repo $repo --latest" in s
s=s.replace("CD83AFBE75B9E3B4AF4A144E2238316CAB90A5AB85A4EC03F17946C6D01D2F86","37258C170121D085B4118E936DA4C7BD6BE7C93869793DF0EEE510ED0E7966D1")
s=s.replace("286168891","286169202")
old="Storyboard AI Studio Pro 1.3.9\n- Display an explicit **Đăng nhập** button for Muse accounts instead of an ambiguous refresh icon.\n- Protect failed/pending Muse scene receipts from unintended resubmission and duplicate charges.\n- Normalize requested scene composition to 16:9 for image generation.\n- Preserve the existing Muse runtime, production pipeline, accounts, projects and update UI.\n- Regression: 30/30 Muse tests passed; live Korean-machine Muse image-to-video probe passed."
new="Storyboard AI Studio Pro 1.3.9\n- Fix one-click updates choosing stale GitHub Raw manifests.\n- Check both official update manifests, bust Raw CDN cache and select the highest verified version.\n- Preserve all Muse AI 1.3.8 fixes, login controls, projects, accounts and production pipeline.\n- Verified using stale v1.3.7 manifest and current v1.3.8 manifest."
assert old in s
s=s.replace(old,new)
s=s.replace("'Visible Muse login control.','Never re-submit failed or pending Muse scene jobs without explicit recovery.','Correct 16:9 scene ratio; preserve accounts, projects and existing pipeline.'","'One-click updater ignores stale Raw CDN manifests.','Compare both official manifests and choose the newest valid version.','Preserve Muse fixes, accounts, projects and existing pipeline.'")
s=s.replace("Muse Reliability and Login UI","Update Manifest Cache Repair")
s=s.replace("Muse reliability and login UI","updater manifest cache repair")
assert "'1.3.8'" in s and "1.3.9" in s
target=Path(r"D:\STORYBOARD_AI\dist\publish-update-139.ps1")
assert not target.exists()
target.write_text(s,encoding="utf-8-sig")
print("PUBLISH139_SCRIPT_CREATED", len(s.splitlines()))
