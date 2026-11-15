import ast,json,pathlib,shutil,subprocess,re
root=pathlib.Path(r"D:\STORYBOARD_AI\studio")
cp=root/"runtime/mcp_v2_only_20261108_102327"
p=root/"series_studio.py";s=p.read_text(encoding="utf-8-sig")
shutil.copy2(p,cp/p.name)
s=s.replace('choices=["gemini","v2_tuanstor","mcp_v2","comfyui","muse_video","flowkit"]','choices=["gemini","v2_tuanstor","mcp_v2","comfyui","muse_video"]')
a=s.index('r.add_argument("--image-provider"');b=s.index('r.add_argument("--mcp-model-index"',a)
block=s[a:b];assert 'default="comfyui"' in block
s=s[:a]+block.replace('default="comfyui"','default="mcp_v2"')+s[b:]
a=s.index('            if job.get("image_provider") == "flowkit":');b=s.index('            elif job.get("image_provider") == "mcp_v2":',a)
s=s[:a]+'''            if job.get("image_provider") == "flowkit":
                raise RuntimeError("FLOWKIT_REMOVED_SELECT_MCP_V2")
'''+s[b:]
a=s.index('    if args.mode=="live" and args.image_provider=="flowkit":');b=s.index('    elif args.mode=="live" and args.image_provider=="mcp_v2":',a)
s=s[:a]+'''    if args.mode=="live" and args.image_provider=="flowkit":
        raise RuntimeError("FLOWKIT_REMOVED_SELECT_MCP_V2")
'''+s[b:]
compile(s,str(p),"exec");p.write_text(s,encoding="utf-8")
test=subprocess.run([str(root/"runtime/python/python.exe"),"-B",str(root/"tests/test_flowkit_removed_offline.py")],capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=60,cwd=root)
(cp/"routing_tests.txt").write_text(test.stdout+test.stderr,encoding="utf-8")
if test.returncode:shutil.copy2(cp/p.name,p)
print(test.stdout+test.stderr)
assert test.returncode==0
(cp/"after"/p.name).write_text(s,encoding="utf-8")
report=json.loads((cp/"migration_result.json").read_text());report["files"].append(p.name);report["tests"]="9/9 offline"
(cp/"migration_result.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
