const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");
const source = fs.readFileSync(path.resolve(__dirname, "../../studio/web/app.js"),"utf8");
const start = source.indexOf("let onlineUpdatePolling = false;");
const end = source.indexOf("// END ONLINE UPDATE UI",start);
assert(start>=0 && end>start,"Update button must follow progress instead of resetting after 12 seconds");
const script=source.slice(start,end);
async function run(states) {
  const seen=[]; const toasts=[]; let text=""; let reloads=0;
  const button={disabled:false,dataset:{},title:"",setAttribute(){},set textContent(v){text=v;seen.push(v)},get textContent(){return text}};
  const storage=new Map();
  const context=vm.createContext({
    document:{getElementById:()=>button},
    window:{addEventListener(){}},
    sessionStorage:{setItem:(k,v)=>storage.set(k,v),removeItem:k=>storage.delete(k),getItem:k=>storage.get(k)},
    location:{reload:()=>reloads++},
    setTimeout:fn=>{fn();return 1},
    showToast:(...args)=>toasts.push(args),
    fetch:async(url)=> {
      if(url.endsWith("/start"))return {ok:true,json:async()=>({success:true})};
      const next=states.shift();
      if(next instanceof Error)throw next;
      assert(next,"Unexpected extra status poll");
      return {ok:true,json:async()=>next};
    }
  });
  vm.runInContext(script,context);
  await context.startOnlineUpdate();
  return {seen,toasts,button,reloads,storage};
}
(async()=>{
  let r=await run([{state:"downloading",percent:42},{state:"installing"},{state:"completed",version:"1.3.5"}]);
  assert(r.seen.some(s=>s.includes("42%")));
  assert(r.seen.some(s=>s.includes("cài")));
  assert.equal(r.reloads,1); assert.equal(r.button.disabled,false); assert.equal(r.storage.size,0);
  r=await run([{state:"failed",message:"SHA256 mismatch"}]);
  assert(r.button.textContent.includes("Lỗi cập nhật")); assert(r.button.title.includes("SHA256")); assert.equal(r.reloads,0);
  r=await run([new Error("server restarting"),{state:"completed",version:"1.3.5"}]);
  assert(r.seen.some(s=>s.includes("khởi động lại"))); assert.equal(r.reloads,1);
  process.stdout.write("ONLINE_UPDATE_UI_TESTS_PASS\n");
})().catch(err=>{console.error(err);process.exitCode=1});
