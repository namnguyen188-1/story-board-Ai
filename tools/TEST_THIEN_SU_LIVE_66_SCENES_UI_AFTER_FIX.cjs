const {chromium}=require('D:/STORYBOARD_AI/studio/studio_mcp/node/node_modules/playwright-core');
(async()=>{
const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',args:['--no-first-run']});
try{
 const page=await browser.newPage({viewport:{width:1400,height:850}});
 const errors=[];page.on('pageerror',x=>errors.push(String(x.message)));
 await page.goto('http://127.0.0.1:8765/',{waitUntil:'domcontentloaded',timeout:30000});
 await page.locator('#btnModeDrama').click();
 await page.locator('#inSeries').fill('THIÊN SƯ: HUYỀN PHÙ TRẤN QUỶ');
 await page.locator('#inEpisode').fill('1');
 await page.waitForFunction(()=>document.getElementById('timelineDurationText')?.textContent?.includes('11:00'),null,{timeout:20000});
 const result=await page.evaluate(()=>({
   project:document.getElementById('headerProjectName')?.textContent,
   sceneCount:document.querySelectorAll('.scene-time-pill').length,
   firstSceneDuration:document.querySelector('.scene-time-pill')?.textContent,
   timeline:document.getElementById('timelineDurationText')?.textContent,
   sceneImageCount:document.querySelectorAll('img[src*="/api/drama/assets/photo"]').length,
   minutes:document.getElementById('inMinutes')?.value,
   seconds:document.getElementById('inSceneSec')?.value
 }));
 console.log('HEADLESS_LIVE_DRAMA_BOARD_CHECK',JSON.stringify(result),'PAGE_ERRORS',errors.slice(0,4));
 if(result.sceneCount!==66||!result.firstSceneDuration?.includes('10s')||!result.timeline?.includes('11:00')||result.sceneImageCount<10||errors.length)throw Error('Live board regression: '+JSON.stringify(result));
}finally{await browser.close()}
})().catch(e=>{console.error('DRAMA_UI_BOARD_REGRESSION_FAIL',e.stack);process.exit(1)});
