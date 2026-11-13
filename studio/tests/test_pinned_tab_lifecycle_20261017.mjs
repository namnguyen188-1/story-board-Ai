import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import path from 'node:path';
const source=fs.readFileSync(new URL('../studio_mcp/node/production-job-tab.mjs',import.meta.url),'utf8');
const url='https://flow.google.com/project/11111111-1111-1111-1111-111111111111/tool/22222222-2222-2222-2222-222222222222';
const id='A'.repeat(32);
for(const action of ['create','close','abandon']){
 let opened=0,closed=0,output='';
 const frame={evaluate:async()=>true};
 const page={isClosed:()=>false,url:()=>url,frames:()=>[frame],waitForTimeout:async()=>{},close:async()=>{closed++}};
 const context={pages:()=>[page],newPage:async()=>{opened++;throw Error('Unexpected new tab')},
  newCDPSession:async()=>({send:async()=>({targetInfo:{targetId:id}}),detach:async()=>{}})};
 const browser={contexts:()=>[context]};
 const sandbox=vm.createContext({URL,Promise,Error,Number,String,JSON,console,
  process:{exitCode:0,stdout:{write:(s,cb)=>{output+=s;cb?.()}},exit:()=>{}},setTimeout});
 const mod=new vm.SourceTextModule(source,{context:sandbox});
 await mod.link(async name=>{
  if(name==='node:url')return new vm.SyntheticModule(['fileURLToPath'],function(){this.setExport('fileURLToPath',()=>String(new URL('../studio_mcp/node/production-job-tab.mjs',import.meta.url)))},{context:sandbox});
  const value=name==='node:fs'?{readFileSync:()=>JSON.stringify({action,port:9550,tool_url:url,target_id:id})}:name==='node:path'?path:{connectOverCDP:async()=>browser};
  const exported=name.startsWith('node:')?'default':'chromium';
  return new vm.SyntheticModule([exported],function(){this.setExport(exported,value)},{context:sandbox});
 });
 await mod.evaluate();
 const result=JSON.parse(output.trim().split('\n').at(-1));
 assert.equal(result.ok,true,action+': '+output);
 assert.equal(opened,0,'production must borrow the connected tab');
 assert.equal(closed,0,'production must keep the connected tab open');
 if(action==='create')assert.equal(result.target_id,id);
 console.log('PASS',action,'same target, no page creation/closure');
}
