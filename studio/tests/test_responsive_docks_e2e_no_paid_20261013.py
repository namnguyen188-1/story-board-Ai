"""Real Edge viewport and navigation regression, no paid API or UI production."""
from playwright.sync_api import sync_playwright
import json
with sync_playwright() as p:
    b=p.chromium.launch(channel="msedge",headless=True)
    for w,h in ((1920,1080),(1440,900),(1280,800),(1024,768),(800,650),(540,850)):
        page=b.new_page(viewport={"width":w,"height":h})
        errors=[]
        page.on("pageerror",lambda x: errors.append(str(x)))
        page.goto("http://127.0.0.1:8765",wait_until="domcontentloaded",timeout=22000)
        page.wait_for_function("state.statusReady",timeout=12000)
        if w<=800:
            page.locator(".dock-tab-setup").click()
            page.locator(".col-control").wait_for(state="visible",timeout=2200)
        page.locator("#inSeries").fill("UI-QA-NO-PRODUCTION")
        if w<=800:
            page.locator(".dock-tab-scenes").click()
            page.locator(".col-control").wait_for(state="hidden",timeout=2200)
        for item in range(62):
            page.locator("#scenesContainer").evaluate("""(root,i)=>{
              const card=document.createElement('div');
              card.className='scene-card';
              const thumb=document.createElement('div');
              thumb.className='scene-thumb-wrap';
              const detail=document.createElement('div');
              detail.className='scene-card-title';
              detail.textContent='Phân cảnh '+(i+1)+' — A long storyline that must remain readable';
              card.append(thumb,detail);root.append(card)
            }""",item)
        measured=page.evaluate("""() => {
          const sels=['.workspace','.col-control','.col-storyboard','.col-monitor','.header','.header-tools','#scenesContainer','.scene-card'];
          const o={};
          for(const name of sels){
            const e=document.querySelector(name);const r=e.getBoundingClientRect();
            o[name]={x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height),
              visible:getComputedStyle(e).visibility!=='hidden'};
          }
          const first=document.querySelector('.scene-card');
          const second=first.nextElementSibling;
          return {vw:innerWidth,scrollWidth:document.documentElement.scrollWidth,
            workspaceOverflow:document.querySelector('.workspace').scrollWidth-document.querySelector('.workspace').clientWidth,
            scenes:document.querySelector('#scenesContainer').children.length,
            cardsPerRow:Math.round(document.querySelector('#scenesContainer').clientWidth/first.getBoundingClientRect().width),
            cardFont:getComputedStyle(document.querySelector('.scene-card-title')).fontSize,
            firstSceneWidth:Math.round(first.getBoundingClientRect().width),
            nav:getComputedStyle(document.querySelector('.dock-nav')).display, boxes:o};
        }""")
        assert measured["scenes"]>=62
        assert measured["workspaceOverflow"]<=3,(w,measured)
        assert measured["scrollWidth"]<=w+3,(w,measured)
        assert measured["firstSceneWidth"]>=245,(w,measured)
        if w>=1200:
            assert measured["boxes"][".col-monitor"]["visible"]
            assert measured["boxes"][".col-control"]["visible"]
            assert measured["boxes"][".col-storyboard"]["visible"]
        else:
            assert measured["nav"]!="none"
            assert not measured["boxes"][".col-monitor"]["visible"]
            page.locator(".dock-tab-monitor").click()
            assert page.locator("body").get_attribute("data-dock")=="monitor"
            page.locator(".col-monitor").wait_for(state="visible",timeout=2200)
            page.locator(".dock-tab-scenes").click()
            page.locator(".col-monitor").wait_for(state="hidden",timeout=2200)
            if w<=800:
                page.locator(".dock-tab-setup").click()
                page.locator(".col-control").wait_for(state="visible",timeout=2200)
                page.locator(".dock-tab-scenes").click()
                page.locator(".col-control").wait_for(state="hidden",timeout=2200)
        assert page.locator("#inSeries").input_value()=="UI-QA-NO-PRODUCTION"
        assert not errors,(w,errors)
        print("LAYOUT_PASS",w,h,"SCENE_CARD",measured["firstSceneWidth"],
              "FONT",measured["cardFont"],"NAV",measured["nav"],
              "PAGE_SCROLL",measured["scrollWidth"],flush=True)
        page.close()
    b.close()
print("MULTI_WIDTH_NO_OVERLAP_AND_SWITCH_PASS",flush=True)
