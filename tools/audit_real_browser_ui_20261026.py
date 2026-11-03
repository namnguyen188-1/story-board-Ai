# -*- coding: utf-8 -*-
"""Real headless UI E2E, read/control only; never press Produce, Queue, Upload, Update."""
from pathlib import Path
import json,time,sys
from playwright.sync_api import sync_playwright
ROOT=Path(r"D:\STORYBOARD_AI\studio")
RESULT=ROOT/"diagnostics"/"audit_browser_ui_20261026.json"
modes=["flow_video","color_cinematic","color_animation","colored_marker","hand_color","whiteboard"]
results=[]
with sync_playwright() as p:
    browser=p.chromium.launch(channel="msedge",headless=True, args=["--disable-background-networking"])
    for w,h in [(1366,768),(540,850)]:
        context=browser.new_context(viewport={"width":w,"height":h},locale="vi-VN")
        page=context.new_page()
        errors=[]
        page.on("pageerror", lambda err: errors.append(str(err)[:200]))
        response=page.goto("http://127.0.0.1:8765",wait_until="domcontentloaded",timeout=18000)
        page.wait_for_function("typeof window.setProductionModeUI === 'function'",timeout=14000)
        data=page.evaluate("""(modes)=>{
          const id=x=>document.getElementById(x);
          const style=id('inVisualStyle'), genre=id('inGenre');
          const options=[...style.options].map(x=>x.value);
          const got=[];
          window.setProductionModeUI('cinematic_drama');
          genre.value='animation';genre.dispatchEvent(new Event('change',{bubbles:true}));
          for(const mode of modes){
            style.value=mode;style.dispatchEvent(new Event('change',{bubbles:true}));
            got.push({mode,selected:style.value,production:id('inProductionMode').value,
              genre:genre.value});
          }
          window.setProductionModeUI('narrative');
          return {options,got,ending_mode:id('inProductionMode').value,
            has_voice:!!id('inVoice'),has_language:!!id('inLanguage'),
            has_produce_button:!!id('btnLive'),has_series:!!id('inSeries')};
        }""",modes)
        good=all(x["selected"]==x["mode"] and x["production"]=="cinematic_drama"
                 and x["genre"]=="animation" for x in data["got"])
        results.append({"viewport":f"{w}x{h}","http":response.status if response else None,
                       "styles_ok":good,"errors":errors[:10],"control_data":data})
        context.close()
    browser.close()
RESULT.write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding="utf-8")
for r in results:
 print("UI_VIEW",r["viewport"],"HTTP",r["http"],"STYLE_6",r["styles_ok"],
       "JS_ERRORS",len(r["errors"]),"PRODUCE_BUTTON_PRESENT",r["control_data"]["has_produce_button"],flush=True)
print("SAVED",RESULT,flush=True)
