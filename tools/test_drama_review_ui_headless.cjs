const {chromium}=require('D:/STORYBOARD_AI/studio/studio_mcp/node/node_modules/playwright-core');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',args:['--no-first-run']});
 try {
   const page=await browser.newPage({viewport:{width:1366,height:900}});
   await page.goto('http://127.0.0.1:8766/',{waitUntil:'domcontentloaded',timeout:30000});
   await page.locator('#btnModeDrama').click();
   await page.locator('#inSeries').fill('multi_role_asset_first_e2e');
   await page.locator('#inEpisode').fill('6');
   await page.locator('#btnDramaAssetReview').waitFor({state:'visible',timeout:15000});
   await page.locator('#btnDramaAssetReview').click();
   await page.locator('#dramaAssetReviewModal article').first().waitFor({state:'visible',timeout:15000});
   const count=await page.locator('#dramaAssetReviewModal article').count();
   const summary=await page.locator('#dramaAssetReviewModal div').filter({hasText:'13/13 bộ ảnh'}).first().textContent();
   console.log('ASSET_REVIEW_UI_HEADLESS_PASS',count,'assets','hint:',summary?.slice(0,200));
   if(count!==13)throw Error('Expected 13 review cards');
 }finally{await browser.close();}
})().catch(e=>{console.error('ASSET_REVIEW_UI_TEST_FAILED',e.message);process.exit(1)});
