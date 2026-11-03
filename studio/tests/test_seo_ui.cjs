const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '..', 'web', 'app.js'), 'utf8');
const begin = source.indexOf('window.renderSeoPackageUI = function');
const end = source.indexOf('window.currentSeoTab = ', begin);
const nodes = new Map();
function element(id) {
  if (!nodes.has(id)) nodes.set(id, {textContent:'', innerHTML:'', value:'', style:{}, classList:{add(){},remove(){}}});
  return nodes.get(id);
}
const context = { window:{switchSeoPackTab(){}}, state:{}, el:{},
  document:{getElementById:element}, escapeHtml:v=>String(v??''), currentSeoData:null };
vm.createContext(context);
vm.runInContext(source.slice(begin,end), context);
const pack={language:'English',series:'DRAMA',episode:3,metadata_checks:{source:'internal_checklist',total_score:0,max_score:100,rating:'Kiểm tra nội bộ: 0/100',breakdown:[]},
  vidiq_score:{source:'internal_checklist',total_score:0,max_score:100,rating:'Kiểm tra nội bộ: 0/100',breakdown:[]},
  official_vidiq:{total_score:null}, titles:[{title:'HOA Tow Warning',char_count:15}], tags:[],
  thumbnail_checks:{total_score:0,source:'internal_technical_checklist',breakdown:[]},
  thumbnail_vidiq_scorecard:{total_score:0,breakdown:[]},thumbnail_options:[],shorts_package:null};
context.window.renderSeoPackageUI(pack);
assert.equal(element('vidiqScoreNumber').textContent,0,'zero must not become 100');
assert(!element('seoTitlesContainer').innerHTML.includes('14-18%'),'no invented CTR');
assert(!element('seoTitlesContainer').innerHTML.includes('10/10'),'no default perfect title score');
assert(element('vidiqPerformanceBadge').textContent.includes('chưa'),'unknown performance stays unknown');
assert.equal(element('seoThumbnailPreview').style.display,'none','missing thumbnail clears old preview');
assert.equal(element('seoThumbnailGallery').innerHTML,'','empty options clear old gallery');
console.log('PASS SEO renderer: zero, null, title claims, missing image and empty gallery');
