import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import path from 'node:path';
const here=path.resolve(path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/,'$1')),'..','studio_mcp','node');
const source=fs.readFileSync(path.join(here,'production-job-tab.mjs'),'utf8');
const url='https://flow.google.com/project/11111111-1111-4111-8111-111111111111/tool/22222222-2222-4222-8222-222222222222';
const account='account_ee27d30a0c7f',id='A'.repeat(32),studio=path.resolve(here,'..','..');
async function run(state,account_id=account){
 let output='',generated=0,cleared=0,opened=0,closed=0;const archives=[];
 const initial=[{id:'shot_1',status:'pending',promptText:'Preserve this original unsent draft',assetKind:'video'}];
 const api={queue:JSON.parse(JSON.stringify(initial)),isProcessing:false,capabilities:{addToQueue(){},startImageProduction(){generated++},clearQueue(){cleared++;api.queue=[]}}};
 const frame={evaluate:async(fn,arg)=>{
  const body=String(fn).replace("import('flow-sdk')","Promise.resolve(fakeSdk)");
  return await vm.runInNewContext('('+body+')(arg)',{window:{__STORYBOARD_MCP__:api},arg,fakeSdk:{Flow:{generate:{image(){generated++}}}}});
 }};
 const page={isClosed:()=>false,url:()=>url,frames:()=>[frame],close:async()=>{closed++}};
 const context={pages:()=>[page],newPage:async()=>{opened++;throw Error('UNEXPECTED_TAB')},newCDPSession:async()=>({send:async()=>({targetInfo:{targetId:id}}),detach:async()=>{}})};
 const req={action:'create',port:9461,tool_url:url,state_dir:state,account_id};
 const fakefs={...fs,readFileSync:()=>JSON.stringify(req),mkdirSync(){},writeFileSync(p,data,options){archives.push({p,data,options});}};
 const sandbox=vm.createContext({URL,Promise,Error,Number,String,JSON,console,process:{exitCode:0,stdout:{write:(s,cb)=>{output+=s;cb?.()}},exit(){}},setTimeout});
 const mod=new vm.SourceTextModule(source,{context:sandbox,identifier:path.join(here,'production-job-tab.mjs')});
 await mod.link(async name=>{
  const value=name==='node:fs'?fakefs:name==='node:path'?path:name==='node:url'?{fileURLToPath:()=>path.join(here,'production-job-tab.mjs')}:{connectOverCDP:async()=>({contexts:()=>[context]})};
  const exported=name.startsWith('node:')?'default':'chromium';
  if(name==='node:url')return new vm.SyntheticModule(['fileURLToPath'],function(){this.setExport('fileURLToPath',value.fileURLToPath)},{context:sandbox});
  return new vm.SyntheticModule([exported],function(){this.setExport(exported,value)},{context:sandbox});
 });
 await mod.evaluate();
 const result=JSON.parse(output.trim().split('\n').at(-1));
 return {result,archives,generated,cleared,opened,closed,queue:api.queue,initial};
}
const state=path.join(studio,'flow_accounts',account+'_state');
const good=await run(state);
assert.equal(good.result.ok,true,JSON.stringify(good.result));
assert.equal(good.archives.length,1);
assert.equal(good.archives[0].data,JSON.stringify(good.initial));
assert.equal(good.archives[0].options.flag,'wx');
assert.equal(path.dirname(good.archives[0].p),path.join(state,'pinned_tab_drafts'));
assert.equal(good.generated,0);assert.equal(good.cleared,0);assert.equal(good.opened,0);assert.equal(good.closed,0);
for(const bad of [path.join(studio,'flow_accounts','account_aaaaaaaaaaaa_state'),'D:\\FLOW_MCP_SERVER\\runtime']){
 const denied=await run(bad);assert.equal(denied.result.ok,false);assert.equal(denied.archives.length,0);assert.equal(denied.generated,0);
}
console.log('PRODUCTION_DRAFT_ARCHIVE_PORTABLE_STATE_PASS_ZERO_GENERATION');