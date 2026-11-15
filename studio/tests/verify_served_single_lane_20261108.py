import urllib.request,re,json
base="http://127.0.0.1:8765"
html=urllib.request.urlopen(base+"/",timeout=5).read().decode("utf8")
js=urllib.request.urlopen(base+"/app.js",timeout=5).read().decode("utf8")
checks={
 "html_hidden_worker_1": 'id="inWorkers" value="1"' in html,
 "html_one_lane_active": bool(re.search(r'class="[^"]*worker-chip active-chip[^"]*" data-val="1"',html)),
 "html_multi_disabled": all(bool(re.search(r'data-val="'+str(v)+r'" disabled',html)) for v in (2,4,6,8)),
 "script_pinned_1": 'const savedWorkers = "1";' in js,
 "script_worker_set_1": 'const t = 1; // single-lane stability mode' in js,
 "script_produce_and_queue_1": js.count('workers: 1')==2 and 'const workers = 1;' in js,
}
print(json.dumps(checks))
if not all(checks.values()):raise SystemExit(1)
