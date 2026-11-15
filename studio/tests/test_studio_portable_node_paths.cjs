const fs=require("node:fs"),path=require("node:path"),vm=require("node:vm"),assert=require("node:assert/strict");
const root=path.resolve(__dirname,".."),here=path.join(root,"studio_mcp","node");
const raw=fs.readFileSync(path.join(here,"studio-flow-rpc.mjs"),"utf8");
const source=raw.split("\n").filter(l=>!l.startsWith("import ")).join("\n").replace(/^const here =.*$/m,"const here = "+JSON.stringify(here)+";");
const id="account_ee27d30a0c7f",tool="https://flow.google.com/project/11111111-1111-4111-8111-111111111111/tool/22222222-2222-4222-8222-222222222222";
async function check(extra){
 let stdout="";
 const env={FLOW_MCP_USER_DATA_DIR:path.join(process.env.USERPROFILE,".storyboard-studio-flow-accounts","account_b61dbd4f7ab7"),FLOW_MCP_STATE_DIR:path.join(root,"flow_accounts",id+"_state"),FLOW_MCP_CDP_PORT:"9461",STORYBOARD_MCP_OUTPUT_ROOT:path.join(root,"runtime","private_mcp_outputs"),STORYBOARD_STUDIO_TOOL_URL:tool,STORYBOARD_MCP_ACCOUNT_ID:id,...extra};
 const req=JSON.stringify({name:"flow_storyboard_native_image",arguments:{action:"health",tool_url:tool}});
 const sandbox={fs:{...fs,readFileSync(fd,...rest){return fd===0?req:fs.readFileSync(fd,...rest)}},path,process:{env,stdout:{write(v){stdout+=v}},execPath:process.execPath},StdioClientTransport:class{constructor(){throw Error("OFFLINE_GUARDS_ACCEPTED")}},setTimeout};
 await vm.runInNewContext("(async()=>{"+source+"\n})()",sandbox);
 return JSON.parse(stdout).code;
}
(async()=>{
 assert.equal(await check({}),"OFFLINE_GUARDS_ACCEPTED");
 assert.equal(await check({FLOW_MCP_USER_DATA_DIR:path.join(root,"flow_accounts",id)}),"OFFLINE_GUARDS_ACCEPTED");
 assert.match(await check({FLOW_MCP_STATE_DIR:path.join(root,"flow_accounts","account_aaaaaaaaaaaa_state")}),/PROFILE_REQUIRED/);
 assert.match(await check({FLOW_MCP_STATE_DIR:"D:\\FLOW_MCP_SERVER\\runtime"}),/PROFILE_REQUIRED/);
 assert.match(await check({FLOW_MCP_CDP_PORT:"9333"}),/CDP_PORT_REQUIRED/);
 console.log("NODE_PORTABLE_ACCOUNT_PATH_GUARDS_5_PASS_NO_MCP_LAUNCH");
})().catch(e=>{console.error(e);process.exitCode=1});
