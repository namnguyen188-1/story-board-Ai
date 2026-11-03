const {chromium}=require('D:/STORYBOARD_AI/studio/studio_mcp/node/node_modules/playwright-core');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',args:['--no-first-run']});
 try{
 const page=await browser.newPage({viewport:{width:1366,height:900}});
 const errors=[];page.on('pageerror',e=>errors.push(String(e.message)));
 await page.goto('http://127.0.0.1:8765/',{waitUntil:'domcontentloaded',timeout:30000});
 await page.locator('#btnModeDrama').click();
 await page.locator('#inSeries').fill('THIÊN SƯ: HUYỀN PHÙ TRẤN QUỶ');
 await page.locator('#inEpisode').fill('1');
 await page.evaluate(async()=>{const status=await fetch('/api/status').then(r=>r.json());window.__reviewTestStatus=status;});
 const status=await page.evaluate(()=>({stage:window.__reviewTestStatus.stage,exit_code:window.__reviewTestStatus.exit_code}));
 await page.locator('#btnDramaAssetReview').click();
 await page.locator('#dramaAssetReviewModal article').first().waitFor({state:'visible',timeout:15000});
 const cards=await page.locator('#dramaAssetReviewModal article').count();
 console.log('ASSET_REVIEW_LIVE_PAUSE',JSON.stringify({status,cards,problems:errors}));
 if(status.stage!=='AWAITING_ASSET_REVIEW'||cards!==17||errors.length)throw Error('Unexpected review pause/UI');
 }finally{await browser.close();}
})().catch(e=>{console.error('LIVE_REVIEW_PAUSE_TEST_FAIL',e.stack);process.exit(1)});
