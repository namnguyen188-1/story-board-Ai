import ast,json,pathlib,re,shutil,subprocess,time,urllib.request
root=pathlib.Path(r"D:\STORYBOARD_AI\studio");cp=root/"runtime"/("mcp_account_path_fix_"+time.strftime("%Y%m%d_%H%M%S"));cp.mkdir()
with urllib.request.urlopen("http://127.0.0.1:8765/api/status",timeout=4) as r:assert json.load(r).get("running") is False,"STUDIO_BUSY_NO_CHANGE"
names=["studio_mcp/transport.py","studio_mcp/node/studio-flow-rpc.mjs","studio_mcp/auto_flow_manager.py","flow_account_manager.py"]
original={n:(root/n).read_text(encoding="utf-8-sig") for n in names};updated=dict(original)
s=updated["studio_mcp/transport.py"]
s=s.replace('import os\n','import os\nimport re\n',1)
a=s.index("    def within(path,parents):")
s=s[:a]+'''    # Portable accounts created by Studio have exact account-owned directories.
    # Resolve paths to retain the existing rejection of foreign/V2 or linked roots.
    ident = str(row.get("id") or "")
    if re.fullmatch(r"account_[0-9a-f]{12}", ident):
        allowed_profile += ((HOME/"flow_accounts"/ident).resolve(),)
        allowed_state += ((HOME/"flow_accounts"/(ident+"_state")).resolve(),)
'''+s[a:]
s=s.replace('        env.update(account_env(row))','        env.update(account_env(row))\n        env["STORYBOARD_MCP_ACCOUNT_ID"]=row["id"]',1)
updated["studio_mcp/transport.py"]=s
s=updated["studio_mcp/node/studio-flow-rpc.mjs"]
a=s.index('  if(!/[\\\\/]') if '  if(!/[\\\\/]' in s else s.index('  if(!/[')
b=s.index('  const localOutput=',a)
s=s[:a]+r'''  const studioRoot=path.resolve(here,'..','..');
  const ident=String(process.env.STORYBOARD_MCP_ACCOUNT_ID||'');
  const portable=/^account_[0-9a-f]{12}$/.test(ident);
  const canonical=(p)=>fs.existsSync(p)?fs.realpathSync(p):path.resolve(p);
  const same=(a,b)=>canonical(a).toLowerCase()===canonical(b).toLowerCase();
  const portableProfile=portable&&same(profile,path.join(studioRoot,'flow_accounts',ident));
  const portableState=portable&&same(state,path.join(studioRoot,'flow_accounts',ident+'_state'));
  if((!/[\\\/]\.storyboard-studio-(?:private-chrome-default|private-chrome-accounts|flow-accounts)(?:[\\\/]|$)/i.test(profile) && !portableProfile) ||
     (!/[\\\/]\.storyboard-studio-(?:private-state-default|private-mcp-accounts|flow-mcp|flow-accounts)(?:[\\\/]|$)/i.test(state) && !portableState))
     throw Error('STORYBOARD_PRIVATE_PROFILE_REQUIRED');
'''+s[b:]
updated["studio_mcp/node/studio-flow-rpc.mjs"]=s
s=updated["studio_mcp/auto_flow_manager.py"]
s=s.replace('from .accounts import (active_account,','from .accounts import (AccountError, active_account,',1)
s=s.replace('except (BaselineDriftError,ProjectError,ValueError,OSError) as exc:','except (BaselineDriftError,ProjectError,AccountError,ValueError,OSError) as exc:',1)
updated["studio_mcp/auto_flow_manager.py"]=s
s=updated["flow_account_manager.py"]
a=s.index('def get_ui_status()')
b=s.index('        account = active_account()',a)
s=s[:b]+s[b:].replace('        account = active_account()','        account = active_account()\n        from studio_mcp.transport import _isolated\n        _isolated(account)',1)
updated["flow_account_manager.py"]=s
for n,text in updated.items():
 if n.endswith(".py"):compile(text,str(root/n),"exec")
 forparent=cp/n;forparent.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/n,forparent)
staged=cp/"after"
for n,text in updated.items():
 p=staged/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding="utf-8")
check=subprocess.run([r"C:\Program Files\nodejs\node.exe","--check",str(staged/"studio_mcp/node/studio-flow-rpc.mjs")],capture_output=True,text=True)
assert check.returncode==0,check.stderr
try:
 for n,text in updated.items():(root/n).write_text(text,encoding="utf-8")
 results=[]
 for cmd in [
  [str(root/"runtime/python/python.exe"),"-B",str(root/"tests/test_studio_portable_account_paths.py")],
  [r"C:\Program Files\nodejs\node.exe",str(root/"tests/test_studio_portable_node_paths.cjs")],
  [str(root/"runtime/python/python.exe"),"-B",str(root/"tests/test_flowkit_removed_offline.py")],
  [r"C:\Program Files\nodejs\node.exe",str(root/"tests/test_mcp_v2_status_ui.cjs")],
 ]:
  test=subprocess.run(cmd,cwd=root,capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=60)
  (cp/(pathlib.Path(cmd[-1]).name+".log")).write_text(test.stdout+test.stderr,encoding="utf-8")
  print(pathlib.Path(cmd[-1]).name,test.returncode)
  if test.returncode:print(test.stdout+test.stderr);raise RuntimeError("REGRESSION_FAILED")
except Exception:
 for n in names:shutil.copy2(cp/n,root/n)
 raise
print(json.dumps({"checkpoint":str(cp),"files":names,"python_tests":16,"node_path_cases":5,"ui_states":3}))
