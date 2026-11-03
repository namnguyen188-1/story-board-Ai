const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'..','web','app.js'),'utf8');
const nodes=new Map();
const get=id=>{if(!nodes.has(id))nodes.set(id,{value:'',textContent:'',innerHTML:'',style:{}});return nodes.get(id);};
const requests=[];
const c={window:{},document:{getElementById:get},currentSeoData:{},openModal(){},
  getActiveSeriesAndEpisode:()=>({series:'DRAMA',episode:3}),slugify:x=>x.toLowerCase(),
  escapeHtml:x=>x,renderSeoPackageUI(){},showToast(){},
  fetch:async url=>{requests.push(url);return {ok:true,json:async()=>({series:'DRAMA',episode:3,vidiq_score:{}})};}};
vm.createContext(c);
let failures=0;
(async()=>{
  for(const [name,fn] of [
    ['unknown schedule',()=>{
      const a=source.indexOf('window.getSeoScheduleIso = function');
      const b=source.indexOf('window.syncPrivacyChoice = function',a);
      vm.runInContext(source.slice(a,b),c);
      assert.equal(c.window.getSeoScheduleIso({publishing_schedule:{best_time_today:null}}).iso,null);
    }],
    ['validated API cache',async()=>{
      const a=source.indexOf('window.openSeoModal = async function');
      const b=source.indexOf('window.renderSeoPackageUI = function',a);
      vm.runInContext(source.slice(a,b),c);
      await c.window.openSeoModal(false);
      assert(requests[0].startsWith('/api/episode/seo?'));
      assert.equal(requests.length,1);
    }]
  ]) {
    try { await fn(); console.log('PASS '+name); }
    catch(e){failures++;console.error('FAIL '+name+': '+e.message);}
  }
  process.exitCode=failures?1:0;
})();
