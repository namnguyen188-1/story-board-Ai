import json,pathlib,shutil,subprocess,time,urllib.request
root=pathlib.Path(r"D:\STORYBOARD_AI\studio");cp=root/"runtime"/("production_tab_e2e_"+time.strftime("%Y%m%d_%H%M%S"));cp.mkdir()
names=["studio_mcp/production_tab.py","studio_mcp/node/production-job-tab.mjs","tests/test_pinned_tab_lifecycle_20261017.mjs"]
for n in names:
 p=cp/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/n,p)
p=root/names[0];s=p.read_text(encoding="utf-8");s=s.replace('req={"action":action,','req={"account_id":account["id"],"action":action,',1);compile(s,str(p),"exec");p.write_text(s,encoding="utf-8")
p=root/names[1];s=p.read_text(encoding="utf-8");s=s.replace("import path from 'node:path';","import path from 'node:path';\nimport {fileURLToPath} from 'node:url';",1)
a=s.index("   if(!path.isAbsolute(state)");b=s.index("   const dir=",a)
s=s[:a]+r'''   const ident=String(input.account_id||'');
   const studio=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..','..');
   const expected=path.join(studio,'flow_accounts',ident+'_state');
   const actual=fs.existsSync(state)?fs.realpathSync(state):path.resolve(state);
   const portable=/^account_[0-9a-f]{12}$/.test(ident)&&actual.toLowerCase()===expected.toLowerCase();
   const legacy=/[\\\/]\.storyboard-studio-(?:private-state-default|private-mcp-accounts|flow-mcp|flow-accounts)(?:[\\\/]|$)/i.test(actual);
   if(!path.isAbsolute(state)||(!portable&&!legacy))
    throw Error('FLOW_JOB_SESSION_PRIVATE_DRAFT_ARCHIVE_REQUIRED');
'''+s[b:];p.write_text(s,encoding="utf-8")
p=root/names[2];s=p.read_text(encoding="utf-8")
s=s.replace("const value=name==='node:fs'?","if(name==='node:url')return new vm.SyntheticModule(['fileURLToPath'],function(){this.setExport('fileURLToPath',()=>String(new URL('../studio_mcp/node/production-job-tab.mjs',import.meta.url)))},{context:sandbox});\n  const value=name==='node:fs'?",1)
p.write_text(s,encoding="utf-8")
try:
 for cmd in [
 [r"C:\Program Files\nodejs\node.exe","--check",str(root/names[1])],
 [str(root/"runtime/python/python.exe"),"-B",str(root/"tests/test_production_portable_contract.py")],
 [r"C:\Program Files\nodejs\node.exe","--experimental-vm-modules",str(root/"tests/test_production_portable_draft_archive.mjs")],
 [r"C:\Program Files\nodejs\node.exe","--experimental-vm-modules",str(root/"tests/test_pinned_tab_lifecycle_20261017.mjs")],
 [str(root/"runtime/python/python.exe"),"-B",str(root/"tests/test_studio_portable_account_paths.py")],
 [str(root/"runtime/python/python.exe"),"-B",str(root/"tests/test_flowkit_removed_offline.py")]]:
  r=subprocess.run(cmd,cwd=root,capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=60)
  (cp/(pathlib.Path(cmd[-1]).name+".log")).write_text(r.stdout+r.stderr,encoding="utf-8")
  print(pathlib.Path(cmd[-1]).name,r.returncode)
  if r.returncode:print(r.stdout+r.stderr);raise RuntimeError("REGRESSION_FAILED")
except Exception:
 for n in names:shutil.copy2(cp/n,root/n)
 raise
print(json.dumps({"checkpoint":str(cp),"result":"all selected tests pass"}))
