/* Multi-role cinematic drama: explicit, compact visual asset approval UI.
 * Does not change narrative/SEO/clone modes. Does not auto-approve.
 */
(() => {
  const init = () => {
    const mode = document.getElementById("inProductionMode");
    const drama = document.getElementById("btnModeDrama");
    if (!mode || !drama || document.getElementById("btnDramaAssetReview")) return;
    const trigger = document.createElement("button");
    trigger.id = "btnDramaAssetReview";
    trigger.type = "button";
    trigger.textContent = "🖼 Duyệt ảnh nhân vật · bối cảnh · đạo cụ";
    trigger.style.cssText = "margin-top:7px;width:100%;display:none;padding:7px 10px;border:1px solid #334155;border-radius:7px;background:#151e31;color:#e2e8f0;cursor:pointer;font-size:12px;font-weight:600;";
    drama.parentElement.parentElement.appendChild(trigger);
    const shade = document.createElement("div");
    shade.id = "dramaAssetReviewModal";
    shade.style.cssText = "position:fixed;inset:0;z-index:9800;background:rgba(0,0,0,.8);display:none;align-items:center;justify-content:center;padding:20px;";
    const shell = document.createElement("section");
    shell.style.cssText = "background:#0f172a;color:#e5e7eb;border:1px solid #475569;border-radius:12px;max-width:1000px;width:100%;max-height:92vh;display:flex;flex-direction:column;overflow:hidden;box-shadow:0 20px 50px #0008;";
    const top = document.createElement("div");
    top.style.cssText = "display:flex;gap:14px;justify-content:space-between;align-items:center;padding:12px 16px;border-bottom:1px solid #334155;";
    const title = document.createElement("strong");
    title.textContent = "Duyệt ảnh tham chiếu — Phim kịch đa vai";
    title.style.fontSize = "15px";
    const close = document.createElement("button");
    close.type = "button";
    close.textContent = "Đóng";
    close.style.cssText = "border:1px solid #334155;padding:7px 14px;border-radius:6px;background:#1e293b;color:white;cursor:pointer;";
    top.append(title,close);
    const hint = document.createElement("div");
    hint.style.cssText = "padding:9px 16px;font-size:12px;color:#cbd5e1;";
    const content = document.createElement("div");
    content.style.cssText = "display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;padding:12px 16px 20px;overflow:auto;";
    shell.append(top,hint,content);
    shade.appendChild(shell);
    document.body.appendChild(shade);
    const current = () => ({
      series: document.getElementById("inSeries")?.value?.trim() || "",
      episode: parseInt(document.getElementById("inEpisode")?.value || "1",10)
    });
    let isFetching = false;
    let activeItem = null;
    const applyMode = () => { trigger.style.display = mode.value === "cinematic_drama" ? "block" : "none"; };
    drama.addEventListener("click",() => setTimeout(applyMode,0));
    document.getElementById("btnModeNarrative")?.addEventListener("click",() => setTimeout(applyMode,0));
    mode.addEventListener("change",applyMode);
    const oldModeSetter = window.setProductionModeUI;
    if (typeof oldModeSetter === "function") {
      window.setProductionModeUI = (...args) => {
        const res = oldModeSetter(...args);
        applyMode();
        return res;
      };
    }
    applyMode();
    const hide = () => { shade.style.display = "none"; };
    close.addEventListener("click",hide);
    shade.addEventListener("click",e => { if(e.target === shade) hide(); });
    const load = async () => {
      if (isFetching) return;
      isFetching = true;
      content.replaceChildren();
      hint.textContent = "Đang đọc bộ ảnh của tập phim trên máy...";
      try {
        const cfg=current();
        const query = new URLSearchParams(cfg);
        const response = await fetch("/api/drama/assets?" + query.toString(),{cache:"no-store"});
        const data = await response.json();
        if(!response.ok || !data.ok) throw Error(data.error || "Chưa có bộ ảnh master cho tập này.");
        const rows = data.assets || [];
        const done = rows.filter(x => x.approved).length;
        hint.textContent = done + "/" + rows.length + " bộ ảnh đã duyệt. Xem 4 góc thật; chỉ duyệt ảnh đúng mặt, phòng và đạo cụ. Ảnh cảnh cũng cần duyệt trước Muse Video.";
        for(const item of rows) {
          const card=document.createElement("article");
          card.style.cssText="min-width:0;border:1px solid #334155;border-radius:8px;background:#111c2e;padding:9px;display:flex;flex-direction:column;gap:7px;";
          const name=document.createElement("strong");
          const kindName={characters:"Nhân vật",locations:"Bối cảnh",props:"Đạo cụ",scene:"Ảnh cảnh"}[item.kind] || item.kind;
          name.textContent = kindName+" · "+item.title;
          name.style.fontSize="12px";
          const img=document.createElement("img");
          img.style.cssText="width:100%;aspect-ratio:16/10;object-fit:contain;background:#25334a;border-radius:5px;";
          if(item.image_url) img.src=item.image_url; else img.alt="Chưa tạo ảnh";
          const state=document.createElement("small");
          state.textContent=item.approved?"✓ Đã duyệt":item.state;
          state.style.color=item.approved?"#86efac":"#fbbf24";
          const btn=document.createElement("button");
          btn.type="button";
          btn.textContent=item.approved?"Hủy duyệt":"Duyệt ảnh này";
          btn.disabled=!item.image_url;
          btn.style.cssText="padding:7px;border:1px solid #475569;border-radius:5px;background:#1e40af;color:white;cursor:pointer;font-weight:600;";
          btn.onclick=async () => {
            if (activeItem) return;
            activeItem = item.kind+"/"+item.id;btn.disabled=true;
            try{
              const r=await fetch("/api/drama/assets/review",{
                method:"POST",headers:{"Content-Type":"application/json"},
                body:JSON.stringify({...cfg,kind:item.kind,id:item.id,approve:!item.approved})
              });
              const reply=await r.json();
              if(!r.ok || !reply.ok) throw Error(reply.error || "Duyệt ảnh thất bại");
              await load();
            }catch(error){ hint.textContent="Lỗi duyệt ảnh: "+error.message; }
            finally{activeItem=null;btn.disabled=false;}
          };
          card.append(name,img,state,btn); content.append(card);
        }
        if(!rows.length) hint.textContent="Chưa có ảnh. Bấm Sản xuất để tạo bộ ảnh master trước.";
      }catch(e){
        hint.textContent="Chưa thể xem ảnh: "+e.message+" — Hãy kiểm tra tập phim và bấm Sản xuất để tạo tài sản trước.";
      }finally{isFetching=false;}
    };
    trigger.addEventListener("click",()=>{shade.style.display="flex";load();});
  };
  if(document.readyState==="loading") document.addEventListener("DOMContentLoaded",init);
  else init();
})();
