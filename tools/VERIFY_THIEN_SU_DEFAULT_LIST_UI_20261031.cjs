const {chromium}=require('D:/STORYBOARD_AI/studio/studio_mcp/node/node_modules/playwright-core');
(async()=>{const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe'});
try{
 const p=await browser.newPage({viewport:{width:1400,height:850}});const errs=[];
 p.on('pageerror',e=>errs.push(e.message));
 await p.goto('http://127.0.0.1:8765/',{waitUntil:'domcontentloaded',timeout:25000});
 await p.locator('#btnModeDrama').click();
 await p.locator('#inSeries').fill('THIÊN SƯ: HUYỀN PHÙ TRẤN QUỶ');
 await p.locator('#inEpisode').fill('1');
 await p.waitForFunction(()=>document.getElementById('scenesContainer')?.classList.contains('view-list') &&
   document.getElementById('timelineDurationText')?.textContent.includes('11:00'),null,{timeout:22000});
 const summary=await p.evaluate(()=>({series:document.getElementById('headerProjectName')?.textContent,
 list:document.getElementById('scenesContainer')?.classList.contains('view-list'),
 count:document.querySelectorAll('.scene-time-pill').length,
 sceneSeconds:document.querySelector('.scene-time-pill')?.textContent,
 thumbnails:document.querySelectorAll('img[src*="/api/drama/assets/photo"]').length,
 total:document.getElementById('timelineDurationText')?.textContent,
 minuteInput:document.getElementById('inMinutes')?.value}));
 console.log('FINAL_DRAMA_UI_TEST',JSON.stringify(summary),'JS_ERRORS',JSON.stringify(errs));
 if(summary.count!==66||!summary.list||!summary.total?.includes('11:00')||summary.thumbnails<15||errs.length)throw Error('LIVE_UI_ASSERTION_FAILED');
}finally{await browser.close()}})().catch(e=>{console.error('FAILED',e.stack);process.exit(1)});
