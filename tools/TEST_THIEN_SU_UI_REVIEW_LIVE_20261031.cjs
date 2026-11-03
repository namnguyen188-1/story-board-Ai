const {chromium}=require('D:/STORYBOARD_AI/studio/studio_mcp/node/node_modules/playwright-core');
(async()=>{
const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',args:['--no-first-run']});
try{
 const page=await browser.newPage({viewport:{width:1366,height:900}});
 const problems=[];
 page.on('pageerror',e=>problems.push(e.message));
 await page.goto('http://127.0.0.1:8765/',{waitUntil:'domcontentloaded',timeout:30000});
 await page.locator('#btnModeDrama').click();
 await page.locator('#inSeries').fill('THIÊN SƯ: HUYỀN PHÙ TRẤN QUỶ');
 await page.locator('#inEpisode').fill('1');
 await page.locator('#btnDramaAssetReview').waitFor({state:'visible',timeout:15000});
 await page.locator('#btnDramaAssetReview').click();
 await page.locator('#dramaAssetReviewModal article').first().waitFor({state:'visible',timeout:20000});
 const count=await page.locator('#dramaAssetReviewModal article').count();
 const imgs=await page.locator('#dramaAssetReviewModal article img').count();
 const header=await page.locator('#dramaAssetReviewModal').innerText();
 const status=await page.evaluate(async()=>{const r=await fetch('/api/status');const x=await r.json();return {running:x.running,stage:x.stage};});
 console.log('THIEN_SU_REAL_UI_REVIEW_PASS',JSON.stringify({cards:count,images:imgs,header:header.slice(0,260),status,problems:problems.slice(0,4)}));
 if(count!==17||imgs!==17)throw Error('Expected exactly 17 real asset cards');
}finally{await browser.close()}
})().catch(e=>{console.error('HEADLESS_APP_REVIEW_FAIL',e.stack);process.exit(1)});
