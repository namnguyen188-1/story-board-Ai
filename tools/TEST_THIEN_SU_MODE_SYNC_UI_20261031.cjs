const {chromium}=require('D:/STORYBOARD_AI/studio/studio_mcp/node/node_modules/playwright-core');
(async()=>{const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe'});
try{
 const page=await browser.newPage({viewport:{width:1400,height:850}});const issues=[];page.on('pageerror',e=>issues.push(e.message));
 await page.goto('http://127.0.0.1:8765/',{waitUntil:'domcontentloaded',timeout:30000});
 await page.locator('#inSeries').fill('THIÊN SƯ: HUYỀN PHÙ TRẤN QUỶ');
 await page.locator('#inEpisode').fill('1');
 await page.waitForFunction(()=>document.getElementById('inProductionMode')?.value==='cinematic_drama' && document.getElementById('scenesContainer')?.classList.contains('view-list'),null,{timeout:22000});
 const actual=await page.evaluate(()=>({
  mode:document.getElementById('inProductionMode')?.value,
  dramaButtonActive:document.getElementById('btnModeDrama')?.classList.contains('active'),
  imageProvider:document.getElementById('inImageSource')?.value,
  count:document.querySelectorAll('.scene-time-pill').length,
  duration:document.getElementById('timelineDurationText')?.textContent,
  firstSeconds:document.querySelector('.scene-time-pill')?.textContent,
  images:document.querySelectorAll('img[src*="/api/drama/assets/photo"]').length,
  minutes:document.getElementById('inMinutes')?.value
 }));
 console.log('DRAMA_MODE_RESTORED_TEST',JSON.stringify(actual),'JS_ERRORS',issues);
 if(actual.mode!=='cinematic_drama'||!actual.dramaButtonActive||actual.imageProvider!=='muse_video'||actual.count!==66||!actual.duration?.includes('11:00')||actual.images<15||issues.length)throw Error("INVALID_DRAMA_UI");
}finally{await browser.close()}})().catch(e=>{console.error("FAIL",e.stack);process.exit(1)});
