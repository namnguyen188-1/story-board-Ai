const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const appPath = process.argv[2] || path.join(__dirname, '..', 'web', 'app.js');
const source = fs.readFileSync(appPath, 'utf8');
const start = source.indexOf('async function submitProduction(');
const end = source.indexOf('  state.submitting = true;', start);
assert(start >= 0 && end > start);
const code = source.slice(start, end) + '  return payload;\n}\nsubmitProduction("live")';
async function check(productionMode, inputMode, expectedSec) {
  const values = {
    inSeries:'DRAMA', inEpisode:'3', inInputMode:inputMode,
    inPrompt:inputMode === 'link' ? 'REFERENCE analysis after scan' : 'A family drama',
    inReferenceUrl:'https://www.youtube.com/watch?v=abcdefghijk',
    inImageSource:'muse_video', inMinutes:'6.6', inSceneSec:'8',
    inProductionMode:productionMode, inLanguage:'English', inVoice:'Orus',
    inGenre:'family_drama', inVisualStyle:'cinematic', inResolution:'1280x720',
    inModel:'gemini', inMcpMaxImages:'40'
  };
  const el = new Proxy({}, {get: (_, key) => key in values ? {value:values[key]} : null});
  const payload = await vm.runInNewContext(code, {
    state:{statusReady:true,isRunning:false,submitting:false}, el,
    document:{getElementById:()=>null}, estimatedImageScenes:()=>40,
    alert:msg=>{throw new Error(msg)}
  });
  assert.equal(payload.scene_seconds, expectedSec);
  assert.equal(payload.production_mode, productionMode);
  assert.equal(payload.image_provider, 'muse_video');
  if (inputMode === 'link') assert.equal(payload.reference_url, values.inReferenceUrl);
  console.log('PASS ' + productionMode + ' / ' + inputMode + ' / scene_seconds=' + expectedSec);
}
(async()=>{
  let failures=0;
  for (const args of [['cinematic_drama','link',10],['cinematic_drama','idea',10],['narrative','link',8]]) {
    try { await check(...args); }
    catch (e) { failures++; console.error('FAIL ' + args.join(' / ') + ': ' + e.message); }
  }
  process.exitCode=failures ? 1 : 0;
})();
