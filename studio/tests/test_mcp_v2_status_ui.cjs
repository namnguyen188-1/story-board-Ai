const fs=require("node:fs"),vm=require("node:vm"),assert=require("node:assert/strict"),path=require("node:path");
const root=path.resolve(__dirname,".."),source=fs.readFileSync(path.join(root,"web","app.js"),"utf8");
const start=source.indexOf("function updateFlowKitUI(data) {"),end=source.indexOf("\nasync function refreshAutoFlowStatus",start);
assert(start>=0&&end>start);
const nodes=new Map();
const document={getElementById(id){if(!nodes.has(id))nodes.set(id,{textContent:"",innerHTML:"",style:{}});return nodes.get(id)}};
const context=vm.createContext({document,Boolean});
vm.runInContext(source.slice(start,end),context);
for(const [ready,connected,want] of [[true,true,"MCP V2: đã kết nối"],[false,true,"MCP V2: cần đăng nhập"],[false,false,"MCP V2: chưa kết nối"]]){
 document.getElementById("autoFlowManagerStatus").textContent="🟢";
 context.updateFlowKitUI({provider:"mcp_v2",ready,connected,badge_text:want,status_text:"MCP V2 · kết nối; chưa kiểm tra tạo nội dung."});
 assert.equal(document.getElementById("flowkitLiveStatusBadge").textContent,want);
 assert.equal(document.getElementById("flowkitStatusBox").textContent,"MCP V2 · kết nối; chưa kiểm tra tạo nội dung.");
 assert(!/FlowKit|18110/.test(document.getElementById("statusFlowKit").textContent));
}
console.log("MCP_V2_STATUS_UI_THREE_STATES_PASS");
