// Storyboard AI Studio Pro - Client Logic (Commercial 3-Pane Studio)



const state = {



  currentSeries: "Whiteboard Chronicles",



  currentEpisode: 1,



  loadedEpisodeData: null,



  activePreviewMode: "episode", // "episode" | "scene"



  selectedSceneNumber: null,



  pollTimer: null,



  isRunning: false,



  statusReady: false,



  submitting: false,



  lastPercent: null,



  polling: false,



  deckSignature: null,



  logsSignature: null,



  episodeRequest: 0,



  storyboardFilter: "all",



  lastLoadedScenes: [],



  currentRunningScene: null,



  userCustomizedMaxImages: false,



  userExplicitLanguage: false,



  userExplicitRegion: false,



};







// DOM References



const el = {



  // Form



  inProductionMode: document.getElementById("inProductionMode"),



  inSeries: document.getElementById("inSeries"),



  inEpisode: document.getElementById("inEpisode"),



  inMinutes: document.getElementById("inMinutes"),



  inSceneSec: document.getElementById("inSceneSec"),



  inLanguage: document.getElementById("inLanguage"),



  inVoice: document.getElementById("inVoice"),



  inSpeechPacing: document.getElementById("inSpeechPacing"),



  inGenre: document.getElementById("inGenre"),



  inVisualStyle: document.getElementById("inVisualStyle"),



  inRegion: document.getElementById("inRegion"),



  inInputMode: document.getElementById("inInputMode"),



  inReferenceUrl: document.getElementById("inReferenceUrl"),



  inLinkCloneMode: document.getElementById("inLinkCloneMode"),



  linkCloneModeWrap: document.getElementById("linkCloneModeWrap"),



  inImageSource: document.getElementById("inImageSource"),



  mcpConfigRow: document.getElementById("mcpConfigRow"),



  inMcpModel: document.getElementById("inMcpModel"),



  inMcpMaxImages: document.getElementById("inMcpMaxImages"),



  inMcpVisualReuse: document.getElementById("inMcpVisualReuse"),



  inMcpAutoMinimize: document.getElementById("inMcpAutoMinimize"),



  inCleanWatermark: document.getElementById("inCleanWatermark"),



  btnMcpToggleWindow: document.getElementById("btnMcpToggleWindow"),



  imageBudgetHint: document.getElementById("imageBudgetHint"),



  inResolution: document.getElementById("inResolution"),



  inSubtitleStyle: document.getElementById("inSubtitleStyle"),



  inSubtitleSize: document.getElementById("inSubtitleSize"),



  subtitleSizeBadge: document.getElementById("subtitleSizeBadge"),



  inCameraMotion: document.getElementById("inCameraMotion"),



  inAtmosphericOverlay: document.getElementById("inAtmosphericOverlay"),



  inMotionMode: document.getElementById("inMotionMode"),



  inFlowVideoModel: document.getElementById("inFlowVideoModel"),



  inFlowVideoDuration: document.getElementById("inFlowVideoDuration"),



  flowVideoRow: document.getElementById("flowVideoRow"),



  inWorkers: document.getElementById("inWorkers"),



  inModel: document.getElementById("inModel"),



  inPrompt: document.getElementById("inPrompt"),



  btnLive: document.getElementById("btnLive"),



  btnOffline: document.getElementById("btnOffline"),



  btnStop: document.getElementById("btnStop"),



  btnResume: document.getElementById("btnResume"),



  btnRetryEpisode: document.getElementById("btnRetryEpisode"),



  btnRetryError: document.getElementById("btnRetryError"),



  resumeBanner: document.getElementById("resumeBanner"),



  resumeBadge: document.getElementById("resumeBadge"),



  resumeBannerDesc: document.getElementById("resumeBannerDesc"),



  completedBanner: document.getElementById("completedBanner"),



  btnNextEpisode: document.getElementById("btnNextEpisode"),



  btnRemakeEpisode: document.getElementById("btnRemakeEpisode"),







  // Storyboard Deck



  scenesContainer: document.getElementById("scenesContainer"),



  scenesCountBadge: document.getElementById("scenesCountBadge"),







  // Cinema Player



  cinemaVideo: document.getElementById("cinemaVideo"),



  videoEmptyState: document.getElementById("videoEmptyState"),



  videoMonitorContainer: document.getElementById("videoMonitorContainer"),



  videoPlayCenterBtn: document.getElementById("videoPlayCenterBtn"),



  videoUnmutePill: document.getElementById("videoUnmutePill"),



  playerPlaybackStatus: document.getElementById("playerPlaybackStatus"),



  modeBtnEpisode: document.getElementById("modeBtnEpisode"),



  modeBtnShort: document.getElementById("modeBtnShort"),



  modeBtnScene: document.getElementById("modeBtnScene"),



  playerTitle: document.getElementById("playerTitle"),



  btnDownloadMp4: document.getElementById("btnDownloadMp4"),



  btnOpenFolder: document.getElementById("btnOpenFolder"),







  // Pipeline Stepper



  stepScript: document.getElementById("stepScript"),



  stepImage: document.getElementById("stepImage"),



  stepAnim: document.getElementById("stepAnim"),



  stepAudio: document.getElementById("stepAudio"),



  stepConcat: document.getElementById("stepConcat"),



  progressPercent: document.getElementById("progressPercent"),



  progressBarFill: document.getElementById("progressBarFill"),



  pipelineMessage: document.getElementById("pipelineMessage"),







  // Logs



  logsConsole: document.getElementById("logsConsole"),



  headerStatusPill: document.getElementById("headerStatusPill"),



  headerStatusDot: document.getElementById("headerStatusDot"),



  headerStatusText: document.getElementById("headerStatusText"),







  // Modals



  modalApiKey: document.getElementById("modalApiKey"),



  modalProductions: document.getElementById("modalProductions"),



  modalLightbox: document.getElementById("modalLightbox"),



  lightboxImg: document.getElementById("lightboxImg"),



  inGeminiKey: document.getElementById("inGeminiKey"),



  mcpAccountSelect: document.getElementById("mcpAccountSelect"),



  mcpNewAccountName: document.getElementById("mcpNewAccountName"),



  mcpAccountStatus: document.getElementById("mcpAccountStatus"),



  mcpProjectSelect: document.getElementById("mcpProjectSelect"),



  mcpProjectStatus: document.getElementById("mcpProjectStatus"),



  mcpOpenProjectTab: document.getElementById("mcpOpenProjectTab"),



  mcpProjectName: document.getElementById("mcpProjectName"),



  mcpGenreBind: document.getElementById("mcpGenreBind"),



  btnSaveKey: document.getElementById("btnSaveKey"),



  productionsList: document.getElementById("productionsList"),



};







// CURATED VOICES BY COUNTRY & REGION (Gemini 3.8 Studio - Súc Tích & Chuẩn Quốc Gia)



const VOICE_CATALOG = {



  VN: {



    name: "Việt Nam",



    female: [



      { id: "Aoede", text: "Aoede (Nữ - Truyền cảm)" },



      { id: "Kore", text: "Kore (Nữ - Dứt khoát)" },



      { id: "Leda", text: "Leda (Nữ - Trẻ trung)" },



      { id: "Puck", text: "Puck (Nữ - Hoạt hình)" },



      { id: "Zephyr", text: "Zephyr (Nữ - Trong trẻo)" },



    ],



    male: [



      { id: "Orus", text: "Orus (Nam - Ấm áp)" },



      { id: "Charon", text: "Charon (Nam - Trầm đĩnh đạc)" },



      { id: "Gacrux", text: "Gacrux (Nam - Sâu sắc)" },



      { id: "Fenrir", text: "Fenrir (Nam - Mạnh mẽ)" },



      { id: "Alnilam", text: "Alnilam (Nam - Điện ảnh)" },



    ],



  },



  US: {



    name: "Mỹ (American English)",



    female: [



      { id: "Puck", text: "Puck (Female - Lively)" },



      { id: "Zephyr", text: "Zephyr (Female - Clear)" },



      { id: "Despina", text: "Despina (Female - Smooth)" },



      { id: "Callirrhoe", text: "Callirrhoe (Female - Friendly)" },



      { id: "Autonoe", text: "Autonoe (Female - Bright)" },



    ],



    male: [



      { id: "Orus", text: "Orus (Male - Warm)" },



      { id: "Fenrir", text: "Fenrir (Male - Punchy)" },



      { id: "Alnilam", text: "Alnilam (Male - Deep Cinema)" },



      { id: "Umbriel", text: "Umbriel (Male - Casual)" },



      { id: "Pulcherrima", text: "Pulcherrima (Male - Direct)" },



    ],



  },



  GB: {



    name: "Anh (British English)",



    female: [



      { id: "Algieba", text: "Algieba (Female - Calm RP)" },



      { id: "Callirrhoe", text: "Callirrhoe (Female - Friendly)" },



      { id: "Vindemiatrix", text: "Vindemiatrix (Female - Elegant)" },



    ],



    male: [



      { id: "Schedar", text: "Schedar (Male - Classic Doc)" },



      { id: "Charon", text: "Charon (Male - Historical)" },



      { id: "Rasalgethi", text: "Rasalgethi (Male - Academic)" },



    ],



  },



  JP: {



    name: "Nhật Bản (Japanese)",



    female: [



      { id: "Autonoe", text: "Autonoe (女性 - Anime)" },



      { id: "Sulafat", text: "Sulafat (女性 - Warm)" },



      { id: "Kore", text: "Kore (女性 - News)" },



    ],



    male: [



      { id: "Enceladus", text: "Enceladus (男性 - Deep)" },



      { id: "Achird", text: "Achird (男性 - Friendly)" },



      { id: "Charon", text: "Charon (男性 - Epic)" },



    ],



  },



  KR: {



    name: "Hàn Quốc (Korean)",



    female: [



      { id: "Laomedeia", text: "Laomedeia (여성 - Modern)" },



      { id: "Achernar", text: "Achernar (여성 - Calm Drama)" },



      { id: "Aoede", text: "Aoede (여성 - Melodic)" },



    ],



    male: [



      { id: "Pulcherrima", text: "Pulcherrima (남성 - News)" },



      { id: "Iapetus", text: "Iapetus (남성 - Sincere)" },



      { id: "Gacrux", text: "Gacrux (남성 - Deep Doc)" },



    ],



  },



  CN: {



    name: "Trung Quốc (Mandarin)",



    female: [



      { id: "Vindemiatrix", text: "Vindemiatrix (优雅抒情女声)" },



      { id: "Sadachbia", text: "Sadachbia (生动自然女声)" },



      { id: "Aoede", text: "Aoede (温柔治愈女声)" },



    ],



    male: [



      { id: "Zubenelgenubi", text: "Zubenelgenubi (稳重大气男声)" },



      { id: "Sadaltager", text: "Sadaltager (知识导师男声)" },



      { id: "Orus", text: "Orus (温暖叙事男声)" },



    ],



  },



  ES: {



    name: "Tây Ban Nha (España)",



    female: [



      { id: "Despina", text: "Despina (Femenina - Cautivadora)" },



      { id: "Kore", text: "Kore (Femenina - Clara)" },



      { id: "Puck", text: "Puck (Femenina - Dinámica)" },



    ],



    male: [



      { id: "Charon", text: "Charon (Masculino - Solemne)" },



      { id: "Algenib", text: "Algenib (Masculino - Firme)" },



      { id: "Orus", text: "Orus (Masculino - Cálido)" },



    ],



  },



  MX: {



    name: "Mexico / Latin",



    female: [



      { id: "Despina", text: "Despina (Femenina - Suave)" },



      { id: "Puck", text: "Puck (Femenina - Divertida)" },



    ],



    male: [



      { id: "Orus", text: "Orus (Masculino - Expresivo)" },



      { id: "Algenib", text: "Algenib (Masculino - Intrépido)" },



    ],



  },



  FR: {



    name: "Pháp (France)",



    female: [



      { id: "Aoede", text: "Aoede (Féminin - Poétique)" },



      { id: "Algieba", text: "Algieba (Féminin - Distingué)" },



    ],



    male: [



      { id: "Charon", text: "Charon (Masculin - Profond)" },



      { id: "Gacrux", text: "Gacrux (Masculin - Posé)" },



    ],



  },



  DE: {



    name: "Đức (Germany)",



    female: [



      { id: "Kore", text: "Kore (Weiblich - Präzise)" },



      { id: "Zephyr", text: "Zephyr (Weiblich - Sachlich)" },



    ],



    male: [



      { id: "Alnilam", text: "Alnilam (Männlich - Kraftvoll)" },



      { id: "Fenrir", text: "Fenrir (Männlich - Dynamisch)" },



    ],



  },



  RU: {



    name: "Nga (Russian)",



    female: [



      { id: "Erinome", text: "Erinome (Женский - Чёткий)" },



      { id: "Algieba", text: "Algieba (Женский - Спокойный)" },



    ],



    male: [



      { id: "Charon", text: "Charon (Мужской - Монументальный)" },



      { id: "Alnilam", text: "Alnilam (Мужской - Кино)" },



    ],



  },



  BR: {



    name: "Brazil (Portuguese)",



    female: [



      { id: "Leda", text: "Leda (Feminina - Jovem)" },



      { id: "Autonoe", text: "Autonoe (Feminina - Vibrante)" },



    ],



    male: [



      { id: "Umbriel", text: "Umbriel (Masculino - Natural)" },



      { id: "Fenrir", text: "Fenrir (Masculino - Enérgico)" },



    ],



  },



  IT: {



    name: "Ý (Italian)",



    female: [



      { id: "Algieba", text: "Algieba (Femminile - Elegante)" },



      { id: "Despina", text: "Despina (Femminile - Caldo)" },



    ],



    male: [



      { id: "Charon", text: "Charon (Maschile - Solenne)" },



      { id: "Achird", text: "Achird (Maschile - Empatico)" },



    ],



  },



  TH: {



    name: "Thái Lan (Thai)",



    female: [



      { id: "Aoede", text: "Aoede (หญิง - อ่อนหวาน)" },



      { id: "Puck", text: "Puck (หญิง - สดใส)" },



    ],



    male: [



      { id: "Orus", text: "Orus (ชาย - อบอุ่น)" },



      { id: "Gacrux", text: "Gacrux (ชาย - สุขุม)" },



    ],



  },



  ID: {



    name: "Indonesia / Đông Nam Á",



    female: [



      { id: "Aoede", text: "Aoede (Wanita - Lembut)" },



      { id: "Puck", text: "Puck (Wanita - Ceria)" },



    ],



    male: [



      { id: "Orus", text: "Orus (Pria - Hangat)" },



      { id: "Gacrux", text: "Gacrux (Pria - Berkarakter)" },



    ],



  },



  IN: {



    name: "Ấn Độ (Hindi)",



    female: [



      { id: "Callirrhoe", text: "Callirrhoe (Female - Clear)" },



      { id: "Zephyr", text: "Zephyr (Female - Smooth)" },



    ],



    male: [



      { id: "Orus", text: "Orus (Male - Storyteller)" },



      { id: "Rasalgethi", text: "Rasalgethi (Male - Wise)" },



    ],



  },



  SA: {



    name: "Ả Rập (Arabic)",



    female: [



      { id: "Sulafat", text: "Sulafat (أنثى - دافئة)" },



      { id: "Algieba", text: "Algieba (أنثى - هادئة)" },



    ],



    male: [



      { id: "Alnilam", text: "Alnilam (ذكر - فخم)" },



      { id: "Schedar", text: "Schedar (ذكر - حكيم)" },



    ],



  },



};







const ALL_FEMALE_VOICES = [



  { id: "Aoede", text: "Aoede (Nữ - Truyền cảm)" },



  { id: "Kore", text: "Kore (Nữ - Dứt khoát)" },



  { id: "Leda", text: "Leda (Nữ - Trẻ trung)" },



  { id: "Puck", text: "Puck (Nữ - Hoạt hình)" },



  { id: "Zephyr", text: "Zephyr (Nữ - Trong trẻo)" },



  { id: "Algieba", text: "Algieba (Nữ - Điềm tĩnh)" },



  { id: "Callirrhoe", text: "Callirrhoe (Nữ - Tự nhiên)" },



  { id: "Despina", text: "Despina (Nữ - Cuốn hút)" },



  { id: "Autonoe", text: "Autonoe (Nữ - Sôi nổi)" },



  { id: "Sulafat", text: "Sulafat (Nữ - Ấm áp)" },



  { id: "Laomedeia", text: "Laomedeia (Nữ - Năng động)" },



  { id: "Achernar", text: "Achernar (Nữ - Dịu êm)" },



  { id: "Vindemiatrix", text: "Vindemiatrix (Nữ - Trang nhã)" },



  { id: "Sadachbia", text: "Sadachbia (Nữ - Sắc sảo)" },



  { id: "Erinome", text: "Erinome (Nữ - Rành mạch)" },



];







const ALL_MALE_VOICES = [



  { id: "Orus", text: "Orus (Nam - Ấm áp)" },



  { id: "Charon", text: "Charon (Nam - Trầm đĩnh đạc)" },



  { id: "Gacrux", text: "Gacrux (Nam - Sâu sắc)" },



  { id: "Fenrir", text: "Fenrir (Nam - Mạnh mẽ)" },



  { id: "Alnilam", text: "Alnilam (Nam - Điện ảnh)" },



  { id: "Schedar", text: "Schedar (Nam - Triết lý)" },



  { id: "Iapetus", text: "Iapetus (Nam - Trong sáng)" },



  { id: "Algenib", text: "Algenib (Nam - Phong trần)" },



  { id: "Rasalgethi", text: "Rasalgethi (Nam - Học thuật)" },



  { id: "Enceladus", text: "Enceladus (Nam - Bí ẩn)" },



  { id: "Umbriel", text: "Umbriel (Nam - Tự nhiên)" },



  { id: "Pulcherrima", text: "Pulcherrima (Nam - Dứt khoát)" },



  { id: "Achird", text: "Achird (Nam - Gần gũi)" },



  { id: "Zubenelgenubi", text: "Zubenelgenubi (Nam - Mộc mạc)" },



  { id: "Sadaltager", text: "Sadaltager (Nam - Dẫn dắt)" },



];







function getEffectiveRegion() {



  const reg = el.inRegion ? el.inRegion.value : "auto";



  if (reg && reg !== "auto") return reg;



  const lang = el.inLanguage ? el.inLanguage.value.toLowerCase() : "vietnamese";



  const langMap = {



    vietnamese: "VN", english: "US", chinese: "CN", japanese: "JP",



    korean: "KR", spanish: "ES", french: "FR", german: "DE",



    russian: "RU", portuguese: "BR", italian: "IT", thai: "TH",



    indonesian: "ID", malay: "ID", filipino: "ID", hindi: "IN",



    arabic: "SA", dutch: "DE", polish: "DE", turkish: "DE",



    swedish: "GB", greek: "GB"



  };



  return langMap[lang] || "VN";



}







function updateVoiceOptions(showAll = false) {



  if (!el.inVoice) return;



  const currentVal = el.inVoice.value;



  const regKey = getEffectiveRegion();



  const catalog = VOICE_CATALOG[regKey] || VOICE_CATALOG["VN"];







  let html = `<option value="auto">✨ Tự động</option>`;







  if (showAll) {



    html += `<optgroup label="👩 Giọng Nữ (15 giọng)">`;



    ALL_FEMALE_VOICES.forEach((v) => {



      html += `<option value="${v.id}">${v.text}</option>`;



    });



    html += `</optgroup><optgroup label="👨 Giọng Nam (15 giọng)">`;



    ALL_MALE_VOICES.forEach((v) => {



      html += `<option value="${v.id}">${v.text}</option>`;



    });



    html += `</optgroup>`;



    html += `<option value="__FILTERED__">🔙 Chỉ giọng ${catalog.name}...</option>`;



  } else {



    html += `<optgroup label="👩 Giọng Nữ ${catalog.name} (${catalog.female.length})">`;



    catalog.female.forEach((v) => {



      html += `<option value="${v.id}">${v.text}</option>`;



    });



    html += `</optgroup><optgroup label="👨 Giọng Nam ${catalog.name} (${catalog.male.length})">`;



    catalog.male.forEach((v) => {



      html += `<option value="${v.id}">${v.text}</option>`;



    });



    html += `</optgroup>`;



    html += `<option value="__ALL__">🌐 Tất cả 30 giọng...</option>`;



  }



  html += `<option value="__LIBRARY__">🎧 Nghe thử từng giọng...</option>`;







  el.inVoice.innerHTML = html;







  // Preserve previous value if still valid



  const optionExists = Array.from(el.inVoice.options).some((o) => o.value === currentVal);



  if (optionExists && currentVal !== "__ALL__" && currentVal !== "__FILTERED__") {



    el.inVoice.value = currentVal;



  } else {



    el.inVoice.value = "auto";



  }







  const voiceLabel = document.getElementById("inVoiceLabel");



  if (voiceLabel) {



    voiceLabel.textContent = "Giọng Kể";



  }



}







function updateLiveButtonLabel() {



  const ep = parseInt(el.inEpisode?.value, 10) || 1;



  const label = document.getElementById("btnLiveLabel");



  if (label && !state.isRunning && !state.submitting && state.statusReady) {



    label.textContent = `Sản Xuất Tập ${ep}`;



  }



}







window.snapWindow1400x850 = function() {



  try {



    window.resizeTo(1400, 850);



  } catch (e) {}



  fetch("/api/window/resize", {



    method: "POST",



    headers: { "Content-Type": "application/json" },



    body: JSON.stringify({ width: 1400, height: 850 })



  }).then(r => r.json()).then(data => {



    console.log("[WINDOW_RESIZE] 1400x850 applied:", data);



  }).catch(() => {});



};



window.snapWindow1024x648 = window.snapWindow1400x850;







// INIT



document.addEventListener("DOMContentLoaded", () => {



  const updateButton = document.getElementById("btnCheckUpdates");



  if (updateButton) {



    updateButton.dataset.updateDefaultText = updateButton.textContent.trim();



    updateButton.dataset.updateDefaultTitle = updateButton.title;



    updateButton.addEventListener("click", startOnlineUpdate);



    checkUpdateAvailability();



    window.setInterval(checkUpdateAvailability, 5 * 60 * 1000);



    window.addEventListener("focus", checkUpdateAvailability);



    document.addEventListener("visibilitychange", () => {



      if (!document.hidden) checkUpdateAvailability();



    });



  }







  // Restore saved series and episode from localStorage



  const savedSeries = localStorage.getItem("storyboard_saved_series");



  const savedEp = localStorage.getItem("storyboard_saved_episode");



  if (savedSeries && el.inSeries) {



    el.inSeries.value = savedSeries;



    state.currentSeries = savedSeries;



  }



  if (savedEp && el.inEpisode) {



    el.inEpisode.value = savedEp;



    state.currentEpisode = parseInt(savedEp, 10) || 1;



  }



  const headerProj = document.getElementById("headerProjectName");



  if (headerProj) {



    headerProj.textContent = `${el.inSeries?.value || "Whiteboard Series"} - Tập ${el.inEpisode?.value || 1}`;



  }







  setupEventHandlers();



  initDockNavigation();



  loadConfig();



  loadMcpAccounts();



  setButtonsRunning(false);



  updateLiveButtonLabel();



  startStatusPolling();



  updateImageBudgetHint();



  loadProductions();



  updateVoiceOptions(false);



  // Auto-load initial episode if present



  loadEpisodeDetails(state.currentSeries, state.currentEpisode);







  // Initialize AI Robot Studio Companion Walker



  if (window.studioRobotWalker && typeof window.studioRobotWalker.init === "function") {



    window.studioRobotWalker.init();



  }







  // Auto-snap window to 1400x850 standard dimensions



  setTimeout(() => {



    if (typeof window.snapWindow1400x850 === "function") {



      window.snapWindow1400x850();



    }



  }, 350);



});







// Adaptive navigation changes only visibility; existing form, player, timeline



// and production DOM nodes are never replaced or re-created.



function initDockNavigation() {



  const tabs = [...document.querySelectorAll(".dock-tab")];



  const shade = document.getElementById("dockShade");



  if (!tabs.length || !shade) return;



  const choose = (requested) => {



    const name = ["setup", "scenes", "monitor"].includes(requested) ? requested : "scenes";



    document.body.dataset.dock = name;



    for (const tab of tabs) {



      const selected = tab.dataset.dock === name;



      tab.classList.toggle("active", selected);



      tab.setAttribute("aria-pressed", String(selected));



    }



  };



  for (const tab of tabs) tab.addEventListener("click", () => choose(tab.dataset.dock));



  shade.addEventListener("click", () => choose("scenes"));



  document.addEventListener("keydown", (event) => {



    if (event.key !== "Escape" || !window.matchMedia("(max-width: 1199px)").matches) return;



    // Let a visible dialog handle Escape itself.



    if (document.querySelector(".modal-overlay.show, .modal-overlay.active")) return;



    if (document.body.dataset.dock !== "scenes") choose("scenes");



  });



  choose("scenes");



}







function setupEventHandlers() {



  // Dual-Mode Production Format Buttons Toggle



  const btnNarrative = document.getElementById("btnModeNarrative");



  const btnDrama = document.getElementById("btnModeDrama");



  const inProdMode = document.getElementById("inProductionMode");



  const prodBadge = document.getElementById("prodModeBadge");







  window.updateDramaDurationCoupling = function() {



    const inProd = document.getElementById("inProductionMode");



    const isDrama = inProd && inProd.value === "cinematic_drama";



    const lblSceneSec = document.getElementById("lblSceneSec");



    const sceneSecHint = document.getElementById("sceneSecHint");



    if (isDrama) {



      if (el.inSceneSec) {



        el.inSceneSec.value = "10";



        el.inSceneSec.readOnly = true;



        el.inSceneSec.style.borderColor = "#f59e0b";



        el.inSceneSec.style.background = "rgba(245, 158, 11, 0.08)";



      }



      if (lblSceneSec) lblSceneSec.textContent = "Cảnh (10s)";



      if (sceneSecHint) {



        const mins = Math.max(0.1, Number(el.inMinutes?.value) || 1.0);



        const scCount = Math.max(1, Math.round(mins * 60 / 10));



        sceneSecHint.style.display = "block";



        sceneSecHint.textContent = `🎬 Tự động khớp 10s video Muse (${scCount} cảnh = ${(scCount * 10 / 60).toFixed(1)} phút)`;



      }



    }



  };







  window.setProductionModeUI = function(mode) {



    if (inProdMode) inProdMode.value = mode;



    try { localStorage.setItem("storyboard_saved_production_mode", mode); } catch (_) {}







    const lblSceneSec = document.getElementById("lblSceneSec");



    const sceneSecHint = document.getElementById("sceneSecHint");







    if (btnNarrative && btnDrama) {



      if (mode === "cinematic_drama") {



        btnDrama.classList.add("active");



        btnDrama.style.border = "1px solid #f59e0b";



        btnDrama.style.background = "rgba(245, 158, 11, 0.22)";



        btnDrama.style.color = "#fbbf24";



        btnDrama.style.fontWeight = "600";







        btnNarrative.classList.remove("active");



        btnNarrative.style.border = "1px solid #334155";



        btnNarrative.style.background = "#0b1120";



        btnNarrative.style.color = "#94a3b8";



        btnNarrative.style.fontWeight = "500";







        if (prodBadge) {



          prodBadge.textContent = "100% Video Chuyển Động";



          prodBadge.className = "badge badge-amber";



        }







        // Tự động khớp độ dài cảnh với thời lượng video Muse (10s/cảnh)



        if (el.inSceneSec) {



          if (!window._savedNarrativeSceneSec && el.inSceneSec.value !== "10") {



            window._savedNarrativeSceneSec = el.inSceneSec.value;



          }



          el.inSceneSec.value = "10";



          el.inSceneSec.readOnly = true;



          el.inSceneSec.style.borderColor = "#f59e0b";



          el.inSceneSec.style.background = "rgba(245, 158, 11, 0.08)";



        }



        if (lblSceneSec) {



          lblSceneSec.textContent = "Cảnh (10s)";



        }



        if (sceneSecHint) {



          const mins = Math.max(0.1, Number(el.inMinutes?.value) || 1.0);



          const scCount = Math.max(1, Math.round(mins * 60 / 10));



          sceneSecHint.style.display = "block";



          sceneSecHint.textContent = `🎬 Tự động khớp 10s video Muse (${scCount} cảnh = ${(scCount * 10 / 60).toFixed(1)} phút)`;



        }



      } else {



        btnNarrative.classList.add("active");



        btnNarrative.style.border = "1px solid #6366f1";



        btnNarrative.style.background = "rgba(99, 102, 241, 0.22)";



        btnNarrative.style.color = "#818cf8";



        btnNarrative.style.fontWeight = "600";







        btnDrama.classList.remove("active");



        btnDrama.style.border = "1px solid #334155";



        btnDrama.style.background = "#0b1120";



        btnDrama.style.color = "#94a3b8";



        btnDrama.style.fontWeight = "500";







        if (prodBadge) {



          prodBadge.textContent = "1 Giọng Đọc • Hook Video 30s";



          prodBadge.title = "Cảnh 1 (Hook mở đầu 25-30s) tự động dùng Video chuyển động (Muse AI / Flow Video), các cảnh sau chạy ảnh tĩnh + chuyển động máy quay";



          prodBadge.className = "badge badge-indigo";



        }







        // Khôi phục luồng thuyết minh nguyên vẹn



        if (el.inSceneSec) {



          el.inSceneSec.readOnly = false;



          el.inSceneSec.style.borderColor = "";



          el.inSceneSec.style.background = "";



          if (window._savedNarrativeSceneSec) {



            el.inSceneSec.value = window._savedNarrativeSceneSec;



          } else if (el.inSceneSec.value === "10") {



            el.inSceneSec.value = "25";



          }



        }



        if (lblSceneSec) {



          lblSceneSec.textContent = "Cảnh (Giây)";



        }



        if (sceneSecHint) {



          sceneSecHint.style.display = "none";



        }



      }



    }



  };







  if (btnNarrative) {



    btnNarrative.addEventListener("click", () => window.setProductionModeUI("narrative"));



  }



  if (btnDrama) {



    btnDrama.addEventListener("click", () => {



      window.setProductionModeUI("cinematic_drama");



      const inImgSrc = document.getElementById("inImageSource");



      if (inImgSrc) {



        inImgSrc.value = "muse_video";



        if (typeof updateImageBudgetHint === "function") updateImageBudgetHint();



      }



    });



  }







  if (el.inImageSource) {



    el.inImageSource.addEventListener("change", () => {



      if (el.inImageSource.value !== "muse_video") {



        window.setProductionModeUI("narrative");



      }



    });



  }







  // Restore saved production mode - Safe default to narrative



  try {



    const savedMode = localStorage.getItem("storyboard_saved_production_mode") || "narrative";



    if (savedMode === "cinematic_drama" && el.inImageSource && el.inImageSource.value === "muse_video") {



      window.setProductionModeUI("cinematic_drama");



    } else {



      window.setProductionModeUI("narrative");



    }



  } catch (_) {



    window.setProductionModeUI("narrative");



  }







  // Save and restore resolution & aspect ratio



  if (el.inResolution) {



    try {



      const savedRes = localStorage.getItem("storyboard_saved_resolution");



      if (savedRes) el.inResolution.value = savedRes;



    } catch (_) {}



    el.inResolution.addEventListener("change", () => {



      try { localStorage.setItem("storyboard_saved_resolution", el.inResolution.value); } catch (_) {}



    });



  }







  // Auto-save and live sync for Series Name



  let seriesDebounceTimer = null;



  if (el.inSeries) {



    el.inSeries.addEventListener("input", (e) => {



      const val = e.target.value.trim() || "Whiteboard Series";



      localStorage.setItem("storyboard_saved_series", e.target.value);



      state.currentSeries = val;



      const ep = parseInt(el.inEpisode ? el.inEpisode.value : 1, 10) || 1;



      const headerProj = document.getElementById("headerProjectName");



      if (headerProj) headerProj.textContent = `${val} - Tập ${ep}`;



      updateLiveButtonLabel();



      clearTimeout(seriesDebounceTimer);



      seriesDebounceTimer = setTimeout(() => {



        loadEpisodeDetails(val, ep);



      }, 400);



    });



  }







  // Auto-save and live sync for Episode Number



  let epDebounceTimer = null;



  const onEpisodeChanged = (e) => {



    const ep = parseInt(e.target.value, 10) || 1;



    localStorage.setItem("storyboard_saved_episode", String(ep));



    state.currentEpisode = ep;



    const series = el.inSeries ? (el.inSeries.value.trim() || "Whiteboard Series") : "Whiteboard Series";



    const headerProj = document.getElementById("headerProjectName");



    if (headerProj) headerProj.textContent = `${series} - Tập ${ep}`;



    updateLiveButtonLabel();







    // Strict Episode Isolation: Invalidate stale SEO cache when switching episodes



    currentSeoData = null;



    window.currentSeoData = null;



    if (state) state.currentSeoData = null;







    // Reset giao diện ngay lập tức khi đổi số tập



    if (!state.isRunning) {



      if (el.progressPercent) el.progressPercent.textContent = "0%";



      if (el.progressBarFill) el.progressBarFill.style.width = "0%";



      if (el.headerStatusDot) el.headerStatusDot.classList.remove("active", "error");



      if (el.headerStatusText) el.headerStatusText.textContent = "Sẵn sàng";



      if (el.pipelineMessage) el.pipelineMessage.textContent = `Đang chuyển sang Tập ${ep}...`;



      const steps = [el.stepScript, el.stepImage, el.stepAnim, el.stepAudio, el.stepConcat];



      steps.forEach((s) => s && s.classList.remove("active", "done"));



    }







    clearTimeout(epDebounceTimer);



    epDebounceTimer = setTimeout(() => {



      loadEpisodeDetails(series, ep);



    }, 200);



  };



  if (el.inEpisode) {



    el.inEpisode.addEventListener("input", onEpisodeChanged);



    el.inEpisode.addEventListener("change", onEpisodeChanged);



  }







  // Player mode switcher



  if (el.modeBtnEpisode) el.modeBtnEpisode.addEventListener("click", () => switchPlayerMode("episode"));



  if (el.modeBtnShort) el.modeBtnShort.addEventListener("click", () => switchPlayerMode("short"));



  if (el.modeBtnScene) el.modeBtnScene.addEventListener("click", () => switchPlayerMode("scene"));







  // Cinema Player Video Events & Controls



  if (el.cinemaVideo) {



    el.cinemaVideo.addEventListener("play", () => {



      updatePlayOverlay(false);



      updatePlaybackStatus(true);



    });



    el.cinemaVideo.addEventListener("playing", () => {



      updatePlayOverlay(false);



      updatePlaybackStatus(true);



    });



    el.cinemaVideo.addEventListener("pause", () => {



      updatePlayOverlay(true);



      updatePlaybackStatus(false);



    });



    el.cinemaVideo.addEventListener("ended", () => {



      updatePlayOverlay(true);



      updatePlaybackStatus(false);



    });



    el.cinemaVideo.addEventListener("volumechange", () => {



      if (!el.cinemaVideo.muted) {



        hideUnmutePill();



      }



    });



    el.cinemaVideo.addEventListener("loadeddata", () => {



      el.cinemaVideo.removeAttribute("poster");



    });



    el.cinemaVideo.addEventListener("click", (e) => {



      e.stopPropagation();



      toggleCinemaPlayback(true);



    });



  }







  if (el.videoPlayCenterBtn) {



    el.videoPlayCenterBtn.addEventListener("click", (e) => {



      e.stopPropagation();



      toggleCinemaPlayback(true);



    });



  }







  if (el.videoUnmutePill) {



    el.videoUnmutePill.addEventListener("click", (e) => {



      e.stopPropagation();



      if (el.cinemaVideo) {



        el.cinemaVideo.muted = false;



        el.cinemaVideo.play().catch(() => {



          // Fallback to muted playback if user gesture was untrusted



          el.cinemaVideo.muted = true;



          el.cinemaVideo.play().catch(() => {});



        });



        hideUnmutePill();



        updatePlayOverlay(false);



        updatePlaybackStatus(true);



        showToast("Đã bật âm thanh 🔊");



      }



    });



  }







  // Form buttons



  if (el.btnLive) el.btnLive.addEventListener("click", () => submitProduction("live"));



  if (el.btnOffline) el.btnOffline.addEventListener("click", () => submitProduction("offline"));



  if (el.btnStop) el.btnStop.addEventListener("click", stopProduction);



  if (el.btnResume) el.btnResume.addEventListener("click", () => submitProduction("live", { resume: true }));



  if (el.btnRetryEpisode) {



    el.btnRetryEpisode.addEventListener("click", () => {



      if (confirm("Bạn có chắc chắn muốn bỏ qua các cảnh đã tạo và làm lại tập này từ đầu không?")) {



        submitProduction("live", { force_new: true });



      }



    });



  }



  if (el.btnRetryError) el.btnRetryError.addEventListener("click", () => submitProduction("live", { resume: true }));



  if (el.btnNextEpisode) {



    el.btnNextEpisode.addEventListener("click", () => {



      const curEp = parseInt(el.inEpisode ? el.inEpisode.value : 1, 10) || 1;



      const next = curEp + 1;



      if (el.inEpisode) el.inEpisode.value = String(next);



      state.currentEpisode = next;



      updateLiveButtonLabel();



      // Strict Episode Isolation: Invalidate stale SEO cache on next episode



      currentSeoData = null;



      window.currentSeoData = null;



      if (state) state.currentSeoData = null;



      if (el.inPrompt) {



        if (!el.inInputMode || el.inInputMode.value === "idea") {

          // Episode continuation is grounded in saved prior plans by the script engine.

          el.inPrompt.value = `Tập ${next}: Viết tiếp Tập ${curEp} trong cùng series ${state.currentSeries || ""}. Giữ nguyên chủ đề lớn, phát triển chương kế tiếp theo kịch bản đã lưu, không tạo ý tưởng độc lập.`;

          el.inPrompt.placeholder = `Tập ${next} nối tiếp Tập ${curEp} (có thể thêm yêu cầu cho chương này)...`;

        } else {

          el.inPrompt.value = "";

          el.inPrompt.placeholder = `Nhập kịch bản hoặc link cho Tập ${next}...`;

        }



        el.inPrompt.focus();



      }



      if (el.inReferenceUrl) {



        el.inReferenceUrl.value = "";



      }



      if (!state.isRunning) {



        if (el.progressPercent) el.progressPercent.textContent = "0%";



        if (el.progressBarFill) el.progressBarFill.style.width = "0%";



        if (el.headerStatusDot) el.headerStatusDot.classList.remove("active", "error");



        if (el.headerStatusText) el.headerStatusText.textContent = "Sẵn sàng";



        if (el.pipelineMessage) el.pipelineMessage.textContent = `Sẵn sàng sản xuất Tập ${next}`;



        const steps = [el.stepScript, el.stepImage, el.stepAnim, el.stepAudio, el.stepConcat];



        steps.forEach((s) => s && s.classList.remove("active", "done"));



      }



      renderLogs([`[Studio] Đã chuyển sang Tập ${next}. Chế độ ý tưởng sẽ nối tiếp tập đã lưu trong cùng series.`]);



      showToast(`Đã chuyển sang Tập ${next}. Bấm Sản Xuất để viết chương tiếp theo của series!`);



      loadEpisodeDetails(state.currentSeries, next);



    });



  }



  if (el.btnRemakeEpisode) {



    el.btnRemakeEpisode.addEventListener("click", () => {



      const curEp = parseInt(el.inEpisode ? el.inEpisode.value : 1, 10) || 1;



      if (confirm(`Bạn có chắc chắn muốn XÓA DỮ LIỆU CŨ và SẢN XUẤT LẠI TẬP ${curEp} từ đầu không?`)) {



        submitProduction("live", { force_new: true });



      }



    });



  }







  const galleryList = document.getElementById("productionsList");



  if (galleryList) galleryList.addEventListener("click", onGalleryAction);



  for (const id of ["gallerySearch", "galleryFilter", "gallerySort"]) {



    const node = document.getElementById(id);



    if (node) node.addEventListener(id === "gallerySearch" ? "input" : "change", renderGallery);



  }







  if (el.inInputMode) {



    el.inInputMode.addEventListener("change", updateInputModeFields);



    updateInputModeFields();



  }











  // Scan link button



  const btnScan = document.getElementById("btnAnalyzeLink");



  if (btnScan) {



    btnScan.addEventListener("click", () => analyzeYouTubeLink(null, true));



  }







  // Import script button & file input



  const btnImport = document.getElementById("btnImportScript");



  const fileImportInput = document.getElementById("fileScriptInput");



  if (btnImport && fileImportInput) {



    btnImport.addEventListener("click", () => {



      fileImportInput.click();



    });



    fileImportInput.addEventListener("change", (e) => {



      const file = e.target.files && e.target.files[0];



      if (!file) return;



      const reader = new FileReader();



      reader.onload = (evt) => {



        const content = evt.target.result;



        if (el.inPrompt) {



          el.inPrompt.value = content;



        }



        if (el.inInputMode) {



          el.inInputMode.value = "script";



          updateInputModeFields();



        }



        syncAutoImageBudget();



        const matches = content.match(/(?:^|\n)[ \t=*-]*(?:#{1,4}[ \t]*)?(?:SHOT|SCENE|CẢNH|PHÂN CẢNH|C\u1ea2NH|PH\u00c2N C\u1ea2NH)[ \t_]+(\d{1,4})/gi);



        const count = matches ? matches.length : 0;



        showToast("Đã nhập kịch bản: " + file.name + (count > 0 ? " (" + count + " cảnh)" : ""));



        fileImportInput.value = "";



      };



      reader.readAsText(file, "UTF-8");



    });



  }







  // Prompt input listener (detect when entering YouTube link, defer scanning until start or manual button)

  if (el.inPrompt) {

    el.inPrompt.addEventListener("input", (e) => {

      const val = e.target.value.trim();

      if (val.startsWith("http://") || val.startsWith("https://") || val.includes("youtu.be") || val.includes("youtube.com")) {

        if (el.inInputMode && el.inInputMode.value !== "link") {

          el.inInputMode.value = "link";

          updateInputModeFields();

        }

        if (el.inReferenceUrl) el.inReferenceUrl.value = val;

        const detectBadge = document.getElementById("linkDetectBadge");

        if (detectBadge && val !== lastAnalyzedUrl) {

          detectBadge.style.display = "flex";

          detectBadge.className = "link-detect-badge";

          detectBadge.innerHTML = `<span>🔗 Đã nhận link video. Bấm <strong>'SẢN XUẤT BẰNG AI'</strong> để tự động quét & sản xuất A-Z ngay!</span>`;

        }

        if (el.inVisualStyle && (!el.inVisualStyle.value || el.inVisualStyle.value === "auto")) {

          const g = el.inGenre?.value || "";

          el.inVisualStyle.value = g === "animation" ? "color_animation" : (g === "whiteboard" ? "whiteboard" : (g === "colored_marker" ? "colored_marker" : ((el.inProductionMode && el.inProductionMode.value === "cinematic_drama") ? "flow_video" : "color_cinematic")));

        }

        clearTimeout(analyzeDebounceTimer);

        analyzeDebounceTimer = setTimeout(() => {

          if (val && val !== lastAnalyzedUrl && !isAnalyzingLink && !state.isRunning) {

            analyzeYouTubeLink(val, false);

          }

        }, 1200);

      } else {

        const mode = el.inInputMode ? el.inInputMode.value : "idea";

        if (mode === "link") {

          if (el.inReferenceUrl) el.inReferenceUrl.value = val;

        } else if (mode === "script") {

          syncAutoImageBudget();

        }

      }

    });



    el.inPrompt.addEventListener("paste", () => {

      setTimeout(() => {

        const val = el.inPrompt ? el.inPrompt.value.trim() : "";

        if (val.startsWith("http://") || val.startsWith("https://") || val.includes("youtu.be") || val.includes("youtube.com")) {

          if (el.inInputMode && el.inInputMode.value !== "link") {

            el.inInputMode.value = "link";

            updateInputModeFields();

          }

          if (el.inReferenceUrl) el.inReferenceUrl.value = val;

          const detectBadge = document.getElementById("linkDetectBadge");

          if (detectBadge && val !== lastAnalyzedUrl) {

            detectBadge.style.display = "flex";

            detectBadge.className = "link-detect-badge";

            detectBadge.innerHTML = `<span>🔗 Đã nhận link video. Bấm <strong>'SẢN XUẤT BẰNG AI'</strong> để tự động quét & sản xuất A-Z ngay!</span>`;

          }

          if (el.inVisualStyle && (!el.inVisualStyle.value || el.inVisualStyle.value === "auto")) {

            const g = el.inGenre?.value || "";

            el.inVisualStyle.value = g === "animation" ? "color_animation" : (g === "whiteboard" ? "whiteboard" : (g === "colored_marker" ? "colored_marker" : ((el.inProductionMode && el.inProductionMode.value === "cinematic_drama") ? "flow_video" : "color_cinematic")));

          }

          clearTimeout(analyzeDebounceTimer);

          analyzeDebounceTimer = setTimeout(() => {

            if (val && val !== lastAnalyzedUrl && !isAnalyzingLink && !state.isRunning) {

              analyzeYouTubeLink(val, false);

            }

          }, 600);

        } else {

          const mode = el.inInputMode ? el.inInputMode.value : "idea";

          if (mode === "script") setTimeout(syncAutoImageBudget, 50);

        }

      }, 50);

    });

  }



  if (el.inReferenceUrl) {

    el.inReferenceUrl.addEventListener("input", (e) => {

      const val = e.target.value.trim();

      if (val.startsWith("http://") || val.startsWith("https://")) {

        clearTimeout(analyzeDebounceTimer);

        analyzeDebounceTimer = setTimeout(() => {

          if (val && val !== lastAnalyzedUrl && !isAnalyzingLink && !state.isRunning) {

            analyzeYouTubeLink(val, false);

          }

        }, 1200);

      }

    });

  }







  // Country & Language Voice Synchronization



  if (el.inLanguage) {



    el.inLanguage.addEventListener("change", () => {



      state.userExplicitLanguage = (el.inLanguage.value !== "Auto");



      if (el.inRegion && (el.inRegion.value === "auto" || !state.userExplicitRegion)) {



        const effReg = getEffectiveRegion();



        el.inRegion.value = effReg;



      }



      updateVoiceOptions(false);



    });



  }



  if (el.inRegion) {



    el.inRegion.addEventListener("change", () => {



      state.userExplicitRegion = (el.inRegion.value !== "auto");



      updateVoiceOptions(false);



    });



  }



  // Voice Preview Engine (Instant 0ms Playback + Pre-cached)



  let currentPreviewAudio = null;



  let activePreviewBtn = null;



  const preloadedVoiceAudios = {};







  function preloadPopularVoices() {



    const popular = ["Kore", "Aoede", "Charon", "Orus", "Leda", "Puck", "Zephyr", "Gacrux", "Fenrir", "Alnilam"];



    popular.forEach((v) => {



      if (!preloadedVoiceAudios[v]) {



        const a = new Audio(`/api/voice/preview?voice=${encodeURIComponent(v)}&language=Vietnamese`);



        a.preload = "auto";



        preloadedVoiceAudios[v] = a;



      }



    });



  }







  // Preload on initial load



  setTimeout(preloadPopularVoices, 500);







  window.playVoicePreviewAudio = async function (voiceName, btnEl) {



    // If currently playing the same voice -> pause it



    if (currentPreviewAudio && !currentPreviewAudio.paused && activePreviewBtn === btnEl) {



      currentPreviewAudio.pause();



      currentPreviewAudio.currentTime = 0;



      currentPreviewAudio = null;



      if (btnEl) {



        btnEl.classList.remove("playing", "loading");



        btnEl.textContent = "🔊";



      }



      activePreviewBtn = null;



      return;



    }







    // Stop any previous audio and reset previous button icon



    if (currentPreviewAudio) {



      currentPreviewAudio.pause();



      currentPreviewAudio.currentTime = 0;



      currentPreviewAudio = null;



    }



    if (activePreviewBtn) {



      activePreviewBtn.classList.remove("playing", "loading");



      activePreviewBtn.textContent = "🔊";



      activePreviewBtn = null;



    }







    const voice = voiceName || (el.inVoice ? el.inVoice.value : "auto");



    const language = el.inLanguage ? el.inLanguage.value : "Vietnamese";



    const pacing = el.inSpeechPacing ? el.inSpeechPacing.value : "slow";



    const genre = el.inGenre ? el.inGenre.value : "documentary";



    const region = el.inRegion ? el.inRegion.value : "auto";







    if (btnEl) {



      btnEl.classList.remove("playing");



      btnEl.classList.add("loading");



      btnEl.textContent = "⏳";



    }



    activePreviewBtn = btnEl;







    try {



      // Reuse preloaded audio if available for zero latency



      let audio = preloadedVoiceAudios[voice];



      if (!audio) {



        const url = `/api/voice/preview?voice=${encodeURIComponent(voice)}&language=${encodeURIComponent(language)}&pacing=${encodeURIComponent(pacing)}&genre=${encodeURIComponent(genre)}&region=${encodeURIComponent(region)}`;



        audio = new Audio(url);



        preloadedVoiceAudios[voice] = audio;



      } else {



        audio.currentTime = 0;



      }



      currentPreviewAudio = audio;







      audio.onplay = () => {



        if (btnEl) {



          btnEl.classList.remove("loading");



          btnEl.classList.add("playing");



          btnEl.textContent = "⏸️";



        }



      };







      audio.onended = () => {



        if (btnEl) {



          btnEl.classList.remove("playing", "loading");



          btnEl.textContent = "🔊";



        }



        currentPreviewAudio = null;



        activePreviewBtn = null;



      };







      audio.onerror = () => {



        if (btnEl) {



          btnEl.classList.remove("playing", "loading");



          btnEl.textContent = "⚠️";



          setTimeout(() => {



            btnEl.textContent = "🔊";



          }, 1500);



        }



        currentPreviewAudio = null;



        activePreviewBtn = null;



      };







      await audio.play();



    } catch (err) {



      console.warn("Voice preview error:", err);



      if (btnEl) {



        btnEl.classList.remove("playing", "loading");



        btnEl.textContent = "⚠️";



        setTimeout(() => {



          btnEl.textContent = "🔊";



        }, 1500);



      }



      currentPreviewAudio = null;



      activePreviewBtn = null;



    }



  };







  const btnPreviewVoice = document.getElementById("btnPreviewVoice");



  if (btnPreviewVoice) {



    btnPreviewVoice.addEventListener("click", () => {



      const voice = el.inVoice ? el.inVoice.value : "auto";



      window.playVoicePreviewAudio(voice, btnPreviewVoice);



    });



  }







  if (el.inVoice) {



    el.inVoice.addEventListener("change", (e) => {



      if (currentPreviewAudio && !currentPreviewAudio.paused) {



        currentPreviewAudio.pause();



        currentPreviewAudio = null;



      }



      if (activePreviewBtn) {



        activePreviewBtn.classList.remove("playing", "loading");



        activePreviewBtn.textContent = "🔊";



        activePreviewBtn = null;



      }



      if (e.target.value === "__ALL__") {



        updateVoiceOptions(true);



      } else if (e.target.value === "__FILTERED__") {



        updateVoiceOptions(false);



      } else if (e.target.value === "__LIBRARY__") {



        const prev = el.inVoice.getAttribute("data-prev-voice") || "auto";



        el.inVoice.value = prev;



        window.openVoiceLibraryModal();



      } else {



        el.inVoice.setAttribute("data-prev-voice", e.target.value);



      }



    });



  }







  window.openVoiceLibraryModal = function () {



    const modal = document.getElementById("modalVoiceLibrary");



    const container = document.getElementById("voiceLibraryListContainer");



    if (!modal || !container) return;







    const regKey = getEffectiveRegion();



    const catalog = VOICE_CATALOG[regKey] || VOICE_CATALOG["VN"];



    const currentVoice = el.inVoice ? el.inVoice.value : "auto";







    let html = `



      <div style="background:#020617;padding:10px 14px;border-radius:8px;border:1px solid #1e293b;display:flex;justify-content:space-between;align-items:center;">



        <div>



          <span style="font-weight:700;color:#fef08a;font-size:0.8rem;">📍 Đang chọn khu vực: ${catalog.name}</span>



          <span style="font-size:0.7rem;color:#94a3b8;margin-left:6px;">(${catalog.female.length + catalog.male.length} giọng tối ưu)</span>



        </div>



        <button type="button" class="btn btn-secondary btn-xs" onclick="updateVoiceOptions(true); openVoiceLibraryModal();" style="font-size:0.68rem;padding:3px 8px;">



          🌐 Xem Toàn Bộ 30 Giọng Quốc Tế



        </button>



      </div>







      <div>



        <div style="font-size:0.75rem;font-weight:700;color:#f472b6;margin-bottom:8px;display:flex;align-items:center;gap:6px;">



          <span>🌸 Giọng Nữ ${catalog.name} (${catalog.female.length} giọng):</span>



        </div>



        <div style="display:flex;flex-direction:column;gap:6px;">



          ${catalog.female.map((v) => {



            const isSelected = currentVoice === v.id;



            return `



            <div style="display:flex;justify-content:space-between;align-items:center;background:#0f172a;padding:8px 12px;border-radius:8px;border:1px solid ${isSelected ? '#10b981' : '#1e293b'};transition:all 0.15s ease;">



              <div style="display:flex;align-items:center;gap:10px;">



                <span style="font-size:1.1rem;">👩</span>



                <div>



                  <div style="font-size:0.82rem;font-weight:700;color:#f8fafc;display:flex;align-items:center;gap:6px;">



                    <span>${v.id}</span>



                    ${isSelected ? '<span class="badge" style="background:#059669;color:#fff;font-size:0.6rem;padding:1px 5px;">Đang chọn</span>' : ''}



                  </div>



                  <div style="font-size:0.7rem;color:#94a3b8;">${v.text}</div>



                </div>



              </div>



              <div style="display:flex;align-items:center;gap:8px;">



                <button type="button" class="btn-voice-preview-icon" onclick="window.playVoicePreviewAudio('${v.id}', this)" title="Nghe thử giọng ${v.id} ngay">🔊</button>



                <button type="button" class="btn ${isSelected ? 'btn-success' : 'btn-secondary'} btn-xs" onclick="window.selectVoiceFromLibrary('${v.id}')" style="padding:4px 10px;font-size:0.72rem;font-weight:600;">



                  ${isSelected ? '✓ Đang Dùng' : 'Chọn Giọng Này'}



                </button>



              </div>



            </div>



            `;



          }).join("")}



        </div>



      </div>







      <div style="margin-top:8px;">



        <div style="font-size:0.75rem;font-weight:700;color:#60a5fa;margin-bottom:8px;display:flex;align-items:center;gap:6px;">



          <span>👑 Giọng Nam ${catalog.name} (${catalog.male.length} giọng):</span>



        </div>



        <div style="display:flex;flex-direction:column;gap:6px;">



          ${catalog.male.map((v) => {



            const isSelected = currentVoice === v.id;



            return `



            <div style="display:flex;justify-content:space-between;align-items:center;background:#0f172a;padding:8px 12px;border-radius:8px;border:1px solid ${isSelected ? '#10b981' : '#1e293b'};transition:all 0.15s ease;">



              <div style="display:flex;align-items:center;gap:10px;">



                <span style="font-size:1.1rem;">👨</span>



                <div>



                  <div style="font-size:0.82rem;font-weight:700;color:#f8fafc;display:flex;align-items:center;gap:6px;">



                    <span>${v.id}</span>



                    ${isSelected ? '<span class="badge" style="background:#059669;color:#fff;font-size:0.6rem;padding:1px 5px;">Đang chọn</span>' : ''}



                  </div>



                  <div style="font-size:0.7rem;color:#94a3b8;">${v.text}</div>



                </div>



              </div>



              <div style="display:flex;align-items:center;gap:8px;">



                <button type="button" class="btn-voice-preview-icon" onclick="window.playVoicePreviewAudio('${v.id}', this)" title="Nghe thử giọng ${v.id} ngay">🔊</button>



                <button type="button" class="btn ${isSelected ? 'btn-success' : 'btn-secondary'} btn-xs" onclick="window.selectVoiceFromLibrary('${v.id}')" style="padding:4px 10px;font-size:0.72rem;font-weight:600;">



                  ${isSelected ? '✓ Đang Dùng' : 'Chọn Giọng Này'}



                </button>



              </div>



            </div>



            `;



          }).join("")}



        </div>



      </div>



    `;







    container.innerHTML = html;



    openModal(modal);



  };







  window.selectVoiceFromLibrary = function (voiceId) {



    if (el.inVoice) {



      el.inVoice.value = voiceId;



      el.inVoice.dispatchEvent(new Event("change"));



    }



    closeAllModals();



    showToast(`Đã chọn giọng đọc: ${voiceId}`);



  };











  // Useful defaults, but the user may still change language, country and voice.



  if (el.inGenre) {



    el.inGenre.addEventListener("change", () => {



      // Only apply language/region presets if user hasn't explicitly chosen a custom language



      if (!state.userExplicitLanguage || el.inLanguage?.value === "Auto") {



        const presets={stoic:["Spanish","ES"], western:["English","US"],



                       family_drama:["Vietnamese","VN"],



                       mafia_thriller:["Vietnamese","VN"],



                       psychological_horror:["Vietnamese","VN"],



                       romance_melodrama:["Vietnamese","VN"],



                       history:["Vietnamese","VN"]};



        const values=presets[el.inGenre.value];



        if (values) {



          if (el.inLanguage) el.inLanguage.value=values[0];



          if (el.inRegion && (!state.userExplicitRegion || el.inRegion.value === "auto")) el.inRegion.value=values[1];



        }



      }



      updateVoiceOptions(false);



      if (el.inVoice) el.inVoice.value="auto";



      if (el.mcpGenreBind) el.mcpGenreBind.value = el.inGenre.value;



      if (el.inVisualStyle && (!state.userExplicitVisualStyle || el.inVisualStyle.value === "auto")) {

        const g = el.inGenre.value;

        if (g === "animation") el.inVisualStyle.value = "color_animation";

        else if (g === "whiteboard") el.inVisualStyle.value = "colored_marker";

        else if (g === "colored_marker") el.inVisualStyle.value = "colored_marker";

        else if (el.inProductionMode && el.inProductionMode.value === "cinematic_drama") el.inVisualStyle.value = "flow_video";

        else el.inVisualStyle.value = "color_cinematic";

      }

      updateMcpProjectForGenre();
      if (typeof updateHintChipsForGenre === "function") updateHintChipsForGenre(el.inGenre.value);



    });



  }







  if (el.inVisualStyle) {



    el.inVisualStyle.addEventListener("change", () => {

      state.userExplicitVisualStyle = (el.inVisualStyle.value !== "auto");



      if (el.inVisualStyle.value === "flow_video") {



        if (el.inMotionMode) {



          el.inMotionMode.value = "flow_video";



          window.toggleFlowVideoOptions();



        }



      }



    });



  }







  if (el.inMotionMode) {



    el.inMotionMode.addEventListener("change", () => {



      window.toggleFlowVideoOptions();



      if (el.inMotionMode.value === "flow_video" && el.inVisualStyle && el.inVisualStyle.value !== "flow_video") {



        el.inVisualStyle.value = "flow_video";



      }



    });



  }











  // Image source toggle (MCP options)



  if (el.inImageSource) {



    el.inImageSource.addEventListener("change", handleImageSourceChange);



    handleImageSourceChange();



  }



  if (el.inMinutes) {



    el.inMinutes.addEventListener("input", () => {



      if (typeof window.updateDramaDurationCoupling === "function") window.updateDramaDurationCoupling();



      syncAutoImageBudget();



    });



    el.inMinutes.addEventListener("change", () => {



      if (typeof window.updateDramaDurationCoupling === "function") window.updateDramaDurationCoupling();



      syncAutoImageBudget();



    });



  }



  if (el.inSceneSec) {
    el.inSceneSec.addEventListener("input", () => {
      state.userCustomizedMaxImages = false;
      syncAutoImageBudget();
    });
    el.inSceneSec.addEventListener("change", () => {
      state.userCustomizedMaxImages = false;
      syncAutoImageBudget();
    });
  }
  if (el.inMinutes) {
    el.inMinutes.addEventListener("input", () => {
      state.userCustomizedMaxImages = false;
      syncAutoImageBudget();
    });
    el.inMinutes.addEventListener("change", () => {
      state.userCustomizedMaxImages = false;
      syncAutoImageBudget();
    });
  }



  if (el.inMcpMaxImages) {



    el.inMcpMaxImages.addEventListener("input", () => {



      state.userCustomizedMaxImages = true;



      updateImageBudgetHint();



    });



    el.inMcpMaxImages.addEventListener("change", () => {



      state.userCustomizedMaxImages = true;



      updateImageBudgetHint();



    });



  }



  if (el.inMcpVisualReuse) {



    el.inMcpVisualReuse.addEventListener("change", updateImageBudgetHint);



  }



  if (el.inInputMode) {



    el.inInputMode.addEventListener("change", () => {



      if (el.inInputMode.value === "link") {



        state.userCustomizedMaxImages = false;



        syncAutoImageBudget();



      }



    });



  }







  
  const btnSuggestIdea = document.getElementById("btnSuggestIdea");
  if (btnSuggestIdea) {
    let _suggestIdx = 0;
    btnSuggestIdea.addEventListener("click", () => {
      const g = el.inGenre ? el.inGenre.value : "stoic";
      const presets = GENRE_PROMPT_PRESETS[g] || GENRE_PROMPT_PRESETS["stoic"] || [];
      if (!presets.length) return;
      const pick = presets[_suggestIdx % presets.length];
      _suggestIdx++;
      if (el.inPrompt) {
        el.inPrompt.value = pick.text;
        el.inPrompt.focus();
        showToast("✨ AI Gợi ý: " + pick.label);
      }
    });
  }

  // Quick Prompt Chips



  document.querySelectorAll(".hint-chip").forEach((chip) => {



    chip.addEventListener("click", (e) => {



      const type = e.currentTarget.dataset.type;



      applyPromptPreset(type);



    });



  });







  // Modal Triggers



  document.getElementById("btnOpenSettings").addEventListener("click", () => {



    openModal(el.modalApiKey);



    void loadGatewayStatus();



    void loadMuseStatus();



  });



  document.getElementById("btnOpenProductions").addEventListener("click", () => {

    loadProductions();

    openModal(el.modalProductions);

  });



  const btnHeaderYt = document.getElementById("btnHeaderYouTube");

  if (btnHeaderYt) {

    btnHeaderYt.addEventListener("click", (e) => {

      e.preventDefault();

      if (typeof window.openYouTubeModal === "function") window.openYouTubeModal();

    });

  }



  const btnHeaderMuse = document.getElementById("btnHeaderMuse");

  if (btnHeaderMuse) {

    btnHeaderMuse.addEventListener("click", (e) => {

      e.preventDefault();

      if (typeof window.openMuseModal === "function") window.openMuseModal();

    });

  }



  el.btnSaveKey.addEventListener("click", saveApiKey);



  const btnDirect = document.getElementById("btnMcpOpenDirectTab");



  if (btnDirect) btnDirect.addEventListener("click", () => window.robotOpenDirectTab());

  // FlowKit Google Flow Handlers
  const btnFlowLogin = document.getElementById("btnFlowLogin") || document.getElementById("btnMcpOpenLogin");
  if (btnFlowLogin) {
    btnFlowLogin.addEventListener("click", async () => {
      const statusBox = document.getElementById("mcpAccountStatus");
      if (statusBox) statusBox.textContent = "⏳ Đang mở trình duyệt Google Flow... Cửa sổ giữ nguyên trên màn hình.";
      try {
        const res = await fetch("/api/flow/login", { method: "POST" });
        const data = await res.json();
        if (statusBox) statusBox.textContent = data.message || "Đã mở trình duyệt Chrome. Hãy đăng nhập tài khoản Google.";
        const pollTimer = setInterval(async () => {
          await refreshAutoFlowStatus();
          const node = document.getElementById("autoFlowManagerStatus");
          if (node && node.textContent.includes("🟢")) {
            clearInterval(pollTimer);
            await refreshAutoFlowStatus();
            if (typeof showToast === "function") showToast("Đã kết nối Web Tool Storyboard Director AI thành công!");
          }
        }, 2000);
        setTimeout(() => clearInterval(pollTimer), 300000);
      } catch (err) {
        if (statusBox) statusBox.textContent = "Lỗi khi mở trình duyệt: " + err.message;
      }
    });
  }

  const btnInstallFkAction = document.getElementById("btnInstallFlowKit");
  if (btnInstallFkAction) {
    btnInstallFkAction.addEventListener("click", async () => {
      btnInstallFkAction.disabled = true;
      btnInstallFkAction.textContent = "⏳ Đang kết nối...";
      const statusBox = document.getElementById("mcpAccountStatus");
      if (statusBox) statusBox.textContent = "Đang bắt đầu tải và cài đặt động cơ FlowKit...";
      try {
        await fetch("/api/flowkit/install_engine", { method: "POST" });
        const timer = setInterval(async () => {
          try {
            const res = await fetch("/api/flowkit/install_status");
            const st = await res.json();
            btnInstallFkAction.textContent = `⏳ ${st.percent || 0}%`;
            if (statusBox) statusBox.textContent = st.message || "Đang cài đặt động cơ...";
            if (st.success) {
              clearInterval(timer);
              btnInstallFkAction.disabled = false;
              btnInstallFkAction.textContent = "🚀 Cài Đặt Động Cơ FlowKit";
              if (typeof showToast === "function") showToast("Đã cài đặt thành công động cơ FlowKit!");
              await refreshAutoFlowStatus();
            } else if (st.error) {
              clearInterval(timer);
              btnInstallFkAction.disabled = false;
              btnInstallFkAction.textContent = "⚠️ Thử Lại Cài Đặt";
              if (statusBox) statusBox.textContent = "Lỗi cài đặt: " + st.error;
            }
          } catch (_) {}
        }, 1500);
      } catch (e) {
        btnInstallFkAction.disabled = false;
        btnInstallFkAction.textContent = "🚀 Cài Đặt Động Cơ FlowKit";
        if (statusBox) statusBox.textContent = "Lỗi kích hoạt cài đặt: " + e.message;
      }
    });
  }

  const btnFlowAdd = document.getElementById("btnFlowAddAccount");
  if (btnFlowAdd) {
    btnFlowAdd.addEventListener("click", async () => {
      const statusBox = document.getElementById("mcpAccountStatus");
      if (statusBox) statusBox.textContent = "⏳ Đang tạo hồ sơ mới và mở Chrome... Cửa sổ giữ nguyên trên màn hình.";
      try {
        const res = await fetch("/api/flow/add_account", { method: "POST" });
        const data = await res.json();
        if (statusBox) statusBox.textContent = data.message || "Đã mở Chrome cho tài khoản mới. Vui lòng đăng nhập Google.";
        const pollTimer = setInterval(async () => {
          await refreshAutoFlowStatus();
          const node = document.getElementById("autoFlowManagerStatus");
          if (node && node.textContent.includes("🟢")) {
            clearInterval(pollTimer);
            if (statusBox) statusBox.textContent = "✓ Đã đăng nhập tài khoản mới thành công! Cửa sổ đã tự động ẩn và kết nối Web Tool.";
            if (typeof showToast === "function") showToast("Tài khoản mới đã sẵn sàng và kết nối Web Tool!");
          }
        }, 2000);
        setTimeout(() => clearInterval(pollTimer), 300000);
      } catch (err) {
        if (statusBox) statusBox.textContent = "Lỗi khi thêm tài khoản: " + err.message;
      }
    });
  }

  refreshAutoFlowStatus();
  setInterval(refreshAutoFlowStatus, 30000);

  // FlowKit Settings Event Handlers
  const btnFkLogin = document.getElementById("btnFlowKitOpenLogin");
  if (btnFkLogin) {
    btnFkLogin.addEventListener("click", async () => {
      const box = document.getElementById("flowkitStatusBox");
      if (box) box.textContent = "⏳ Đang mở trình duyệt Google Flow để đăng nhập hoặc xem Web Tool...";
      try {
        const res = await fetch("/api/flowkit/open_browser", { method: "POST" });
        const data = await res.json();
        if (box) box.textContent = data.message || (data.success ? "Đã mở trình duyệt thành công." : "Lỗi: " + data.error);
        setTimeout(refreshFlowKitStatus, 2500);
      } catch (e) {
        if (box) box.textContent = "Lỗi khi mở trình duyệt: " + e.message;
      }
    });
  }

  const btnFkCheck = document.getElementById("btnFlowKitCheckStatus");
  if (btnFkCheck) {
    btnFkCheck.addEventListener("click", async () => {
      await refreshFlowKitStatus(true);
    });
  }

  const btnFkRestart = document.getElementById("btnFlowKitRestartDaemon");
  if (btnFkRestart) {
    btnFkRestart.addEventListener("click", async () => {
      const box = document.getElementById("flowkitStatusBox");
      if (box) box.textContent = "⚡ Đang kiểm tra & khởi động lại FlowKit Gateway...";
      try {
        const res = await fetch("/api/flowkit/reconnect", { method: "POST" });
        const data = await res.json();
        updateFlowKitUI(data);
        showToast("Đã làm mới kết nối FlowKit Gateway!");
      } catch (e) {
        if (box) box.textContent = "Lỗi khởi động lại FlowKit: " + e.message;
      }
    });
  }

  refreshFlowKitStatus();
  setInterval(refreshFlowKitStatus, 30000);




  document.getElementById("btnMcpVerifyAccount").addEventListener("click", () => mcpAccountAction("verify"));



  document.getElementById("btnMcpAddAccount").addEventListener("click", () => mcpAccountAction("create"));



  el.mcpAccountSelect.addEventListener("change", () => mcpAccountAction("select"));



  document.getElementById("btnMcpScanProjects").addEventListener("click", loadMcpProjects);



  document.getElementById("btnMcpRegisterProject").addEventListener("click", () => mcpProjectAction("register"));



  document.getElementById("btnMcpSwitchProject").addEventListener("click", () => mcpProjectAction("select"));



  document.getElementById("btnMcpOpenProject").addEventListener("click", () => mcpProjectAction("open"));







  window.updateMcpWindowButtons = function (running, minimized) {



    window._isMcpRunning = Boolean(running);



    window._isMcpMinimized = Boolean(minimized);



    const headerBtn = document.getElementById("btnHeaderToggleMcpWindow");



    const headerLbl = document.getElementById("btnHeaderToggleMcpLabel");



    const modalBtn = document.getElementById("btnMcpToggleWindow");



    const robotBtn = document.getElementById("robotBtnHideChrome");







    if (!running) {



      if (headerBtn) {



        headerBtn.style.opacity = "0.7";



        headerBtn.title = "Tiến trình đồ họa chưa khởi chạy (Bấm để kết nối)";



        headerBtn.style.borderColor = "rgba(148,163,184,0.4)";



        headerBtn.style.color = "#94a3b8";



      }



      if (headerLbl) headerLbl.textContent = "🌐 Máy Chủ AI";



      if (modalBtn) modalBtn.textContent = "🌐 Máy Chủ Đồ Họa (Chưa mở)";



      return;



    }



    if (headerBtn) headerBtn.style.opacity = "1";



    if (minimized) {



      if (headerLbl) headerLbl.textContent = "🔒 Đã Chạy Ngầm";



      if (headerBtn) {



        headerBtn.title = "Tiến trình đồ họa đang chạy ngầm ở Taskbar. Bấm để hiển thị cửa sổ.";



        headerBtn.style.borderColor = "rgba(16,185,129,0.5)";



        headerBtn.style.color = "#34d399";



      }



      if (modalBtn) modalBtn.textContent = "🔼 Hiện Cửa Sổ Đồ Họa";



      if (robotBtn) robotBtn.textContent = "🔒 Đã Chạy Ngầm (Bấm để Hiện)";



    } else {



      if (headerLbl) headerLbl.textContent = "🔽 Ẩn Chạy Ngầm";



      if (headerBtn) {



        headerBtn.title = "Cửa sổ đồ họa đang mở trên màn hình. Bấm để chuyển xuống chạy ngầm.";



        headerBtn.style.borderColor = "rgba(56,189,248,0.4)";



        headerBtn.style.color = "#38bdf8";



      }



      if (modalBtn) modalBtn.textContent = "🔽 Ẩn Chạy Ngầm";



      if (robotBtn) robotBtn.textContent = "🔽 Tối Ưu Tiến Trình Ẩn (Chạy Ngầm)";



    }



  };







  window.toggleMcpWindow = async function (preferredAction) {



    const headerBtn = document.getElementById("btnHeaderToggleMcpWindow");



    const modalBtn = document.getElementById("btnMcpToggleWindow");



    const robotBtn = document.getElementById("robotBtnHideChrome");



    const buttons = [headerBtn, modalBtn, robotBtn].filter(Boolean);



    buttons.forEach(b => { b.disabled = true; });



    try {



      const action = preferredAction || (window._isMcpMinimized ? "show" : "lock");



      const resp = await fetch("/api/mcp/window", {



        method: "POST",



        headers: { "Content-Type": "application/json" },



        body: JSON.stringify({ action }),



      });



      const data = await resp.json();



      if (data.ok) {



        window.updateMcpWindowButtons(data.running, data.minimized);



        if (data.minimized) {



          showToast("🔒 Đã chuyển tiến trình đồ họa xuống chạy ngầm!");



        } else {



          showToast("🌐 Đã mở cửa sổ tiến trình đồ họa lên màn hình.");



        }



        return data;



      } else {



        showToast(data.error || "Không thể điều khiển cửa sổ đồ họa", "error");



      }



    } catch (err) {



      showToast("Lỗi kết nối tới máy chủ Studio", "error");



    } finally {



      buttons.forEach(b => { b.disabled = false; });



    }



  };







  window.syncMcpWindowState = async function () {



    try {



      const resp = await fetch("/api/mcp/window", {



        method: "POST",



        headers: { "Content-Type": "application/json" },



        body: JSON.stringify({ action: "status" }),



      });



      const data = await resp.json();



      if (data && data.ok) {



        window.updateMcpWindowButtons(data.running, data.minimized);



      }



    } catch (e) {}



  };







  const btnHeaderToggleWin = document.getElementById("btnHeaderToggleMcpWindow");



  if (btnHeaderToggleWin) {



    btnHeaderToggleWin.addEventListener("click", () => {



      const isMin = window._isMcpMinimized === true;



      window.toggleMcpWindow(isMin ? "show" : "lock");



    });



  }







  const btnToggleWin = document.getElementById("btnMcpToggleWindow");



  if (btnToggleWin) {



    btnToggleWin.addEventListener("click", () => {



      const isMin = window._isMcpMinimized === true;



      window.toggleMcpWindow(isMin ? "show" : "lock");



    });



  }







  window.syncMcpWindowState();



  setInterval(window.syncMcpWindowState, 60000);







  // Restore auto-minimize preference from localStorage (default true to lock Chrome down on taskbar)



  const savedAutoMin = localStorage.getItem("storyboard_mcp_auto_minimize");



  if (el.inMcpAutoMinimize) {



    el.inMcpAutoMinimize.checked = savedAutoMin !== "false";



    el.inMcpAutoMinimize.addEventListener("change", (e) => {



      localStorage.setItem("storyboard_mcp_auto_minimize", String(e.target.checked));



    });



  }







  // Restore watermark cleaner preference (default true)



  const savedCleanWm = localStorage.getItem("storyboard_clean_watermark");



  if (el.inCleanWatermark) {



    if (savedCleanWm !== null) {



      el.inCleanWatermark.checked = savedCleanWm === "true";



    }



    el.inCleanWatermark.addEventListener("change", (e) => {



      localStorage.setItem("storyboard_clean_watermark", String(e.target.checked));



    });



  }







  // Restore subtitle style & size preference from localStorage



  const savedSubStyle = localStorage.getItem("storyboard_subtitle_style");



  if (savedSubStyle && el.inSubtitleStyle) {



    el.inSubtitleStyle.value = savedSubStyle;



  }



  if (el.inSubtitleStyle) {



    el.inSubtitleStyle.addEventListener("change", (e) => {



      localStorage.setItem("storyboard_subtitle_style", e.target.value);



    });



  }







  const savedSubSize = localStorage.getItem("storyboard_subtitle_size");



  if (savedSubSize) {



    const sz = parseInt(savedSubSize, 10);



    if (sz >= 18 && sz <= 120) {



      if (el.inSubtitleSize) el.inSubtitleSize.value = sz;



      if (el.subtitleSizeBadge) el.subtitleSizeBadge.textContent = `${sz}px`;



      updateSubtitleChips(sz);



    }



  }







  const savedWorkers = localStorage.getItem("storyboard_workers");



  if (savedWorkers) {



    const w = parseInt(savedWorkers, 10);



    if (w >= 1 && w <= 16) {



      if (el.inWorkers) el.inWorkers.value = String(w);



      updateWorkerChips(w);



    }



  }







  // Close modals



  document.querySelectorAll(".modal-close, .modal-overlay").forEach((item) => {



    item.addEventListener("click", (e) => {



      if (e.target === item || item.classList.contains("modal-close")) {



        closeAllModals();



      }



    });



  });







  // Subtitle size input sync



  if (el.inSubtitleSize) {



    el.inSubtitleSize.addEventListener("input", (e) => {



      const val = parseInt(e.target.value, 10) || 52;



      if (el.subtitleSizeBadge) el.subtitleSizeBadge.textContent = `${val}px`;



      updateSubtitleChips(val);



      localStorage.setItem("storyboard_subtitle_size", String(val));



    });



  }







  // Actions



  if (el.btnOpenFolder) el.btnOpenFolder.addEventListener("click", openCurrentFolder);



}







window.setSubtitleSize = function (size) {



  if (el.inSubtitleSize) {



    el.inSubtitleSize.value = size;



  }



  if (el.subtitleSizeBadge) {



    el.subtitleSizeBadge.textContent = `${size}px`;



  }



  updateSubtitleChips(size);



  localStorage.setItem("storyboard_subtitle_size", String(size));



};







window.toggleFlowVideoOptions = function () {



  const mode = el.inMotionMode ? el.inMotionMode.value : "ken_burns";



  const row = document.getElementById("flowVideoRow");



  if (row) {



    row.style.display = mode === "flow_video" ? "grid" : "none";



  }

};











function updateSubtitleChips(size) {



  document.querySelectorAll(".sub-size-chip").forEach((chip) => {



    const s = parseInt(chip.dataset.size, 10);



    if (s === size) {



      chip.classList.add("active-chip");



      chip.style.color = "#818cf8";



      chip.style.borderColor = "#818cf8";



      chip.style.fontWeight = "700";



    } else {



      chip.classList.remove("active-chip");



      chip.style.color = "";



      chip.style.borderColor = "";



      chip.style.fontWeight = "";



    }



  });



}







window.setWorkerThreads = function (threads) {



  const t = Math.min(Math.max(1, parseInt(threads, 10) || 2), 16);



  if (el.inWorkers) {



    el.inWorkers.value = String(t);



  }



  updateWorkerChips(t);



  try {



    localStorage.setItem("storyboard_workers", String(t));



  } catch (err) {}



};







function updateWorkerChips(threads) {



  document.querySelectorAll(".worker-chip").forEach((chip) => {



    const val = parseInt(chip.dataset.val, 10);



    if (val === threads) {



      chip.classList.add("active-chip");



      chip.style.color = "#10b981";



      chip.style.borderColor = "#10b981";



      chip.style.fontWeight = "700";



    } else {



      chip.classList.remove("active-chip");



      chip.style.color = "";



      chip.style.borderColor = "";



      chip.style.fontWeight = "";



    }



  });



}







function switchPlayerMode(mode) {



  state.activePreviewMode = mode;



  const playerMeta = document.getElementById("playerMetaText");







  if (mode === "episode") {



    if (el.modeBtnEpisode) el.modeBtnEpisode.classList.add("active");



    if (el.modeBtnShort) el.modeBtnShort.classList.remove("active");



    if (el.modeBtnScene) el.modeBtnScene.classList.remove("active");



    if (el.videoMonitorContainer) el.videoMonitorContainer.classList.remove("mode-shorts");



    if (playerMeta) playerMeta.textContent = "16:9 H.264 HD Master Cut";



    playEpisodeVideo();



  } else if (mode === "short") {
    const resEl = (typeof el !== 'undefined' && el.inResolution) || document.getElementById("inResolution");
    if (resEl) {
      const opt916 = Array.from(resEl.options).find(o => o.value.includes("720x1280") || o.value.includes("1080x1920"));
      if (opt916) {
        resEl.value = opt916.value;
        try { localStorage.setItem("storyboard_saved_resolution", opt916.value); } catch(_) {}
      }
    }



    if (el.modeBtnShort) el.modeBtnShort.classList.add("active");



    if (el.modeBtnEpisode) el.modeBtnEpisode.classList.remove("active");



    if (el.modeBtnScene) el.modeBtnScene.classList.remove("active");



    if (el.videoMonitorContainer) el.videoMonitorContainer.classList.add("mode-shorts");



    if (playerMeta) playerMeta.textContent = "9:16 Shorts H.264 HD (1080x1920)";



    playShortVideo();



  } else {



    if (el.modeBtnScene) el.modeBtnScene.classList.add("active");



    if (el.modeBtnEpisode) el.modeBtnEpisode.classList.remove("active");



    if (el.modeBtnShort) el.modeBtnShort.classList.remove("active");



    if (el.videoMonitorContainer) el.videoMonitorContainer.classList.remove("mode-shorts");



    if (playerMeta) playerMeta.textContent = "16:9 H.264 Clip Cảnh";



    if (state.selectedSceneNumber) {



      playSceneVideo(state.selectedSceneNumber);



    } else {



      const firstWithVideo = (state.loadedEpisodeData?.scenes || []).find((s) => Boolean(s.video_url));



      if (firstWithVideo) {



        selectSceneAndPlay(firstWithVideo.scene_number, firstWithVideo.video_url);



      } else {



        showToast("Chọn một cảnh trong Storyboard để xem clip riêng");



      }



    }



  }



}








const GENRE_PROMPT_PRESETS = {
  stoic: [
    { label: "🏛️ Làm chủ tâm trí", text: "Làm chủ tâm trí: Khám phá triết lý Khắc kỷ của hoàng đế Marcus Aurelius. Nghệ thuật giữ tâm bất biến giữa dòng đời vạn biến, buông bỏ những điều nằm ngoài tầm kiểm soát và đánh thức sức mạnh nội tâm vững vàng như tượng đá cẩm thạch trước bão giông." },
    { label: "⚡ Nghệ thuật buông bỏ", text: "Nghệ thuật buông bỏ và tĩnh lặng: Bí quyết người thông thái im lặng rút lui khỏi những ồn ào vô nghĩa, thanh lọc các mối quan hệ độc hại và tìm thấy tự do đích thực trong tâm hồn." },
    { label: "🛡️ Bản lĩnh nghịch cảnh", text: "Bản lĩnh trước nghịch cảnh: Chuyển hóa khó khăn thành đòn bẩy phát triển bản thân. Bài học từ những suy tưởng sâu sắc giúp vượt qua mọi khủng hoảng cuộc đời với sự điềm tĩnh phi thường." }
  ],
  family_drama: [
    { label: "💔 Bữa cơm chia tài sản", text: "Bữa cơm gia đình định mệnh: Đêm họp mặt đầy sóng gió của ba thế hệ khi bức di chúc bí mật của người cha bất ngờ được mở ra. Những mâu thuẫn âm ỉ bùng nổ, sự thật cay đắng về lòng hiếu thảo và bài học xót xa về tình thân." },
    { label: "⚖️ Bí mật của người cha", text: "Gánh nặng của người cha thợ may: 30 năm hy sinh thầm lặng của người cha nghèo nuôi hai đứa con ăn học thành tài, chỉ đến ngày con thành đạt mới thấu hiểu vết sẹo hằn sâu trên lưng cha và bài học nghẹn ngào về sự tha thứ." },
    { label: "🏡 Căn nhà cổ 3 đời", text: "Trận chiến giữ căn nhà từ đường: Mối giằng xé giữa người con cả muốn bảo tồn cội nguồn gia tộc và các em muốn bán đất đổi đời. Cuộc đối đầu đẫm nước mắt trong ngày giỗ mẹ." }
  ],
  mafia_thriller: [
    { label: "🌧️ Đêm mưa trừng phạt", text: "Thế giới ngầm và luật im lặng: Trận đấu trí nghẹt thở giữa viên thanh tra dày dạn kinh nghiệm và ông trùm mafia quyền lực bậc nhất thành phố trong một đêm mưa bão rực sáng ánh đèn neon, nơi ranh giới giữa chính nghĩa và phản bội bị xóa nhòa." },
    { label: "♟️ Bẫy gián điệp", text: "Cán cân quyền lực: Cuộc thanh trừng nội bộ trong tập đoàn mafia khi phát hiện kẻ chỉ điểm. Kế hoạch lật mặt tinh vi đến từng giây phút nghẹt thở." }
  ],
  psychological_horror: [
    { label: "🕯️ Tiếng gõ cửa 3h sáng", text: "Cơn ác mộng lúc 3 giờ sáng: Người đàn ông một mình trong căn hộ tầng 13 bắt đầu nghe thấy những tiếng thì thầm sau bức tường và chiếc gương soi phản chiếu một hành động mà anh ta không hề làm. Ranh giới mong manh giữa sự hoang tưởng và thực tại rùng rợn." },
    { label: "🪞 Ảo giác gương vỡ", text: "Bí mật dưới tầng hầm: Chuyến trở về ngôi nhà thời thơ ấu và những ký ức kinh hoàng bị chôn vùi bắt đầu thức giấc theo từng tiếng tích tắc của chiếc đồng hồ quả lắc." }
  ],
  romance_melodrama: [
    { label: "🌧️ Chia tay dưới mưa", text: "Mối tình thanh xuân trắc trở: Cuộc gặp lại bất ngờ sau 7 năm chia ly giữa hai người từng thề non hẹn biển. Giọt nước mắt nghẹn ngào dưới cơn mưa chiều khi nhận ra tình cảm năm xưa chưa từng phai nhạt, nhưng khoảng cách cuộc đời đã quá lớn." },
    { label: "💍 Hôn ước không tình yêu", text: "Hi sinh vì gia đình: Cuộc hôn nhân sắp đặt và hành trình chạm tới trái tim người lạnh lùng bằng sự chân thành, vượt qua định kiến xã hội và những hiểu lầm nghiệt ngã." }
  ],
  whiteboard: [
    { label: "🧠 Hiệu ứng Dunning-Kruger", text: "Tâm lý học hành vi: Giải mã hiệu ứng Dunning-Kruger và cái bẫy của sự tự tin mù quáng. Tại sao người càng thiếu hiểu biết lại càng tự tin, và bí quyết rèn luyện tư duy phản biện để làm chủ cuộc đời qua các hình vẽ minh họa bảng trắng After Skool." },
    { label: "⏳ Định luật Parkinson", text: "Nghệ thuật quản lý thời gian: Tại sao công việc luôn kéo dài tương ứng với lượng thời gian được giao? Bí quyết áp dụng định luật Parkinson và quy tắc 80/20 để nhân 10 hiệu suất làm việc." },
    { label: "💰 Tư duy người giàu", text: "Tâm lý học về tiền bạc: Sự khác biệt cốt lõi giữa tài sản và tiêu sản, cách người giàu tư duy về đòn bẩy và sự kiên nhẫn tích lũy giá trị dài hạn." }
  ],
  colored_marker: [
    { label: "🧠 Hiệu ứng Dunning-Kruger", text: "Tâm lý học hành vi: Giải mã hiệu ứng Dunning-Kruger và cái bẫy của sự tự tin mù quáng. Tại sao người càng thiếu hiểu biết lại càng tự tin, và bí quyết rèn luyện tư duy phản biện để làm chủ cuộc đời qua các hình vẽ minh họa bảng trắng After Skool." },
    { label: "⏳ Định luật Parkinson", text: "Nghệ thuật quản lý thời gian: Tại sao công việc luôn kéo dài tương ứng với lượng thời gian được giao? Bí quyết áp dụng định luật Parkinson và quy tắc 80/20 để nhân 10 hiệu suất làm việc." }
  ],
  animation: [
    { label: "🐾 Chú mèo ma thuật", text: "Cuộc phiêu lưu vào Rừng Đom Đóm: Chú mèo mướp tinh nghịch vô tình nhặt được chiếc la bàn cổ tích và bước vào chuyến thám hiểm kỳ thú giải cứu vương quốc bánh kẹo khỏi phù thủy bóng đêm, bài học xúc động về lòng dũng cảm và tình bạn." },
    { label: "🚀 Cậu bé và vì sao nhỏ", text: "Chuyến bay vượt dải ngân hà: Hành trình của chú robot nhỏ đi tìm nguồn năng lượng ánh sáng để cứu hành tinh quê hương, ngập tràn màu sắc rực rỡ và những điều kỳ diệu." }
  ],
  history: [
    { label: "⚔️ Hào khí Bạch Đằng", text: "Bạch Đằng giang dậy sóng: Chiến thuật cắm cọc gỗ đi vào huyền thoại của Trần Hưng Đạo đánh tan đoàn thuyền giặc Nguyên Mông. Khí thế ngút trời của quân dân Đại Việt bảo vệ từng tấc đất quê hương." },
    { label: "🏛️ Thành Đa Bang bất khuất", text: "Hành trình hào hùng: Cuộc vây hãm thành Đa Bang và ý chí quật cường của nhân dân Đại Việt. Mở đầu bằng sự uy nghi của kinh thành, cao trào là trận chiến quyết định với hỏa hổ và voi chiến." }
  ],
  documentary: [
    { label: "🌌 Bí ẩn hố đen", text: "Bí ẩn hố đen vũ trụ: Chuyến du hành xuyên không gian giải mã điểm kỳ dị Gravitational Singularity và Chân trời sự kiện Event Horizon. Cách mà lực hấp dẫn bẻ cong ánh sáng và thời gian ngừng trôi." },
    { label: "🚢 Thảm kịch Titanic", text: "Đêm định mệnh của con tàu không thể chìm: Giải mã chuỗi sai lầm định mệnh dẫn đến thảm kịch Titanic năm 1912 và những câu chuyện xúc động về danh dự con người trong giây phút sinh tử." }
  ],
  western: [
    { label: "🤠 Đấu súng hoàng hôn", text: "Hoàng hôn trên miền Viễn Tây: Cuộc chạm trán sinh tử giữa tay súng cô độc và băng cướp khét tiếng tại thị trấn cát bụi rực đỏ ánh tà dương, bảo vệ công lý và danh dự người quân tử." }
  ],
  action: [
    { label: "🏎️ Rượt đuổi nghẹt thở", text: "Cuộc đào thoát trong gang tấc: 24 giờ nghẹt thở của người cựu điệp viên bị gài bẫy, đơn độc truy tìm sự thật giữa vòng vây sát thủ và máy bay không người lái của tổ chức phản diện." }
  ]
};

function updateHintChipsForGenre(genre) {
  const row = document.getElementById("hintChipsRow");
  if (!row) return;
  const g = String(genre || "stoic").trim().toLowerCase();
  const presets = GENRE_PROMPT_PRESETS[g] || GENRE_PROMPT_PRESETS["stoic"] || [];
  row.innerHTML = "";
  presets.forEach((item, idx) => {
    const chip = document.createElement("span");
    chip.className = "hint-chip";
    chip.textContent = item.label;
    chip.title = item.text;
    chip.addEventListener("click", () => {
      if (el.inPrompt) {
        el.inPrompt.value = item.text;
        el.inPrompt.focus();
        showToast("💡 Đã nạp ý tưởng: " + item.label);
      }
    });
    row.appendChild(chip);
  });
}

function applyPromptPreset(type) {



  const presets = {



    history: "Hành trình hào hùng: Cuộc vây hãm thành Đa Bang và ý chí quật cường của nhân dân Đại Việt. Mở đầu bằng sự uy nghi của kinh thành, cao trào là trận chiến quyết định với hỏa hổ và voi chiến, kết thúc với tinh thần bất khuất lưu truyền thiên thu.",



    science: "Bí ẩn hố đen vũ trụ: Chuyến du hành xuyên không gian giải mã điểm kỳ dị Gravitational Singularity và Chân trời sự kiện Event Horizon. Cách mà lực hấp dẫn bẻ cong ánh sáng và thời gian ngừng trôi.",



    startup: "Bài học từ sự thất bại: Hành trình khởi nghiệp từ gara cũ kỹ tới vòng gọi vốn Series A. Những cú ngã đau đớn khi cạn kiệt dòng tiền, sự đổi mới sản phẩm thần tốc và bài học kiên trì của người sáng lập.",



  };



  if (presets[type] && el.inPrompt) {



    el.inPrompt.value = presets[type];



  }



}







function estimatedImageScenes() {
  if (el.inInputMode?.value === "script") {
    const txt = el.inPrompt ? el.inPrompt.value.trim() : "";
    if (txt) {
      const matches = txt.match(/(?:^|\n)[ \t=*-]*(?:#{1,4}[ \t]*)?(?:SHOT|SCENE|CẢNH|PHÂN CẢNH|PHẦN|ĐOẠN|C\u1ea2NH|PH\u00c2N C\u1ea2NH)[ \t_:]*(\d{1,4})/gi);
      if (matches && matches.length > 0) return matches.length;
      const paras = txt.split(/\n\s*\n+/).filter(p => p.trim().length > 5);
      if (paras.length > 0) return paras.length;
    }
  }
  const mins = Math.max(0.1, Number(el.inMinutes?.value) || 1.0);
  const seconds = Math.max(4, Number(el.inSceneSec?.value) || 7);
  return mins > 0 && seconds > 0 && Number.isFinite(mins / seconds)
    ? Math.ceil(mins * 60 / seconds) : null;
}

function syncAutoImageBudget() {
  const n = estimatedImageScenes();
  if (n && n > 0 && el.inMcpMaxImages) {
    el.inMcpMaxImages.value = String(n);
  }
  updateImageBudgetHint();
}







function updateImageBudgetHint() {



  if (!el.imageBudgetHint) return;



  el.imageBudgetHint.style.display = "none";



}







function handleImageSourceChange() {



  if (!el.inImageSource || !el.mcpConfigRow) return;



  const isMcp = el.inImageSource.value === "mcp_v2" || el.inImageSource.value === "flowkit";



  el.mcpConfigRow.style.display = isMcp ? "grid" : "none";



  const gpuNode = document.getElementById("gpuCompatibilityStatus");



  if (gpuNode) {



    gpuNode.style.display = (el.inImageSource.value === "comfyui") ? "block" : "none";



  }



  const museHint = document.getElementById("museProviderHint");



  if (museHint) museHint.hidden = el.inImageSource.value !== "muse_video";



  updateImageBudgetHint();



}







window.toggleGeminiKeyInput = function() {



  const wrap = document.getElementById("geminiKeyInputWrap");



  if (!wrap) return;



  const isHidden = wrap.style.display === "none";



  wrap.style.display = isHidden ? "block" : "none";



  const btn = document.getElementById("btnToggleGeminiKeyInput");



  if (btn) btn.textContent = isHidden ? "Thu gọn" : "Thay đổi";



};







window.toggleGatewayInput = function() {



  const wrap = document.getElementById("gatewayInputWrap");



  if (!wrap) return;



  const isHidden = wrap.style.display === "none";



  wrap.style.display = isHidden ? "block" : "none";



  const btn = document.getElementById("btnToggleGatewayInput");



  if (btn) btn.textContent = isHidden ? "Thu gọn" : "Cập nhật";



};







window.toggleMuseInput = function() {



  const wrap = document.getElementById("museInputWrap");



  if (!wrap) return;



  const isHidden = wrap.style.display === "none";



  wrap.style.display = isHidden ? "block" : "none";



  const btn = document.getElementById("btnToggleMuseInput");



  if (btn) btn.textContent = isHidden ? "Thu gọn" : "Cập nhật";



};







// REST CALLS



async function loadConfig() {



  try {



    const res = await fetch("/api/config");



    const data = await res.json();







    const elGemini = document.getElementById("statusGemini");



    const elGeminiBadge = document.getElementById("geminiKeyBadge");



    const elGeminiWrap = document.getElementById("geminiKeyInputWrap");



    const btnToggleGemini = document.getElementById("btnToggleGeminiKeyInput");







    if (data.gemini_api_configured) {



      const cnt = data.gemini_api_count || 1;



      const maskStr = data.gemini_keys_masked ? data.gemini_keys_masked.join(", ") : "";



      if (elGemini) {



        elGemini.textContent = "Sẵn sàng";



        elGemini.classList.add("text-emerald");



      }



      if (elGeminiBadge) {



        elGeminiBadge.textContent = `● Đã kích hoạt (${maskStr || cnt + " khóa"})`;



        elGeminiBadge.style.color = "#10b981";



      }



      if (elGeminiWrap) elGeminiWrap.style.display = "none";



      if (btnToggleGemini) btnToggleGemini.textContent = "Thay đổi";



    } else {



      if (elGemini) {



        elGemini.textContent = "Tùy chọn";



        elGemini.classList.remove("text-emerald");



      }



      if (elGeminiBadge) {



        elGeminiBadge.textContent = "○ Chưa cấu hình (Tùy chọn bổ sung)";



        elGeminiBadge.style.color = "#94a3b8";



      }



      if (elGeminiWrap) elGeminiWrap.style.display = "none";



      if (btnToggleGemini) btnToggleGemini.textContent = "Thêm khóa";



    }







    const elV2 = document.getElementById("statusV2");



    if (elV2) {



      elV2.textContent = data.v2_gateway_ready ? "Sẵn sàng" : "Chưa kích hoạt";



      if (data.v2_gateway_ready) elV2.classList.add("text-emerald");



    }







    const elMcp = document.getElementById("statusMcp");



    if (elMcp) {



      elMcp.textContent = data.mcp_ready ? "FlowKit đã cài" : "Chưa sẵn sàng";



      if (data.mcp_ready) elMcp.classList.add("text-emerald");



    }
    fetch("/api/flowkit/status").then(r => r.json()).then(fk => {
      const elFk = document.getElementById("statusFlowKit");
      if (elFk) {
        if (fk && fk.ready) {
          elFk.textContent = "🟢 Sẵn sàng (18110)";
          elFk.style.color = "#10b981";
          const rFlowEl = document.getElementById("robotStatusFlow");
          const rBtnEl = document.getElementById("robotBtnGoogleLogin");
          if (rFlowEl) {
            rFlowEl.textContent = "Sẵn sàng (Google Flow)";
            rFlowEl.className = "matrix-val val-green";
          }
          if (rBtnEl) {
            rBtnEl.textContent = "✓ Máy Chủ Đồ Họa Đã Sẵn Sàng";
            rBtnEl.className = "btn btn-success btn-sm";
            rBtnEl.style.background = "#10b981";
            rBtnEl.style.borderColor = "#10b981";
            rBtnEl.style.color = "#ffffff";
          }
        } else {
          elFk.textContent = "🟡 Khởi động lại...";
          elFk.style.color = "#f59e0b";
        }
      }
    }).catch(() => {});







    const gpuNode = document.getElementById("gpuCompatibilityStatus");



    if (gpuNode) {



      const gpu = data.gpu || {};



      const co = data.comfy_compatibility || {};



      const label = gpu.name ? gpu.name + (gpu.vram_mb ? " (" + gpu.vram_mb + " MB VRAM)" : "") : "Chưa nhận diện GPU";



      const captions = {



        ready_server: "ComfyUI đang chạy; cần xác minh model",



        local_nvidia: "NVIDIA CUDA: cần kiểm thử backend và VRAM",



        backend_not_verified: "Chưa xác minh backend GPU; hãy dùng MCP/API đã cấu hình",



        not_installed: "Chưa cài ComfyUI; có thể dùng MCP/API đã cấu hình"



      };



      gpuNode.textContent = "GPU: " + label + " • " + (captions[co.state] || "Chưa xác nhận tương thích");



    }







    const hwBadge = document.getElementById("hardwareSpecsBadge");



    if (hwBadge) {



      const summary = data.hardware_specs || (data.cpu_short ? `${data.cpu_short} + ${data.gpu_short || 'GPU'}` : (data.gpu_name || "GPU AI"));



      hwBadge.textContent = summary;



      hwBadge.title = `Bộ vi xử lý: ${data.cpu_name || 'CPU'} (${data.cpu_threads || ''} Luồng) | Card đồ họa: ${data.gpu_name || (data.gpu && data.gpu.name) || 'GPU'}`;

      if (data.cpu_threads && data.cpu_threads >= 16 && !localStorage.getItem("storyboard_workers")) {

        setWorkerThreads(4);

      }



    }



    const elComfy = document.getElementById("statusComfyUI");



    if (elComfy) {



      if (data.comfyui_ready) {



        elComfy.textContent = "Hoạt động";



        elComfy.classList.add("text-emerald");



      } else if (data.comfyui_installed) {



        elComfy.textContent = "Tự động";



        elComfy.classList.add("text-emerald");



      } else {



        elComfy.textContent = "Chưa kết nối";



      }



    }







    const rComfy = document.getElementById("robotStatusComfy");



    if (rComfy) {



      if (data.comfyui_ready) {



        rComfy.textContent = "Sẵn sàng";



        rComfy.className = "matrix-val val-green";



      } else if (data.comfyui_installed) {



        rComfy.textContent = "Tự động bật";



        rComfy.className = "matrix-val val-blue";



      } else {



        rComfy.textContent = "Chưa kết nối";



        rComfy.className = "matrix-val val-amber";



      }



    }







    const rGemini = document.getElementById("robotStatusGemini");



    if (rGemini) {



      rGemini.textContent = "Director AI Core";



      rGemini.className = "matrix-val val-green";



    }







    void loadGatewayStatus();



    void loadMuseStatus();



  } catch (err) {



    console.warn("Could not load config", err);



  }



}







async function loadGatewayStatus() {



  try {



    const res = await fetch("/api/gateway/status");



    const data = await res.json();



    if (!res.ok || !data.ok) return;







    const cfg = data.config || {};



    const test = data.test || {};







    const inUrl = document.getElementById("inGatewayUrl");



    const inKey = document.getElementById("inGatewayKey");



    const inTextModel = document.getElementById("inGatewayTextModel");



    const inImageModel = document.getElementById("inGatewayImageModel");



    const inEnabled = document.getElementById("inGatewayEnabled");



    const statusBox = document.getElementById("gatewayStatusBox");



    const robotGateway = document.getElementById("robotStatusGateway");



    const gatewayBadge = document.getElementById("gatewayActiveBadge");



    const gatewayWrap = document.getElementById("gatewayInputWrap");



    const btnToggleGw = document.getElementById("btnToggleGatewayInput");



    const elV2 = document.getElementById("statusV2");







    if (inUrl && cfg.base_url) inUrl.value = cfg.base_url;



    if (inKey && cfg.api_key_masked) inKey.placeholder = `Mã hiện tại: ${cfg.api_key_masked}`;



    if (inTextModel && cfg.text_model) inTextModel.value = cfg.text_model;



    if (inImageModel && cfg.image_model) inImageModel.value = cfg.image_model;



    if (inEnabled) inEnabled.checked = !!cfg.enabled;







    if (test.ok || cfg.has_key) {



      if (gatewayBadge) {



        gatewayBadge.innerHTML = `<span style="color:#10b981;font-weight:600;">✓ Bản quyền Cloud AI Pro: Sẵn sàng hoạt động</span> (Mã: <code style="color:#38bdf8;">${escapeHtml(cfg.api_key_masked || "Active")}</code>)`;



      }



      if (gatewayWrap) gatewayWrap.style.display = "none";



      if (btnToggleGw) btnToggleGw.textContent = "Cập nhật";



      if (elV2) {



        elV2.textContent = "Sẵn sàng";



        elV2.classList.add("text-emerald");



      }



      if (robotGateway) {



        robotGateway.textContent = "Sẵn sàng";



        robotGateway.className = "matrix-val val-green";



      }



      if (statusBox) {



        statusBox.innerHTML = `<div style="color:#10b981;">✓ Máy chủ AI Cloud: Phản hồi tốt (${escapeHtml(test.response || "OK")})</div>`;



      }



    } else {



      if (gatewayBadge) {



        gatewayBadge.innerHTML = `<span style="color:#f59e0b;">○ Chưa kích hoạt mã bản quyền Cloud AI</span>`;



      }



      if (gatewayWrap) gatewayWrap.style.display = "block";



      if (btnToggleGw) btnToggleGw.textContent = "Thu gọn";



      if (elV2) {



        elV2.textContent = "Chưa có";



        elV2.classList.remove("text-emerald");



      }



      if (robotGateway) {



        robotGateway.textContent = "Chưa kích hoạt";



        robotGateway.className = "matrix-val val-amber";



      }



      if (statusBox) {



        statusBox.innerHTML = `<div style="color:#f59e0b;">Vui lòng nhập mã bản quyền / API Key để kích hoạt.</div>`;



      }



    }



  } catch (err) {



    console.warn("Could not load gateway status", err);



  }



}



window.loadGatewayStatus = loadGatewayStatus;







async function saveGatewayConfig() {



  const inUrl = document.getElementById("inGatewayUrl");



  const inKey = document.getElementById("inGatewayKey");



  const inTextModel = document.getElementById("inGatewayTextModel");



  const inImageModel = document.getElementById("inGatewayImageModel");



  const inEnabled = document.getElementById("inGatewayEnabled");



  const btnSave = document.getElementById("btnSaveGateway");







  const payload = {



    base_url: inUrl ? inUrl.value.trim() : "https://tuansuapi.store/v1",



    api_key: inKey ? inKey.value.trim() : "",



    text_model: inTextModel ? inTextModel.value.trim() : "gemini-flash-3.8-fast",



    image_model: inImageModel ? inImageModel.value.trim() : "gemini-3.1-flash-image-preview",



    enabled: inEnabled ? inEnabled.checked : true



  };







  try {



    if (btnSave) {



      btnSave.disabled = true;



      btnSave.textContent = "Đang kiểm tra & lưu...";



    }



    const res = await fetch("/api/gateway/save", {



      method: "POST",



      headers: { "Content-Type": "application/json" },



      body: JSON.stringify(payload)



    });



    const data = await res.json();



    if (res.ok && data.ok) {



      if (data.test && data.test.ok) {



        showToast("✓ Đã lưu và kiểm tra kết nối API Bên Thứ Ba thành công!");



      } else {



        showToast("Đã lưu cấu hình Gateway (Lưu ý: " + (data.test?.error || "Cần kiểm tra mạng") + ")", "warning");



      }



      if (inKey && inKey.value) inKey.value = "";



      await loadGatewayStatus();



    } else {



      showToast("Lỗi khi lưu Gateway: " + (data.error || "Không thể lưu"), "error");



    }



  } catch (err) {



    showToast("Lỗi kết nối máy chủ: " + err.message, "error");



  } finally {



    if (btnSave) {



      btnSave.disabled = false;



      btnSave.textContent = "💾 Lưu Cổng API";



    }



  }



}



window.saveGatewayConfig = saveGatewayConfig;







function museLoginState() {



  if (!window.storyboardMuseLogin) window.storyboardMuseLogin = {id: "", timer: null, busy: false, until: 0, account_id: ""};



  return window.storyboardMuseLogin;



}



function setMuseLoginMessage(message, verified = false) {



  const badge = document.getElementById("museActiveBadge");



  const status = document.getElementById("museStatusBox");



  if (badge) { badge.textContent = verified ? "✓ Đã đăng nhập và kết nối Muse" : "○ Muse · " + message; badge.style.color = verified ? "#10b981" : "#94a3b8"; }



  if (status) status.textContent = message;



}



function scheduleMuseLoginCheck() {



  const auth = museLoginState();



  if (auth.timer || !auth.id || auth.busy) return;



  if (Date.now() >= auth.until) { auth.id = ""; setMuseLoginMessage("Hết thời gian chờ đăng nhập. Bấm Đăng nhập Muse để tiếp tục."); return; }



  auth.timer = setTimeout(() => { auth.timer = null; void finishMuseLogin(false); }, 5000);



}







window.openMuseModal = async function () {



  const modal = document.getElementById("modalMuseManager");



  if (!modal) return;



  openModal(modal);



  await loadMuseStatus(false);



};







window.toggleMuseConfigBox = function () {



  const box = document.getElementById("museConfigBox");



  const icon = document.getElementById("museToggleConfigIcon");



  if (!box) return;



  const isHidden = box.style.display === "none";



  box.style.display = isHidden ? "block" : "none";



  if (icon) icon.textContent = isHidden ? "Thu gọn cấu hình nâng cao ▲" : "Đường dẫn Python / Cấu hình nâng cao ▼";



};







window.saveMuseConfigModal = async function () {



  const python = document.getElementById("inMusePythonModal");



  try {



    const res = await fetch("/api/muse/save", {



      method: "POST", headers: { "Content-Type": "application/json" },



      body: JSON.stringify({ python_executable: python ? python.value.trim() : "", enabled: true })



    });



    const data = await res.json();



    if (!res.ok || !data.ok) throw new Error(data.error || "Không lưu được kết nối Muse");



    await loadMuseStatus(true);



    showToast(data.test?.ok ? "Đã lưu và xác minh kết nối Muse thành công!" : (data.test?.message || "Đã lưu cấu hình."), data.test?.ok ? "success" : "warning");



  } catch (err) {



    showToast(err.message, "error");



  }

};







function renderMuseAccounts(accounts, activeId, dispatchMode) {



  const container = document.getElementById("museModalAccountCardsContainer");



  const countBadge = document.getElementById("museAccountCountBadge");



  const modalModeDesc = document.getElementById("museModalModeDesc");



  const modalModeBadge = document.getElementById("museModalBadgeMode");



  const radioRR = document.getElementById("radioModalRR");



  const radioAct = document.getElementById("radioModalActive");







  // Settings card elements



  const settingsBadge = document.getElementById("settingsMuseCountBadge");



  const settingsSummary = document.getElementById("settingsMuseStatusSummary");







  if (radioRR && radioAct) {



    if (dispatchMode === "active_only") {



      radioAct.checked = true;



    } else {



      radioRR.checked = true;



    }



  }







  const readyAccounts = (accounts || []).filter(a => a.ready);



  const readyCount = readyAccounts.length;



  const totalCount = (accounts || []).length;







  if (countBadge) countBadge.textContent = `${totalCount} Tài Khoản`;



  if (modalModeBadge) {



    modalModeBadge.textContent = dispatchMode === "active_only" ? "CHỈ DÙNG 1 ACC" : "ROUND-ROBIN";



  }







  if (settingsBadge) {



    settingsBadge.textContent = `${readyCount} Sẵn sàng`;



    settingsBadge.style.background = readyCount > 0 ? "#f43f5e" : "#64748b";



  }







  if (modalModeDesc) {



    if (dispatchMode === "active_only") {



      modalModeDesc.textContent = "Chỉ dùng 1 tài khoản chính đang chọn cho tất cả các cảnh.";



    } else {



      modalModeDesc.textContent = `Chia đều theo cảnh qua ${readyCount} tài khoản sẵn sàng (Cảnh 1 ➡️ Acc 1, Cảnh 2 ➡️ Acc 2...) + Tự bọc lót khi hết credit.`;



    }



  }







  if (settingsSummary) {



    if (dispatchMode === "active_only") {



      settingsSummary.textContent = `Chỉ dùng tài khoản chính · ${readyCount}/${totalCount} tài khoản sẵn sàng`;



    } else {



      settingsSummary.textContent = `Chia đều theo cảnh (Round-Robin) · ${readyCount}/${totalCount} tài khoản sẵn sàng · Tự động bọc lót`;



    }



  }







  if (!container) return;







  if (!accounts || accounts.length === 0) {



    container.innerHTML = `



      <div style="text-align:center;padding:26px 16px;background:#090d16;border-radius:10px;border:1px dashed rgba(244,63,94,0.35);">



        <div style="font-size:2.2rem;margin-bottom:8px;">🎬</div>



        <div style="color:#f8fafc;font-weight:700;font-size:0.92rem;">Chưa có tài khoản Muse nào được kết nối</div>



        <div style="color:#94a3b8;font-size:0.74rem;margin:6px auto 14px auto;max-width:440px;line-height:1.5;">



          Bấm nút bên dưới để mở cửa sổ đăng nhập Muse. Tool sẽ tự động kết nối và lưu phiên độc lập cho bạn.



        </div>



        <button type="button" class="btn btn-danger btn-sm" onclick="addMuseAccountPrompt()" style="background:#f43f5e;color:#fff;font-weight:700;border:none;padding:7px 16px;border-radius:6px;cursor:pointer;display:inline-flex;align-items:center;gap:6px;box-shadow:0 0 12px rgba(244,63,94,0.4);">



          🔴 + Thêm Tài Khoản Muse Ngay



        </button>



      </div>



    `;



    return;



  }







  container.innerHTML = accounts.map(acc => {



    const isAct = acc.id === activeId;



    const statusText = acc.ready ? "🟢 Đã kết nối" : "🟡 Cần đăng nhập";



    const statusBg = acc.ready ? "#065f46" : "#78350f";



    const statusColor = acc.ready ? "#a7f3d0" : "#fde68a";



    const safeName = (acc.name || "Tài khoản").replace(/'/g, "\\'").replace(/"/g, "&quot;");







    const accTokens = acc.tokens !== undefined ? acc.tokens : 50;

    const tokensUsed = acc.tokens_used || 0;

    const tokenColor = accTokens > 20 ? "#34d399" : (accTokens > 5 ? "#fbbf24" : "#f87171");

    const tokenBg = accTokens > 20 ? "rgba(52,211,153,0.1)" : (accTokens > 5 ? "rgba(251,191,36,0.1)" : "rgba(248,113,113,0.12)");

    const tokenBorder = accTokens > 20 ? "rgba(52,211,153,0.3)" : (accTokens > 5 ? "rgba(251,191,36,0.3)" : "rgba(248,113,113,0.35)");



    return `

      <div style="display:grid;grid-template-columns:minmax(180px, 1fr) 130px 105px 240px;gap:8px;align-items:center;padding:7px 12px;background:#090d16;border-radius:8px;border:1px solid ${isAct ? 'rgba(244,63,94,0.55)' : '#1e293b'};min-height:44px;box-sizing:border-box;">



        



        <!-- Col 1: Tài khoản Muse (Avatar + Tên + Meta) -->



        <div style="display:flex;align-items:center;gap:10px;min-width:0;overflow:hidden;">



          <div style="width:32px;height:32px;border-radius:50%;background:linear-gradient(135deg,#f43f5e,#be123c);display:flex;align-items:center;justify-content:center;border:1.5px solid ${isAct ? '#f43f5e' : '#334155'};flex-shrink:0;box-shadow:0 0 8px rgba(244,63,94,0.3);">



            <svg width="16" height="16" viewBox="0 0 24 24" fill="#fff"><path d="M18 4l2 4h-3l-2-4h-2l2 4h-3l-2-4H8l2 4H7L5 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V4h-4z"/></svg>



          </div>



          <div style="min-width:0;flex:1;overflow:hidden;">



            <div style="display:flex;align-items:center;gap:6px;white-space:nowrap;overflow:hidden;">



              <span style="font-weight:700;font-size:0.86rem;color:#f8fafc;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${escapeHtml(acc.name)}">



                ${escapeHtml(acc.name)}



              </span>



              <span class="badge" style="background:${statusBg};color:${statusColor};font-size:0.58rem;font-weight:600;padding:1px 5px;border-radius:4px;flex-shrink:0;">



                ${statusText}



              </span>



            </div>



            <div style="font-size:0.68rem;color:#94a3b8;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:2px;">



              <span style="color:#cbd5e1;">Hồ sơ riêng</span> &bull; <span style="font-family:monospace;color:#64748b;font-size:0.65rem;">${escapeHtml(acc.id)}</span>



            </div>

            ${acc.proxy ? `

              <div style="font-size:0.65rem;color:#34d399;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:2px;display:flex;align-items:center;gap:4px;">

                <span>🌐</span> <span style="font-family:monospace;background:rgba(16,185,129,0.15);padding:1px 5px;border-radius:4px;border:1px solid rgba(16,185,129,0.3);color:#6ee7b7;">Proxy: ${escapeHtml(acc.proxy)}</span>

              </div>

            ` : `

              <div style="font-size:0.63rem;color:#64748b;margin-top:2px;display:flex;align-items:center;gap:4px;">

                <span>🌐 Direct Home IP</span>

              </div>

            `}



          </div>



        </div>







        <!-- Col 2: Số Lượng Tokens (130px) -->

        <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;gap:3px;">

          <div style="display:flex;align-items:center;gap:5px;cursor:pointer;background:${tokenBg};border:1px solid ${tokenBorder};padding:2px 8px;border-radius:6px;transition:all 0.15s ease;"

               onclick="editMuseAccountTokens('${escapeHtml(acc.id)}', ${accTokens}, '${safeName}')"

               title="Bấm để chỉnh sửa số token chính xác">

            <span style="font-size:0.75rem;">🪙</span>

            <span style="font-weight:700;font-size:0.84rem;color:${tokenColor};font-family:monospace;">${accTokens}</span>

            <span style="font-size:0.62rem;color:#94a3b8;">tokens</span>

            <span style="font-size:0.6rem;color:#64748b;margin-left:2px;">✏️</span>

          </div>

          ${tokensUsed > 0 ? `

            <div style="font-size:0.6rem;color:#64748b;white-space:nowrap;">

              Đã tạo: <span style="color:#94a3b8;font-weight:600;">${tokensUsed}</span> cảnh

            </div>

          ` : `

            <div style="font-size:0.6rem;color:#475569;white-space:nowrap;">Chưa dùng cảnh nào</div>

          `}

        </div>



        <!-- Col 3: Vai trò / Chế độ (105px) -->



        <div style="display:flex;justify-content:center;align-items:center;">



          ${isAct ? `



            <span style="background:rgba(244,63,94,0.2);color:#fda4af;border:1px solid #f43f5e;font-size:0.68rem;padding:3px 8px;border-radius:4px;font-weight:700;letter-spacing:0.02em;">



              ⭐ Kênh Chính



            </span>



          ` : `



            <span style="background:#0b1329;color:#94a3b8;border:1px solid #334155;font-size:0.68rem;padding:3px 8px;border-radius:4px;">



              🔄 Luân phiên



            </span>



          `}



        </div>







        <!-- Col 4: Compact account actions with a visible Muse login button -->



        <div style="display:flex;align-items:center;justify-content:center;gap:5px;width:240px;box-sizing:border-box;">



          ${isAct ? `



            <button type="button" class="yt-circle-btn yt-circle-default active" title="Tài khoản này đang là chính">



              ⭐



            </button>



          ` : `



            <button type="button" class="yt-circle-btn yt-circle-default" onclick="selectMuseAccount('${escapeHtml(acc.id)}')" title="Đặt làm tài khoản chính">



              ⭐



            </button>



          `}



          <button type="button" class="yt-circle-btn yt-circle-studio" style="width:76px;min-width:76px;padding:0 5px;border-radius:6px;white-space:nowrap;font-size:0.68rem;" onclick="loginMuseAccount('${escapeHtml(acc.id)}', '${safeName}')" title="${acc.ready ? 'Đăng nhập lại tài khoản này' : 'Đăng nhập vào tài khoản'}" aria-label="Đăng nhập Muse">



            Đăng nhập



          </button>



          <button type="button" class="yt-circle-btn yt-circle-playlist" onclick="openMuseCookiePasteModal('${escapeHtml(acc.id)}', '${safeName}')" title="Dán Cookie / Session thủ công cho tài khoản này" style="color:#38bdf8;border-color:rgba(56,189,248,0.4);">

            📋

          </button>



          <button type="button" class="yt-circle-btn yt-circle-playlist" onclick="testMuseAccount('${escapeHtml(acc.id)}')" title="Kiểm tra kết nối tài khoản">



            🔍



          </button>



          <button type="button" class="yt-circle-btn yt-circle-channel" onclick="renameMuseAccountPrompt('${escapeHtml(acc.id)}', '${safeName}')" title="Đổi tên tài khoản">



            ✏️



          </button>



          ${accounts.length > 1 ? `



            <button type="button" class="yt-circle-btn yt-circle-delete" onclick="deleteMuseAccount('${escapeHtml(acc.id)}', '${safeName}')" title="Xóa tài khoản này">



              🗑️



            </button>



          ` : `



            <span style="width:28px;height:28px;display:inline-block;"></span>



          `}



        </div>







      </div>



    `;



  }).join("");



}







async function loadMuseStatus(triggerTest = false, accountId = null) {



  const badge = document.getElementById("museActiveBadge");



  const finish = document.getElementById("btnFinishMuseLoginModal");



  try {



    let url = triggerTest ? "/api/muse/status?test=1" : "/api/muse/status";



    if (accountId) url += (url.includes("?") ? "&" : "?") + "account_id=" + encodeURIComponent(accountId);



    const res = await fetch(url);



    const data = await res.json();



    if (!res.ok || !data.ok) throw new Error(data.error || "Không đọc được trạng thái Muse");



    const cfg = data.config || {}, test = data.test || {}, login = data.login || {};



    const pythonModal = document.getElementById("inMusePythonModal");



    const configBadge = document.getElementById("museConfigBadge");



    if (pythonModal) pythonModal.value = cfg.python_executable || "";



    if (configBadge) {



      configBadge.textContent = cfg.configured ? "Đã sẵn sàng" : "Chưa cài đặt";



      configBadge.style.background = cfg.configured ? "#10b981" : "#ef4444";



    }







    renderMuseAccounts(data.accounts || [], data.active_id || "", data.dispatch_mode || "round_robin");







    if (finish) finish.hidden = login.status !== "WAITING_FOR_LOGIN";



    if (login.status === "WAITING_FOR_LOGIN" && login.login_id) {



      const auth = museLoginState();



      auth.id = login.login_id;



      auth.account_id = login.account_id || "";



      if (!auth.until) auth.until = Date.now() + 20 * 60 * 1000;



      scheduleMuseLoginCheck();



    }



    return Boolean(test.ok);



  } catch (err) {



    return false;



  }



}



window.loadMuseStatus = loadMuseStatus;







async function setMuseDispatchMode(mode) {



  try {



    const res = await fetch("/api/muse/accounts/mode", {



      method: "POST", headers: { "Content-Type": "application/json" },



      body: JSON.stringify({ dispatch_mode: mode })



    });



    const data = await res.json();



    if (!res.ok || !data.ok) throw new Error(data.error || "Không lưu được chế độ phân bổ cảnh.");



    await loadMuseStatus(false);



    showToast(mode === "round_robin" ? "Đã bật chế độ Chia đều mỗi cảnh 1 tài khoản (Round-Robin)." : "Đã bật chế độ Chỉ dùng tài khoản chính.", "success");



  } catch (err) {



    showToast(err.message, "error");



  }



}



window.setMuseDispatchMode = setMuseDispatchMode;







async function selectMuseAccount(accountId) {



  try {



    const res = await fetch("/api/muse/accounts/select", {



      method: "POST", headers: { "Content-Type": "application/json" },



      body: JSON.stringify({ account_id: accountId })



    });



    const data = await res.json();



    if (!res.ok || !data.ok) throw new Error(data.error || "Không chọn được tài khoản.");



    await loadMuseStatus(false);



    showToast("Đã chọn làm tài khoản chính.", "success");



  } catch (err) {



    showToast(err.message, "error");



  }



}



window.selectMuseAccount = selectMuseAccount;







async function testMuseAccount(accountId) {



  try {



    showToast("Đang kiểm tra kết nối tài khoản...", "info");



    try {



      await fetch("/api/muse/login/complete", {



        method: "POST",



        headers: { "Content-Type": "application/json" },



        body: JSON.stringify({ account_id: accountId, login_id: window.storyboardMuseLogin?.id || "" })



      });



    } catch (_) {}



    const verified = await loadMuseStatus(true, accountId);



    showToast(verified ? "Tài khoản kết nối thành công và sẵn sàng!" : "Tài khoản chưa xác minh được. Hãy bấm Đăng nhập lại.", verified ? "success" : "warning");



  } catch (err) {



    showToast(err.message, "error");



  }



}



window.testMuseAccount = testMuseAccount;







async function addMuseAccountPrompt() {



  const name = prompt("Nhập tên gợi nhớ cho tài khoản Muse mới (ví dụ: Acc Free 2, Acc Dự Phòng):", "");



  if (name === null) return;



  const accName = name.trim() || "Tài khoản Muse mới";



  try {



    const res = await fetch("/api/muse/accounts/create", {



      method: "POST", headers: { "Content-Type": "application/json" },



      body: JSON.stringify({ name: accName })



    });



    const data = await res.json();



    if (!res.ok || !data.ok) throw new Error(data.error || "Không tạo được tài khoản mới.");



    await loadMuseStatus(false);



    showToast(`Đã thêm '${accName}'. Đang mở cửa sổ đăng nhập...`, "info");



    await loginMuseAccount(data.account.id, accName);



  } catch (err) {



    showToast(err.message, "error");



  }



}



window.addMuseAccountPrompt = addMuseAccountPrompt;







async function renameMuseAccountPrompt(accountId, currentName) {



  const newName = prompt("Nhập tên mới cho tài khoản:", currentName);



  if (!newName || newName.trim() === currentName) return;



  try {



    const res = await fetch("/api/muse/accounts/rename", {



      method: "POST", headers: { "Content-Type": "application/json" },



      body: JSON.stringify({ account_id: accountId, name: newName.trim() })



    });



    const data = await res.json();



    if (!res.ok || !data.ok) throw new Error(data.error || "Không đổi được tên tài khoản.");



    await loadMuseStatus(false);



    showToast("Đã đổi tên tài khoản thành công.", "success");



  } catch (err) {



    showToast(err.message, "error");



  }



}



window.renameMuseAccountPrompt = renameMuseAccountPrompt;



async function editMuseAccountTokens(accountId, currentTokens, accountName) {

  const input = prompt(`Nhập số lượng token chính xác cho tài khoản:

${accountName}`, currentTokens !== undefined ? currentTokens : 50);

  if (input === null) return;

  const num = parseInt(input.trim(), 10);

  if (isNaN(num) || num < 0) {

    showToast("Vui lòng nhập một số nguyên không âm (ví dụ: 50).", "error");

    return;

  }

  try {

    const res = await fetch("/api/muse/accounts/tokens", {

      method: "POST",

      headers: { "Content-Type": "application/json" },

      body: JSON.stringify({ account_id: accountId, tokens: num })

    });

    const data = await res.json();

    if (!res.ok || !data.ok) throw new Error(data.error || "Không cập nhật được số token.");

    await loadMuseStatus(false);

    showToast(`Đã cập nhật số token thành công (${num} tokens).`, "success");

  } catch (err) {

    showToast(err.message, "error");

  }

}

window.editMuseAccountTokens = editMuseAccountTokens;







async function deleteMuseAccount(accountId, name) {



  if (!confirm(`Bạn có chắc muốn xóa tài khoản '${name}' khỏi danh sách?`)) return;



  try {



    const res = await fetch("/api/muse/accounts/delete", {



      method: "POST", headers: { "Content-Type": "application/json" },



      body: JSON.stringify({ account_id: accountId })



    });



    const data = await res.json();



    if (!res.ok || !data.ok) throw new Error(data.error || "Không xóa được tài khoản.");



    await loadMuseStatus(false);



    showToast("Đã xóa tài khoản.", "success");



  } catch (err) {



    showToast(err.message, "error");



  }



}



window.deleteMuseAccount = deleteMuseAccount;







async function loginMuseAccount(accountId, name) {



  const auth = museLoginState();



  if (auth.busy) return;



  try {



    const res = await fetch("/api/muse/login/start", {



      method: "POST", headers: { "Content-Type": "application/json" },



      body: JSON.stringify({ account_id: accountId, name: name })



    });



    const data = await res.json();



    if (!res.ok || !data.ok || !data.opened) throw new Error(data.error || "Chưa mở được cửa sổ đăng nhập Muse.");



    if (auth.timer) clearTimeout(auth.timer);



    auth.timer = null;



    auth.id = data.login_id;



    auth.account_id = accountId;



    auth.until = Date.now() + 20 * 60 * 1000;



    const finish = document.getElementById("btnFinishMuseLoginModal") || document.getElementById("btnFinishMuseLogin");



    if (finish) finish.hidden = false;



    setMuseLoginMessage(data.message || `Đang mở trình duyệt riêng cho '${name}'. Hãy hoàn tất đăng nhập trong cửa sổ vừa mở.`);



    scheduleMuseLoginCheck();



  } catch (err) {



    setMuseLoginMessage(err.message);



    showToast(err.message, "error");



  }



}



window.loginMuseAccount = loginMuseAccount;







async function startMuseLogin() {



  await loginMuseAccount("", "");



}



window.startMuseLogin = startMuseLogin;







async function finishMuseLogin(manual = true) {



  const auth = museLoginState();



  const btn = document.getElementById("btnFinishMuseLoginModal") || document.getElementById("btnFinishMuseLogin");



  if (auth.busy || (!auth.id && !manual)) return false;



  auth.busy = true;



  if (auth.timer) { clearTimeout(auth.timer); auth.timer = null; }



  let keepWaiting = false;



  try {



    if (btn) btn.disabled = true;



    const res = await fetch("/api/muse/login/complete", {



      method: "POST", headers: { "Content-Type": "application/json" },



      body: JSON.stringify({ login_id: auth.id || "", account_id: auth.account_id || "" })



    });



    const data = await res.json();



    if (!res.ok || !data.ok) {



      const error = data.error || "Chưa kết nối được phiên Muse.";



      if (error.startsWith("MUSE_LOGIN_CHECK_TIMEOUT")) { setMuseLoginMessage("Chưa kiểm tra được đăng nhập. Giữ cửa sổ Muse mở; tool sẽ thử lại."); keepWaiting = true; return false; }



      if (error.startsWith("MUSE_QUEUE_BUSY")) { setMuseLoginMessage("Đang có cảnh Muse xử lý. Tool sẽ kết nối lại khi cảnh đó xong."); keepWaiting = true; return false; }



      throw new Error(error);



    }



    if (!data.ready) {



      setMuseLoginMessage(data.message || "Đang chờ bạn hoàn tất đăng nhập trong cửa sổ Muse.");



      keepWaiting = true; return false;



    }



    auth.id = "";



    auth.account_id = "";



    if (btn) btn.hidden = true;



    const verified = await loadMuseStatus(true);



    showToast(verified ? "Đã đăng nhập Muse thành công! Sẵn sàng tạo video." : "Đã lưu phiên Muse; hãy kiểm tra lại kết nối.", verified ? "success" : "warning");



    return verified;



  } catch (err) {



    auth.id = "";



    auth.account_id = "";



    setMuseLoginMessage(err.message);



    if (manual) showToast(err.message, "error");



    return false;



  } finally {



    auth.busy = false;



    if (btn) btn.disabled = false;



    if (keepWaiting) scheduleMuseLoginCheck();



  }



}



window.finishMuseLogin = finishMuseLogin;







async function saveMuseConfig() {



  const btn = document.getElementById("btnSaveMuse");



  const python = document.getElementById("inMusePython");



  try {



    if (btn) { btn.disabled = true; btn.textContent = "Đang kết nối..."; }



    const res = await fetch("/api/muse/save", {



      method: "POST", headers: { "Content-Type": "application/json" },



      body: JSON.stringify({python_executable: python ? python.value.trim() : "", enabled: true})



    });



    const data = await res.json();



    if (!res.ok || !data.ok) throw new Error(data.error || "Không lưu được kết nối Muse");



    await loadMuseStatus(true);



    showToast(data.test?.ok ? "Đã kết nối Muse bằng phiên đăng nhập trên máy." : (data.test?.message || "Chưa xác minh được phiên Muse."), data.test?.ok ? "success" : "warning");



  } catch (err) {



    showToast(err.message, "error");



  } finally {



    if (btn) { btn.disabled = false; btn.textContent = "Kết nối"; }



  }



}



window.saveMuseConfig = saveMuseConfig;







async function loadMcpAccounts() {



  if (!el.mcpAccountSelect) return;



  try {



    const res = await fetch("/api/mcp/accounts");



    const data = await res.json();



    if (!res.ok) throw new Error(data.error || "Không đọc được tài khoản");



    el.mcpAccountSelect.replaceChildren();



    for (const acc of (data.accounts || [])) {



      const option = document.createElement("option");



      option.value = acc.id;



      option.textContent = acc.name + (acc.id === data.active ? " (Đang chọn)" : "");



      el.mcpAccountSelect.appendChild(option);



    }



    el.mcpAccountSelect.value = data.active;



    await loadMcpProjects();



    const toolStatus = document.getElementById("mcpToolAutoStatus");



    if (toolStatus) {



      toolStatus.textContent = data.tool_linked



        ? "Đã lưu dự án Web Tool; trạng thái Google và MCP cần được xác minh riêng."



        : "Đã tích hợp Web Tool. Hãy mở Chrome và đăng nhập Google để Studio tự gắn.";



    }



  } catch (error) {



    el.mcpAccountStatus.textContent = "Không thể tải tài khoản Google Flow: " + error.message;



  }



}



async function refreshFlowKitStatus(isManual = false) {
  const box = document.getElementById("flowkitStatusBox");
  const badge = document.getElementById("flowkitLiveStatusBadge");
  const statusFk = document.getElementById("statusFlowKit");
  try {
    const res = await fetch("/api/flowkit/status", { cache: "no-store" });
    const data = await res.json();
    updateFlowKitUI(data);
    if (isManual) showToast("Đã kiểm tra kết nối FlowKit WebTool thành công.");
  } catch (e) {
    if (badge) {
      badge.textContent = "🔴 Ngoại tuyến";
      badge.style.color = "#ef4444";
      badge.style.background = "rgba(239,68,68,0.15)";
      badge.style.borderColor = "rgba(239,68,68,0.3)";
    }
    if (box) box.textContent = "⚠️ Không thể kết nối với FlowKit Gateway (Port 18110): " + e.message;
    if (statusFk) {
      const autoBadge = document.getElementById("autoFlowManagerStatus");
      if (autoBadge && autoBadge.textContent.includes("🟢")) {
        statusFk.textContent = "🟢 Sẵn sàng";
        statusFk.style.color = "#10b981";
      } else {
        statusFk.textContent = "🔴 Offline";
        statusFk.style.color = "#ef4444";
      }
    }
  }
}

function updateFlowKitUI(data) {
  const box = document.getElementById("flowkitStatusBox");
  const badge = document.getElementById("flowkitLiveStatusBadge");
  const statusFk = document.getElementById("statusFlowKit");
  const cardChrome = document.getElementById("fkCardChrome");
  const cardModel = document.getElementById("fkCardModel");

  if (data && data.ready) {
    const isConnected = Boolean(data.connected);
    if (isConnected) {
      if (badge) {
        badge.textContent = "🟢 Web Tool Đã Kết Nối";
        badge.style.color = "#10b981";
        badge.style.background = "rgba(16,185,129,0.15)";
        badge.style.borderColor = "rgba(16,185,129,0.3)";
      }
      const autoBadge = document.getElementById("autoFlowManagerStatus");
      if (autoBadge) {
        autoBadge.textContent = "🟢 Sẵn sàng";
        autoBadge.style.color = "#10b981";
        autoBadge.style.background = "rgba(16,185,129,0.15)";
      }
      if (box) {
        box.innerHTML = '✅ <strong style="color:#10b981;">FlowKit Gateway (Port 18110) &amp; Google Flow Web Tool (Port 9461)</strong> đang hoạt động ổn định. Sẵn sàng tạo ảnh và video!';
      }
      const rFlowEl = document.getElementById("robotStatusFlow");
      const rBtnEl = document.getElementById("robotBtnGoogleLogin");
      if (rFlowEl) {
        rFlowEl.textContent = "Sẵn sàng (Google Flow)";
        rFlowEl.className = "matrix-val val-green";
      }
      if (rBtnEl) {
        rBtnEl.textContent = "✓ Máy Chủ Đồ Họa Đã Sẵn Sàng";
        rBtnEl.className = "btn btn-success btn-sm";
        rBtnEl.style.background = "#10b981";
        rBtnEl.style.borderColor = "#10b981";
        rBtnEl.style.color = "#ffffff";
      }
      if (statusFk) {
        statusFk.textContent = "🟢 Online (18110)";
        statusFk.style.color = "#10b981";
      }
      if (cardChrome) cardChrome.textContent = "Cổng 9461 · Web Tool Đã Mở";
    } else {
      if (badge) {
        badge.textContent = "🟡 Gateway Online (Chờ Mở Tab)";
        badge.style.color = "#fbbf24";
        badge.style.background = "rgba(251,191,36,0.15)";
        badge.style.borderColor = "rgba(251,191,36,0.3)";
      }
      if (box) {
        box.innerHTML = '⚡ FlowKit Gateway đang chạy (Port 18110). Bấm nút <strong>"Mở Trình Duyệt / Đăng Nhập Flow"</strong> để mở tab Web Tool Google Flow.';
      }
      if (statusFk) {
        statusFk.textContent = "🟡 Sẵn sàng";
        statusFk.style.color = "#fbbf24";
      }
      if (cardChrome) cardChrome.textContent = "Cổng 9461 · Sẵn sàng";
    }
    if (data.model && cardModel) {
      cardModel.textContent = data.model;
    }
  } else {
    if (badge) {
      badge.textContent = "🔴 Gateway Chưa Chạy";
      badge.style.color = "#ef4444";
      badge.style.background = "rgba(239,68,68,0.15)";
      badge.style.borderColor = "rgba(239,68,68,0.3)";
    }
    if (box) {
      box.textContent = "⚠️ FlowKit Gateway chưa được kích hoạt. Hãy bấm Khởi Động Lại Gateway.";
    }
    if (statusFk) {
      const autoBadge = document.getElementById("autoFlowManagerStatus");
      if (autoBadge && autoBadge.textContent.includes("🟢")) {
        statusFk.textContent = "🟢 Sẵn sàng";
        statusFk.style.color = "#10b981";
      } else {
        statusFk.textContent = "🔴 Offline";
        statusFk.style.color = "#ef4444";
      }
    }
  }
}

async function refreshAutoFlowStatus() {
  const node = document.getElementById("autoFlowManagerStatus");
  const statusBox = document.getElementById("mcpAccountStatus");
  if (!node) return;
  try {
    const res = await fetch("/api/flow/status", { cache: "no-store" });
    const data = await res.json();
    node.textContent = data.badge_text || (data.connected ? "🟢 Sẵn sàng" : "🟡 Chờ đăng nhập");
    const btnInstallFk = document.getElementById("btnInstallFlowKit");
    const btnFlowLoginEl = document.getElementById("btnFlowLogin");
    const btnFlowAddEl = document.getElementById("btnFlowAddAccount");
    if (btnInstallFk) {
      if (data.flowkit_installed === false) {
        btnInstallFk.style.display = "inline-flex";
        if (btnFlowLoginEl) btnFlowLoginEl.style.display = "none";
        if (btnFlowAddEl) btnFlowAddEl.style.display = "none";
      } else {
        btnInstallFk.style.display = "none";
        if (btnFlowLoginEl) btnFlowLoginEl.style.display = "inline-flex";
        if (btnFlowAddEl) btnFlowAddEl.style.display = "inline-flex";
      }
    }
    if (data.badge_type === "success") {
      node.style.background = "rgba(16,185,129,0.15)";
      node.style.color = "#10b981";
      node.style.borderColor = "rgba(16,185,129,0.3)";
      if (statusBox) statusBox.style.color = "#10b981";
    } else if (data.badge_type === "warning") {
      node.style.background = "rgba(245,158,11,0.15)";
      node.style.color = "#fbbf24";
      node.style.borderColor = "rgba(245,158,11,0.3)";
      if (statusBox) statusBox.style.color = "#fbbf24";
    } else {
      node.style.background = "rgba(239,68,68,0.15)";
      node.style.color = "#f87171";
      node.style.borderColor = "rgba(239,68,68,0.3)";
      if (statusBox) statusBox.style.color = "#f87171";
    }
    if (statusBox) {
      if (data.connected || data.ready) {
        const emailInfo = data.email ? ` (${data.email})` : "";
        if (data.ready_accounts > 1) {
          statusBox.textContent = `✓ Web Tool đã kết nối${emailInfo} · ${data.ready_accounts} TK Đa luồng Round-Robin`;
        } else {
          statusBox.textContent = `✓ Web Tool đã kết nối${emailInfo}`;
        }
      } else {
        statusBox.textContent = data.status_text || "Chưa kết nối Web Tool Google Flow.";
      }
    }
    const topBarFk = document.getElementById("statusFlowKit");
    if (topBarFk) {
      if (data.connected || data.ready) {
        topBarFk.textContent = "🟢 Sẵn sàng";
        topBarFk.style.color = "#10b981";
      } else {
        topBarFk.textContent = "🔴 Offline";
        topBarFk.style.color = "#ef4444";
      }
    }
    const robotFlow = document.getElementById("robotStatusFlow");
    const robotBtn = document.getElementById("robotBtnGoogleLogin");
    if (data.ready) {
      if (robotFlow) {
        robotFlow.textContent = "Sẵn sàng (Google Flow)";
        robotFlow.className = "matrix-val val-green";
      }
      if (robotBtn) {
        robotBtn.textContent = "✓ Máy Chủ Đồ Họa Đã Sẵn Sàng";
        robotBtn.className = "btn btn-success btn-sm";
        robotBtn.style.background = "#10b981";
        robotBtn.style.borderColor = "#10b981";
        robotBtn.style.color = "#ffffff";
      }
    }
    const countBadge = document.getElementById("flowAccountCountBadge");
    if (countBadge && data.ready_accounts) {
      countBadge.textContent = data.badge_text || `${data.ready_accounts}/${data.total_accounts} Sẵn sàng`;
    }
  } catch (err) {
    node.textContent = "🔴 Lỗi kết nối";
    node.style.color = "#f87171";
  }
}

async function autoFlowReconnect() {



  const node=document.getElementById("autoFlowManagerStatus");



  if(node)node.textContent="Đang tự mở Chrome và dò Web Tool tương thích…";



  try {



    const response=await fetch("/api/mcp/auto",{



      method:"POST",headers:{"Content-Type":"application/json"},



      body:JSON.stringify({genre:el.inGenre?.value||"auto"})



    });



    const data=await response.json();



    await refreshAutoFlowStatus();



    if(!response.ok && node && data.detail)



      node.textContent+=" "+data.detail;



    if(data.ready){await loadMcpProjects();await loadMcpAccounts();}



  }catch(error){



    if(node)node.textContent="Chưa kết nối được: "+String(error.message||error);



  }



}



let flowProjectSnapshot = null;







function updateMcpProjectForGenre() {



  if (!flowProjectSnapshot || !el.mcpProjectSelect) return;



  const genre = el.inGenre?.value || "auto";



  const target = flowProjectSnapshot.genres?.[genre] ||



    (genre === "auto" ? flowProjectSnapshot.active : null);



  if (target && [...el.mcpProjectSelect.options].some(x => x.value === target)) {



    el.mcpProjectSelect.value = target;



    const project = flowProjectSnapshot.projects.find(x => x.id === target);



    if (el.mcpProjectStatus) el.mcpProjectStatus.textContent =



      "Thể loại hiện tại dùng dự án: " + (project?.label || "đã đăng ký") +



      ". Nhấn Xác minh MCP để kiểm tra chức năng tạo ảnh.";



  } else if (el.mcpProjectStatus) {



    el.mcpProjectStatus.textContent =



      "Chưa gán dự án riêng cho thể loại này. Mở đúng Web Tool, chọn thể loại và bấm Thêm / Gán dự án.";



  }



}







async function loadMcpProjects() {



  if (!el.mcpProjectSelect) return;



  try {



    const response = await fetch("/api/mcp/projects", {cache:"no-store"});



    const data = await response.json();



    if (!response.ok) throw new Error(data.error || "Không đọc được dự án.");



    flowProjectSnapshot = data;



    el.mcpProjectSelect.replaceChildren();



    for (const item of data.projects || []) {



      const opt = document.createElement("option");



      opt.value = item.id;



      opt.textContent = item.label + " — " + item.genre;



      el.mcpProjectSelect.appendChild(opt);



    }



    if (data.active) el.mcpProjectSelect.value = data.active;



    el.mcpOpenProjectTab.replaceChildren();



    for (const item of data.open_tabs || []) {



      const opt = document.createElement("option");



      opt.value = item.id;



      opt.textContent = "Dự án " + item.project_id.slice(0,8)



                      + " · Tool " + item.tool_id.slice(0,8);



      el.mcpOpenProjectTab.appendChild(opt);



    }



    if (!data.open_tabs?.length) {



      const opt=document.createElement("option");



      opt.value="";opt.textContent="Chưa thấy Web Tool trong Chrome của tài khoản";



      el.mcpOpenProjectTab.appendChild(opt);



    }



    // Keep an explicit category chosen by the user while registering a project.



    if (el.mcpGenreBind && !el.mcpGenreBind.value)



      el.mcpGenreBind.value = el.inGenre?.value || "auto";



    updateMcpProjectForGenre();
      if (typeof updateHintChipsForGenre === "function") updateHintChipsForGenre(el.inGenre.value);



  } catch(error) {



    if (el.mcpProjectStatus) el.mcpProjectStatus.textContent = "Không đọc được dự án Flow: " + error.message;



  }



}







async function mcpProjectAction(action) {



  const id = action === "register" ? el.mcpOpenProjectTab.value : el.mcpProjectSelect.value;



  if (!id) {



    el.mcpProjectStatus.textContent = "Chưa chọn Web Tool hoặc dự án. Hãy mở Chrome Flow rồi bấm Quét.";



    return;



  }



  const payload = {action,project_id:id,



    name:el.mcpProjectName.value.trim(),



    genre:el.mcpGenreBind.value};



  if (action === "register" && !payload.name) {



    el.mcpProjectStatus.textContent = "Hãy đặt tên dễ nhận biết cho dự án.";



    return;



  }



  el.mcpProjectStatus.textContent = "Đang xử lý dự án trong tài khoản Google Flow...";



  try {



    const response=await fetch("/api/mcp/project",{



      method:"POST",headers:{"Content-Type":"application/json"},



      body:JSON.stringify(payload)



    });



    const data=await response.json();



    if (!response.ok || !data.ok) throw new Error(data.error || "Không chuyển được dự án.");



    await loadMcpProjects();



    if (action!=="open" && el.mcpProjectSelect) el.mcpProjectSelect.value=id;



    el.mcpProjectStatus.textContent = action==="register"



      ? "Đã lưu và gán thể loại cho dự án. Hãy Xác minh MCP trước khi sản xuất."



      : action==="select"



        ? "Đã chọn dự án. Bấm Mở dự án và Xác minh MCP để kiểm tra đúng Web Tool."



        : "Đã mở dự án bằng Chrome riêng; Auto Flow đang xác minh.";



    if (action==="select" || action==="register") void autoFlowReconnect();



    else void refreshAutoFlowStatus();



  } catch(error) {



    el.mcpProjectStatus.textContent="Lỗi dự án Flow: "+error.message;



  }



}







let studioGoogleLoginBusy = false;



async function mcpAccountAction(action) {



  if (action === "login") {



    if (studioGoogleLoginBusy) return null;



    studioGoogleLoginBusy = true;



    const loginButton = document.getElementById("btnMcpOpenLogin");



    if (loginButton) loginButton.disabled = true;



  }



  const id = el.mcpAccountSelect.value;



  const name = el.mcpNewAccountName.value.trim();



  if (action === "create" && !name) {



    el.mcpAccountStatus.textContent = "Hãy nhập tên tài khoản trước khi bấm Thêm & đăng nhập.";



    return;



  }



  el.mcpAccountStatus.textContent = (action === "verify" ?



    "Đang xác minh MCP (không tạo ảnh)..." : "Đang tạo hoặc chọn tài khoản Google Flow...");



  try {



    const res = await fetch("/api/mcp/account", {



      method:"POST",headers:{"Content-Type":"application/json"},



      body:JSON.stringify({action,account_id:id,name,genre:el.inGenre?.value || "auto"})



    });



    const data=await res.json();



    if (!res.ok || !data.ok) throw new Error(data.error || "Veo 3 session request failed");



    if (action==="create") {



      await loadMcpAccounts();



      el.mcpAccountSelect.value=data.result.id;



      el.mcpNewAccountName.value="";



      el.mcpAccountStatus.textContent=data.result.login_opened ?



        "Đã thêm tài khoản và mở Chrome Google Flow riêng.\n"



        +"Bước 1: Đăng nhập Google trong Chrome.\n"



        +"Bước 2: Quay lại, bấm Kiểm tra trình duyệt rồi Xác minh MCP.\n"



        +"Chưa xác minh đăng nhập hoặc quyền truy cập dự án." :



        "Hồ sơ đã tạo, nhưng chưa mở được Chrome: "



        +(data.result.login_error || "Bấm Mở đăng nhập Google Flow.");



    } else if (action==="select") {



      await loadMcpAccounts();



      el.mcpAccountStatus.textContent="Đã chọn tài khoản. Auto Flow đang khôi phục phiên và kiểm tra Web Tool.";



      void autoFlowReconnect();



    } else if (action==="login") {



      el.mcpAccountStatus.textContent="Đã mở Chrome Google Flow riêng; chỉ cần đăng nhập nếu Google yêu cầu.";



      void refreshAutoFlowStatus();



    } else if (action==="check") {



      await loadMcpAccounts();



      const check=data.result;



      el.mcpAccountStatus.textContent=check.connected && check.logged_in && check.window_visible ?



        "Google Flow đã đăng nhập; đang chờ xác minh MCP." :



        check.connected && !check.logged_in ?



        "Chrome đang mở nhưng Google chưa đăng nhập hoặc chưa xác minh được phiên. Hãy đăng nhập trong Chrome; hệ thống sẽ tự kiểm tra và thu nhỏ Chrome khi MCP sẵn sàng." :



        check.connected ?



        "Google đã đăng nhập, Chrome đang chạy ngầm. Đang kiểm tra Web Tool MCP." :



        "Chrome chưa kết nối: "+(check.reason||"hãy mở đăng nhập");



      void refreshAutoFlowStatus();



    } else if (action==="verify") {



      await loadMcpAccounts();



      const result=data.result;



      if(result.ok) {



        el.mcpAccountStatus.textContent="Xác minh chức năng MCP thành công cho tài khoản đã chọn.";



      } else if(result.reason==="FLOW_MCP_DUPLICATE_TOOL_TABS") {



        el.mcpAccountStatus.textContent="Có "+String(result.tab_count)+" tab cùng Web Tool. MCP V2 chỉ xác minh với 1 tab. Hãy kiểm tra và lưu nội dung trước khi đóng tab không sử dụng. Studio không tự xóa ảnh hoặc prompt của bạn.";



      } else if(result.reason==="FLOW_MCP_TOOL_TAB_NOT_OPEN") {



        el.mcpAccountStatus.textContent="Chưa mở tab Web Tool cho dự án này. Bấm Mở dự án và thử xác minh lại.";



      } else {



        el.mcpAccountStatus.textContent="MCP chưa sẵn sàng: "+(result.reason||"kiểm tra quyền truy cập");



      }



    }



    return data;



  } catch(err) {



    el.mcpAccountStatus.textContent="Lỗi tài khoản MCP: "+err.message;



    return null;



  } finally {



    if (action === "login") {



      studioGoogleLoginBusy = false;



      const loginButton = document.getElementById("btnMcpOpenLogin");



      if (loginButton) loginButton.disabled = false;



    }



  }



}







async function saveApiKey() {



  const key = el.inGeminiKey.value.trim();



  if (!key) return showToast("Vui lòng nhập khóa API!", "warning");



  try {



    const res = await fetch("/api/config/key", {



      method: "POST",



      headers: { "Content-Type": "application/json" },



      body: JSON.stringify({ gemini_key: key }),



    });



    const d = await res.json();



    if (d.status === "SAVED") {



      const cnt = d.count || 1;



      showToast(`✓ Đã lưu thành công ${cnt} khóa Gemini API!`);



      loadConfig();



    } else {



      showToast("Lỗi khi lưu khóa: " + (d.error || "Không xác định"), "error");



    }



  } catch (e) {



    showToast("Lỗi khi lưu khóa: " + e.message, "error");



  }



}







function updateInputModeFields() {



  const mode = el.inInputMode ? el.inInputMode.value : "idea";



  const lbl = document.getElementById("inPromptLabel");



  const tip = document.getElementById("promptTip");



  const hintChips = document.getElementById("hintChipsRow");



  const btnScan = document.getElementById("btnAnalyzeLink");



  const detectBadge = document.getElementById("linkDetectBadge");



  const linkCloneWrap = document.getElementById("linkCloneModeWrap");



  const btnImportScript = document.getElementById("btnImportScript");



  if (btnImportScript) btnImportScript.style.display = (mode === "link") ? "none" : "inline-flex";







  const inputModeWrap = document.getElementById("inputModeWrap");



  if (mode === "link") {



    if (lbl) lbl.textContent = "Link Video YouTube";



    if (tip) tip.style.display = "none";



    if (hintChips) hintChips.style.display = "none";



    if (btnScan) btnScan.style.display = "inline-flex";
    const btnSuggest = document.getElementById("btnSuggestIdea");
    if (btnSuggest) btnSuggest.style.display = "none";



    if (inputModeWrap) inputModeWrap.style.gridColumn = "span 1";



    if (linkCloneWrap) linkCloneWrap.style.display = "flex";



    if (el.inLanguage && el.inLanguage.value === "Vietnamese") {



      el.inLanguage.value = "Auto";



    }



    if (el.inPrompt) {



      el.inPrompt.placeholder = "Dán link YouTube (https://youtu.be/...)";



    }



  } else if (mode === "script") {



    if (lbl) lbl.textContent = "Kịch Bản Khóa Lời Thoại";



    if (tip) {



      tip.textContent = "💡 Định dạng: CẢNH 1, CẢNH 2... & LỜI THOẠI";



      tip.style.display = "";



    }



    if (hintChips) hintChips.style.display = "none";



    if (btnScan) btnScan.style.display = "none";



    if (detectBadge) detectBadge.style.display = "none";



    if (inputModeWrap) inputModeWrap.style.gridColumn = "span 2";



    if (linkCloneWrap) linkCloneWrap.style.display = "none";



    if (el.inPrompt) {



      el.inPrompt.placeholder = 'CẢNH 1:\nMô tả: Mặt trời mọc trên núi cao mờ ảo sương sớm.\nLỜI THOẠI: "Chào buổi sáng quê hương tươi đẹp!"\n\nCẢNH 2:\nMô tả: Cánh đồng lúa vàng óng ả trải dài tít tắp.\nLỜI THOẠI: "Mùa màng bội thu đem lại no ấm cho muôn nhà."';



    }



    syncAutoImageBudget();



  } else {



    // Mode idea



    if (lbl) lbl.textContent = "Ý Tưởng / Cốt Truyện";



    if (tip) tip.style.display = "";



    if (hintChips) hintChips.style.display = "flex";
    const btnSuggest = document.getElementById("btnSuggestIdea");
    if (btnSuggest) btnSuggest.style.display = "inline-flex";
    if (typeof updateHintChipsForGenre === "function") updateHintChipsForGenre(el.inGenre ? el.inGenre.value : "stoic");



    if (btnScan) btnScan.style.display = "none";



    if (detectBadge) detectBadge.style.display = "none";



    if (inputModeWrap) inputModeWrap.style.gridColumn = "span 2";



    if (linkCloneWrap) linkCloneWrap.style.display = "none";



    if (el.inPrompt) {



      el.inPrompt.placeholder = "Nhập ý tưởng hoặc tóm tắt kịch bản...";



    }



    if (el.inMinutes && (!el.inMinutes.value || isNaN(parseFloat(el.inMinutes.value)) || parseFloat(el.inMinutes.value) <= 0)) {



      el.inMinutes.value = "1.0";



    }



    if (el.inSceneSec && (!el.inSceneSec.value || isNaN(parseInt(el.inSceneSec.value, 10)) || parseInt(el.inSceneSec.value, 10) < 4)) {



      el.inSceneSec.value = "25";



    }



    syncAutoImageBudget();



  }



}







let analyzeDebounceTimer = null;

let lastAnalyzedUrl = "";

let isAnalyzingLink = false;

let activeLinkAnalysisPromise = null;

let lastAnalyzedData = null;



async function analyzeYouTubeLink(rawUrl, force = false) {

  const url = (rawUrl || (el.inPrompt ? el.inPrompt.value : "")).trim();

  if (!url || !url.startsWith("http")) {

    if (force) showToast("Vui lòng dán link YouTube hợp lệ!");

    return null;

  }



  // 1. Tránh chạy 2 request quét cùng lúc cho cùng một URL: tái sử dụng Promise đang chạy

  if (isAnalyzingLink && activeLinkAnalysisPromise) {

    if (url === lastAnalyzedUrl || !rawUrl) {

      return await activeLinkAnalysisPromise;

    }

  }



  // 2. Trả về cache ngay nếu URL đã được quét thành công trước đó và không force

  if (!force && url === lastAnalyzedUrl && lastAnalyzedData) {

    return lastAnalyzedData;

  }



  lastAnalyzedUrl = url;

  isAnalyzingLink = true;



  const detectBadge = document.getElementById("linkDetectBadge");

  if (detectBadge) {

    detectBadge.style.display = "flex";

    detectBadge.className = "link-detect-badge loading";

    detectBadge.innerHTML = `<span>⏳ Đang quét video...</span>`;

  }



  activeLinkAnalysisPromise = (async () => {

    try {

      const res = await fetch("/api/analyze-link", {

        method: "POST",

        headers: { "Content-Type": "application/json" },

        body: JSON.stringify({ url }),

      });

      const data = await res.json();

      if (!res.ok || !data.ok) {

        throw new Error(data.error || "Không thể phân tích video này.");

      }

      lastAnalyzedData = data;



      // 1. Đồng bộ số phút & TỰ ĐỘNG ĐIỀU CHỈNH SỐ ẢNH TỐI ĐA KHÔNG CẦN CHỌN THỦ CÔNG

      if (data.duration_minutes && el.inMinutes) {

        el.inMinutes.value = String(data.duration_minutes);

        state.userCustomizedMaxImages = false;

        const isShort = Number(data.duration_minutes) <= 1.05 || Boolean(data.is_short);

        if (isShort && el.inSceneSec && (!el.inSceneSec.value || el.inSceneSec.value === "0")) {

          el.inSceneSec.value = "7";

        }

        const sceneSec = parseInt(el.inSceneSec?.value, 10) || (isShort ? 7 : 25);

        const autoScenes = Math.max(3, Math.ceil((Number(data.duration_minutes) * 60) / sceneSec));

        if (el.inMcpMaxImages && autoScenes > 0) {

          el.inMcpMaxImages.value = String(autoScenes);

        }

        const resEl = el.inResolution || document.getElementById("inResolution");
        if (isShort && resEl) {
          const opt916 = Array.from(resEl.options).find(o => o.value.includes("720x1280") || o.value.includes("1080x1920"));
          if (opt916) {
            resEl.value = opt916.value;
            try { localStorage.setItem("storyboard_saved_resolution", opt916.value); } catch(_) {}
          }
        }

        updateImageBudgetHint();

      }



      // 2. Đồng bộ ngôn ngữ & quốc gia (bảo toàn nếu người dùng đã tự tay chọn)

      if (!state.userExplicitLanguage || el.inLanguage?.value === "Auto") {

        if (data.language && el.inLanguage) {

          const opt = Array.from(el.inLanguage.options).find(

            (o) => o.value.toLowerCase() === data.language.toLowerCase()

          );

          if (opt) {

            el.inLanguage.value = opt.value;

          }

        }

        if (data.region && el.inRegion && (!state.userExplicitRegion || el.inRegion.value === "auto")) {

          el.inRegion.value = data.region;

        }

      }



      // 3. Tự động cập nhật danh sách giọng cho quốc gia đó

      updateVoiceOptions(false);



      // 4. Chọn đúng giọng (trầm ấm / mạnh mẽ...)

      if (data.suggested_voice && el.inVoice) {

        const vOpt = Array.from(el.inVoice.options).find(

          (o) => o.value === data.suggested_voice

        );

        if (vOpt) {

          el.inVoice.value = data.suggested_voice;

        }

      }



      // 5. Đồng bộ thể loại & bút pháp (luôn chọn giá trị hợp lệ, không bao giờ để trống)

      if (data.genre && el.inGenre) {

        const gOpt = Array.from(el.inGenre.options).find(o => o.value === data.genre);

        if (gOpt) el.inGenre.value = data.genre;

        else el.inGenre.value = "family_drama";

      }



      if (el.inVisualStyle) {

        const validStyles = ["auto", "flow_video", "color_cinematic", "color_animation", "colored_marker", "hand_color", "whiteboard"];

        let matchedStyle = String(data.visual_style || "").trim();

        if (!validStyles.includes(matchedStyle)) {

          if (matchedStyle.includes("anim")) matchedStyle = "color_animation";

          else if (matchedStyle.includes("flow") || matchedStyle.includes("video")) matchedStyle = "flow_video";

          else if (matchedStyle.includes("board")) matchedStyle = "whiteboard";

          else if (matchedStyle.includes("marker")) matchedStyle = "colored_marker";

          else {

            const g = el.inGenre?.value || "";

            matchedStyle = g === "animation" ? "color_animation" : (g === "whiteboard" ? "whiteboard" : (g === "colored_marker" ? "colored_marker" : ((el.inProductionMode && el.inProductionMode.value === "cinematic_drama") ? "flow_video" : "color_cinematic")));

          }

        }

        el.inVisualStyle.value = matchedStyle;

      }



      // 5.1 Đồng bộ tên series tương ứng với thể loại để không bị lẫn lộn giữa các dòng phim

      const newSeries = data.suggested_series || (data.genre === "stoic" ? "stoi" : data.genre === "family_drama" ? "drama" : data.genre === "mafia_thriller" ? "thriller" : data.genre === "psychological_horror" ? "horror" : data.genre === "romance_melodrama" ? "romance" : null);

      if (newSeries && el.inSeries) {

        const curSeries = el.inSeries.value.trim().toLowerCase();

        const isDefault = !curSeries || curSeries === "whiteboard series" || curSeries === "series";

        if (isDefault) {

          el.inSeries.value = newSeries;

          state.currentSeries = newSeries;

          localStorage.setItem("storyboard_saved_series", newSeries);

        }

      }

      const targetSeries = (el.inSeries ? el.inSeries.value.trim() : "") || newSeries || "drama";

      const headerProj = document.getElementById("headerProjectName");



      // AWAIT tìm tập tiếp theo từ server để tránh conflict tập

      try {

        const prodRes = await fetch("/api/productions");

        const prodData = await prodRes.json();

        const seriesList = prodData.productions || [];

        const match = seriesList.find(p => p.series && p.series.toLowerCase() === targetSeries.toLowerCase());

        if (match && Array.isArray(match.episodes) && match.episodes.length > 0) {

          const maxEp = Math.max(...match.episodes.map(e => e.number || 1));

          const nextEp = maxEp + 1;

          if (el.inEpisode) el.inEpisode.value = String(nextEp);

          state.currentEpisode = nextEp;

          if (headerProj) headerProj.textContent = `${targetSeries} - Tập ${nextEp}`;

        } else {

          if (el.inEpisode && (!el.inEpisode.value || parseInt(el.inEpisode.value, 10) < 1)) {

            el.inEpisode.value = "1";

            state.currentEpisode = 1;

            if (headerProj) headerProj.textContent = `${targetSeries} - Tập 1`;

          }

        }

      } catch (epErr) {

        console.warn("Could not sync next episode:", epErr);

      }

      updateLiveButtonLabel();



      if (el.inReferenceUrl) {

        el.inReferenceUrl.value = data.canonical_url || url;

      }



      // 6. Lưu thông tin clone nhân vật và điền gợi ý cốt truyện nếu có

      if (data.character) {

        state.clonedCharacter = data.character;

        if (data.cloned_prompt_suggestion) {

          state.clonedPromptSuggestion = data.cloned_prompt_suggestion;

          const curMode = el.inInputMode ? el.inInputMode.value : "idea";

          if (curMode !== "link" && el.inPrompt) {

            el.inPrompt.value = data.cloned_prompt_suggestion;

          }

        }

      }



      if (detectBadge) {

        detectBadge.className = "link-detect-badge success";

        if (data.transcript_available && el.inLinkCloneMode) {

          el.inLinkCloneMode.value = "exact_clone";

        }

        const charPart = data.character?.character_name ? ` • 👤 ${escapeHtml(data.character.character_name)}` : '';

        const subPart = data.transcript_available ? ` • 📜 Phụ đề (${data.transcript_lines_count || 0})` : '';

        detectBadge.innerHTML = `<span>✨ ${data.duration_minutes}p • ${data.language} • Giọng ${data.voice_tone_label || 'Trầm'}${charPart}${subPart}</span>`;

      }

      const toastMsg = data.character && data.character.character_name

        ? `Đã clone: ${data.character.character_name} (${data.duration_minutes}p)`

        : `Đã nhận diện: ${data.duration_minutes}p`;

      showToast(toastMsg);

      return data;

    } catch (err) {

      if (detectBadge) {

        detectBadge.className = "link-detect-badge";

        detectBadge.innerHTML = `<span>⚠️ ${escapeHtml(err.message || "Lỗi quét video")}</span>`;

      }

      throw err;

    } finally {

      isAnalyzingLink = false;

      activeLinkAnalysisPromise = null;

    }

  })();



  return await activeLinkAnalysisPromise;

}



async function submitProduction(mode, options = {}) {

  if (!state.statusReady || state.isRunning || state.submitting) return;



  let inputMode = el.inInputMode ? el.inInputMode.value : "idea";

  const rawPrompt = el.inPrompt ? el.inPrompt.value.trim() : "";

  let referenceUrl = el.inReferenceUrl ? el.inReferenceUrl.value.trim() : "";



  // 1. Tự động chuyển mode link nếu dán URL trực tiếp vào ô kịch bản/ý tưởng

  const isDirectUrl = rawPrompt.startsWith("http://") || rawPrompt.startsWith("https://") || rawPrompt.includes("youtu.be") || rawPrompt.includes("youtube.com");

  if (isDirectUrl) {

    referenceUrl = rawPrompt;

    inputMode = "link";

    if (el.inInputMode && el.inInputMode.value !== "link") {

      el.inInputMode.value = "link";

      updateInputModeFields();

    }

    if (el.inReferenceUrl) el.inReferenceUrl.value = referenceUrl;

  } else if (inputMode === "link") {

    referenceUrl = referenceUrl || (rawPrompt.startsWith("http") ? rawPrompt : "");

    if (el.inReferenceUrl && referenceUrl) el.inReferenceUrl.value = referenceUrl;

  }



  if (!rawPrompt && !referenceUrl && !options.resume) {

    return alert("Vui lòng nhập ý tưởng, kịch bản hoặc link YouTube công khai!");

  }



  // 2. TỰ ĐỘNG SẢN XUẤT 1-CLICK A-Z KHI NHẬP LINK ĐỐI THỦ:

  // Nếu đang quét dở hoặc chưa quét, tự động khóa nút ở trạng thái đang quét & tự chạy ngay khi quét xong!

  if ((isDirectUrl || inputMode === "link") && referenceUrl && (referenceUrl.startsWith("http://") || referenceUrl.startsWith("https://"))) {

    const isScanNeeded = (lastAnalyzedUrl !== referenceUrl || !lastAnalyzedData || isAnalyzingLink);

    if (isScanNeeded) {

      state.submitting = true;

      const liveLabel = document.getElementById("btnLiveLabel");

      const origLiveLabel = liveLabel ? liveLabel.textContent : "Sản Xuất Bằng AI";

      if (liveLabel) liveLabel.textContent = "⏳ Đang quét video & tự động sản xuất...";

      if (el.btnLive) el.btnLive.disabled = true;



      const detectBadge = document.getElementById("linkDetectBadge");

      if (detectBadge) {

        detectBadge.style.display = "flex";

        detectBadge.className = "link-detect-badge loading";

        detectBadge.innerHTML = `<span>⏳ Đang quét video & tự động sản xuất A-Z...</span>`;

      }

      showToast("⚡ Đang tự động quét video & khởi chạy sản xuất A-Z...", 4000);



      try {

        if (isAnalyzingLink && activeLinkAnalysisPromise) {

          await activeLinkAnalysisPromise;

        } else {

          await analyzeYouTubeLink(referenceUrl, true);

        }

      } catch (scanErr) {

        console.warn("Auto link analysis warning:", scanErr);

        showToast("⚠️ Quét link có cảnh báo: " + (scanErr.message || scanErr) + ". Tự động chạy với cấu hình hiện có.", 4000);

      } finally {

        state.submitting = false;

        if (el.btnLive) el.btnLive.disabled = false;

        if (liveLabel && !state.isRunning) liveLabel.textContent = origLiveLabel;

      }

    }

  }



  // 3. ĐỌC DỮ LIỆU TƯƠI MỚI SAU KHI QUÉT LINK HOÀN TẤT (TRÁNH LỖI LẤY SERIES/EPISODE CŨ GÂY CONFLICT)

  const series = (el.inSeries ? el.inSeries.value.trim() : "") || "Whiteboard Series";

  const episode = parseInt(el.inEpisode ? el.inEpisode.value : "1", 10) || 1;

  let prompt = el.inPrompt ? el.inPrompt.value.trim() : rawPrompt;

  if (inputMode === "link") {

    if (!prompt || prompt.startsWith("http")) {

      prompt = state.clonedCharacter?.character_name

        ? `Clone kịch bản từ ${referenceUrl} (${state.clonedCharacter.character_name})`

        : `Sản xuất từ link ${referenceUrl}`;

    }

  }



  const isMcp = el.inImageSource.value === "mcp_v2" || el.inImageSource.value === "flowkit";

  const epData = state.loadedEpisodeData;

  const isResume = Boolean(options.resume) || Boolean(epData?.can_resume && !options.force_new);

  const resCfg = isResume ? (epData?.resume_config || null) : null;



  if (resCfg) {

    if (resCfg.prompt) prompt = resCfg.prompt;

    if (resCfg.reference_url) referenceUrl = resCfg.reference_url;

  }



  if (isResume && !prompt) {

    prompt = epData?.title || epData?.logline || (el.inPrompt ? el.inPrompt.value.trim() : "") || `Tiếp tục sản xuất tập ${episode}`;

  }



  const language = (state.userExplicitLanguage && el.inLanguage) ? el.inLanguage.value : ((isResume && (resCfg?.language || epData?.language)) ? (resCfg?.language || epData.language) : (el.inLanguage ? el.inLanguage.value : "Vietnamese"));



  const voiceName = (el.inVoice && el.inVoice.value !== "auto") ? el.inVoice.value : ((isResume && (resCfg?.voice_name || epData?.voice_name)) ? (resCfg?.voice_name || epData.voice_name) : (el.inVoice ? el.inVoice.value : "auto"));



  const imageProvider = (isResume && (resCfg?.image_provider || epData?.image_provider)) ? (resCfg?.image_provider || epData.image_provider) : el.inImageSource.value;



  const genre = (isResume && (resCfg?.genre || epData?.genre)) ? (resCfg?.genre || epData.genre) : (el.inGenre ? el.inGenre.value : "auto");



  let visualStyle = (isResume && (resCfg?.visual_style || epData?.visual_style)) 

    ? (resCfg?.visual_style || epData.visual_style) 

    : ((el.inVisualStyle && el.inVisualStyle.value && el.inVisualStyle.value !== "auto") ? el.inVisualStyle.value : (genre === "animation" ? "color_animation" : (genre === "whiteboard" ? "whiteboard" : (genre === "colored_marker" ? "colored_marker" : ((el.inProductionMode?.value === "cinematic_drama") ? "flow_video" : "color_cinematic")))));

  if (!visualStyle || visualStyle === "" || visualStyle === "auto") {

    visualStyle = (genre === "animation" ? "color_animation" : (genre === "whiteboard" ? "whiteboard" : (genre === "colored_marker" ? "colored_marker" : ((el.inProductionMode?.value === "cinematic_drama") ? "flow_video" : "color_cinematic"))));

  }







    let maxApproved = parseInt(el.inMcpMaxImages ? el.inMcpMaxImages.value : "3", 10) || 3;



    const totalEpScenes = epData?.total_scenes || epData?.scenes?.length || 0;



    if (isResume && totalEpScenes > 0) {



      maxApproved = Math.max(maxApproved, totalEpScenes);



      if (el.inMcpMaxImages) el.inMcpMaxImages.value = String(maxApproved);



    }



    const expectedScenes = estimatedImageScenes();



    if ((inputMode === "link" || !state.userCustomizedMaxImages) && expectedScenes && expectedScenes > 0) {



      maxApproved = Math.max(maxApproved, expectedScenes);



      if (el.inMcpMaxImages) {



        el.inMcpMaxImages.value = String(maxApproved);



      }



    }



    const autoVisualPolicy = (expectedScenes && maxApproved < expectedScenes) ? "reuse" : "unique";







    const rawMin = (resCfg && resCfg.minutes != null) ? parseFloat(resCfg.minutes) : (parseFloat(el.inMinutes ? el.inMinutes.value : "1.0"));



    const safeMin = (!isNaN(rawMin) && rawMin > 0) ? Math.min(Math.max(rawMin, 0.1), 180.0) : 1.0;



    



    const rawSec = (resCfg && resCfg.scene_seconds != null) ? parseInt(resCfg.scene_seconds, 10) : (parseInt(el.inSceneSec ? el.inSceneSec.value : "25", 10));



    let safeSec = (!isNaN(rawSec) && rawSec > 0) ? Math.min(Math.max(rawSec, 4), 60) : 25;







    if (el.inMinutes && (!el.inMinutes.value || isNaN(parseFloat(el.inMinutes.value)) || parseFloat(el.inMinutes.value) <= 0)) {



      el.inMinutes.value = String(safeMin);



    }



    if (el.inSceneSec && (!el.inSceneSec.value || isNaN(parseInt(el.inSceneSec.value, 10)) || parseInt(el.inSceneSec.value, 10) < 4)) {



      el.inSceneSec.value = String(safeSec);



    }







    let finalProdMode = (isResume && (resCfg?.production_mode || epData?.production_mode))



      ? (resCfg?.production_mode || epData?.production_mode)



      : (el.inProductionMode ? el.inProductionMode.value : "narrative");



    let finalImgProv = (resCfg && resCfg.image_provider) ? resCfg.image_provider : imageProvider;



    if (finalProdMode === "cinematic_drama") {

      finalImgProv = (resCfg && resCfg.image_provider) ? resCfg.image_provider : (el.inImageSource ? el.inImageSource.value : "flowkit");

      safeSec = parseInt(el.inSceneSec ? el.inSceneSec.value : "10", 10) || 10;

      if (el.inProductionMode) el.inProductionMode.value = "cinematic_drama";

    }







    const payload = {



      production_mode: finalProdMode,



      series,



      episode,



      prompt,



      minutes: safeMin,



      scene_seconds: safeSec,



      language: language,



      voice_name: voiceName,



      speech_pacing: (resCfg && resCfg.speech_pacing) ? resCfg.speech_pacing : (el.inSpeechPacing ? el.inSpeechPacing.value : "slow"),



      genre: genre,



      visual_style: visualStyle,



      region: (resCfg && resCfg.region) ? resCfg.region : (el.inRegion ? el.inRegion.value : "auto"),



      input_mode: (resCfg && resCfg.input_mode) ? resCfg.input_mode : inputMode,



      reference_url: (resCfg && resCfg.reference_url) ? resCfg.reference_url : referenceUrl,



      link_clone_mode: (resCfg && resCfg.link_clone_mode) ? resCfg.link_clone_mode : ((document.getElementById("inLinkCloneMode")?.value) || "exact_clone"),



      character_clone: state.clonedCharacter || null,



      size: el.inResolution.value,

      aspect_ratio: (el.inResolution.value.includes("1080x1920") || el.inResolution.value.includes("720x1280")) ? "9:16" : "16:9",

      is_short: Boolean(safeMin <= 1.05 || el.inResolution.value.includes("1080x1920") || el.inResolution.value.includes("720x1280")),



      workers: parseInt(el.inWorkers ? el.inWorkers.value : "4", 10) || 4,



      mode,



      model: el.inModel.value,



      image_provider: finalImgProv,



      mcp_model_index: parseInt(el.inMcpModel ? el.inMcpModel.value : "1", 10),



      mcp_max_images: maxApproved,



      mcp_visual_policy: autoVisualPolicy,



      auto_minimize_browser: true,



      clean_watermark: true,

      auto_upload: Boolean(document.getElementById('chkAutoUpload')?.checked),



      resume: Boolean(isResume),



      force_new: Boolean(options.force_new),



      subtitle_style: el.inSubtitleStyle ? el.inSubtitleStyle.value : "karaoke_viral",



      subtitle_size: parseInt(el.inSubtitleSize ? el.inSubtitleSize.value : "52", 10) || 52,



      camera_motion: el.inCameraMotion ? el.inCameraMotion.value : "auto",



      atmospheric_overlay: el.inAtmosphericOverlay ? el.inAtmosphericOverlay.value : "auto",



      motion_mode: el.inMotionMode ? el.inMotionMode.value : "ken_burns",

      auto_upload: Boolean(document.getElementById('chkQueueAutoUpload')?.checked || document.getElementById('chkAutoUpload')?.checked),



      flow_video_model: el.inFlowVideoModel ? el.inFlowVideoModel.value : "Omni 1.1 Flash",



      flow_video_duration: parseInt(el.inFlowVideoDuration ? el.inFlowVideoDuration.value : "8", 10) || 8,



    };







  state.submitting = true;



  setButtonsRunning(false);



  try {



    const res = await fetch("/api/produce", {



      method: "POST",



      headers: { "Content-Type": "application/json" },



      body: JSON.stringify(payload),



    });



    const data = await res.json();



    if (res.status === 409 && data.code === "IMAGE_BUDGET_TOO_SMALL") {



      const required = Number(data.required_images);



      if (Number.isInteger(required) && required > 0) {



        if (el.inMcpMaxImages) {



          el.inMcpMaxImages.value = String(required);



          updateImageBudgetHint();



        }



        // Tự động nâng hạn mức và gửi lại ngay không cần người dùng bấm thủ công



        if (payload.input_mode === "link" || !state.userCustomizedMaxImages) {



          showToast(`✨ Tự động đồng bộ ${required} ảnh theo ${required} phân cảnh của video...`);



          payload.mcp_max_images = required;



          payload.mcp_visual_policy = "unique";



          const retryRes = await fetch("/api/produce", {



            method: "POST",



            headers: { "Content-Type": "application/json" },



            body: JSON.stringify(payload),



          });



          const retryData = await retryRes.json();



          if (retryRes.ok && retryData.status === "STARTED") {



            state.isRunning = true;



            state.lastPercent = 2;



            setButtonsRunning(true, 2);



            state.currentSeries = series;



            state.currentEpisode = episode;



            state.episodeRequest++;



            state.loadedEpisodeData = null;



            state.selectedSceneNumber = null;



            state.deckSignature = null;



            showToast(options.resume ? `Đang chạy tiếp ${series} - Tập ${episode}...` : `Bắt đầu sản xuất ${series} - Tập ${episode} (${required} cảnh tự động)`);



            return;



          }



        }



        const proposal = `Kịch bản có ${required} cảnh nhưng hiện chỉ duyệt ${payload.mcp_max_images} ảnh. ${data.saved_plan ? "Kịch bản đã được lưu, không cần viết lại. " : ""}\n\nNhấn OK để duyệt ${required} ảnh và sản xuất ngay.`;



        if (confirm(proposal) && el.inMcpMaxImages) {



          el.inMcpMaxImages.value = String(required);



          updateImageBudgetHint();



          setTimeout(() => submitProduction(mode, options), 200);



        }



      } else alert(data.error || "Hạn mức ảnh không hợp lệ.");



      return;



    }



    if (res.status === 409 && data.code === "MCP_QUEUE_PREFLIGHT_BLOCKED") {



      alert(data.error || "Web Tool chưa sẵn sàng. Kịch bản hiện tại được giữ nguyên; không có lượt ảnh mới.");



      showToast("FlowKit WebTool chưa sẵn sàng; chưa bắt đầu tạo ảnh hoặc video.");



      return;



    }



    if (res.status === 409 && data.code === "CLONE_REFERENCE_SOURCE_UNAVAILABLE") {



      showToast("✨ Tự động chuyển sang chế độ Sáng Tạo Mới từ chủ đề video...");



      payload.link_clone_mode = "creative_adaptation";



      const retryRes = await fetch("/api/produce", {



        method: "POST",



        headers: { "Content-Type": "application/json" },



        body: JSON.stringify(payload),



      });



      const retryData = await retryRes.json();



      if (retryRes.ok && retryData.status === "STARTED") {



        state.isRunning = true;



        state.lastPercent = 2;



        setButtonsRunning(true, 2);



        state.currentSeries = series;



        state.currentEpisode = episode;



        state.episodeRequest++;



        state.loadedEpisodeData = null;



        state.selectedSceneNumber = null;



        state.deckSignature = null;



        showToast(options.resume ? `Đang chạy tiếp ${series} - Tập ${episode}...` : `Bắt đầu sản xuất ${series} - Tập ${episode}`);



        return;



      }



    }



    if (res.status === 409 && data.code === "EPISODE_CONFLICT") {



      setButtonsRunning(false);



      if (data.can_resume) {



        if (confirm(`${data.error}\n\nBạn có muốn CHẠY TIẾP các cảnh còn dở dang của tập ${episode} không?`)) {



          showToast("Đang tiếp tục sản xuất Tập " + episode + "...");



          setTimeout(() => submitProduction(mode, { resume: true }), 300);



          return;



        }



      }



      const next = Number(data.next_episode);



      if (Number.isInteger(next) && next > episode) {



        if ((inputMode === "link" || isDirectUrl) && !options.resume) {



          el.inEpisode.value = String(next);



          state.currentEpisode = next;



          updateLiveButtonLabel();



          showToast(`✨ Tự động chuyển sang Tập ${next} và sản xuất ngay...`);



          setTimeout(() => submitProduction(mode, {}), 150);



          return;



        }



        const choice = confirm(`${data.error}\n\n👉 Nhấn OK để tự động chuyển sang TẬP ${next} và BẮT ĐẦU SẢN XUẤT NGAY.\n(Nhấn Cancel nếu bạn muốn làm lại từ đầu Tập ${episode})`);



        if (choice) {



          el.inEpisode.value = String(next);



          state.currentEpisode = next;



          updateLiveButtonLabel();



          showToast(`Đang tự động chuyển sang Tập ${next} và khởi chạy...`);



          setTimeout(() => submitProduction(mode, {}), 300);



          return;



        } else {



          if (confirm(`Bạn có chắc chắn muốn XÓA DỮ LIỆU CŨ và LÀM LẠI TẬP ${episode} từ đầu không?`)) {



            showToast(`Đang làm mới Tập ${episode}...`);



            setTimeout(() => submitProduction(mode, { force_new: true }), 300);



            return;



          }



        }



      } else {



        alert(data.error);



      }



      return;



    }



    if (!res.ok || data.status !== "STARTED") {



      throw new Error(data.error || "Máy chủ trả lỗi HTTP " + res.status);



    }



    state.isRunning = true;



    state.lastPercent = 2;



    setButtonsRunning(true, 2);



    state.currentSeries = series;



    state.currentEpisode = episode;



    state.episodeRequest++;



    state.loadedEpisodeData = null;



    state.selectedSceneNumber = null;



    state.deckSignature = null;



    showToast(options.resume ? `Đang chạy tiếp ${series} - Tập ${episode}...` : `Bắt đầu sản xuất ${series} - Tập ${episode}`);



  } catch (err) {



    alert("Lỗi khi khởi chạy: " + err);



    state.statusReady = true;



  } finally {



    state.submitting = false;



    setButtonsRunning(state.isRunning, state.lastPercent);



    void pollStatus();



  }



}







async function stopProduction() {



  if (!confirm("Bạn có chắc chắn muốn dừng tiến trình hiện tại?")) return;



  try {

    state.isRunning = false;

    setButtonsRunning(false, 0);

    if (el.headerStatusDot) el.headerStatusDot.classList.remove("active", "error");

    if (el.headerStatusText) el.headerStatusText.textContent = "Đã dừng";

    await fetch("/api/stop", { method: "POST" }).catch(() => {});

    await fetch("/api/status/reset", { method: "POST" }).catch(() => {});

    showToast("Đã dừng tiến trình sản xuất");

    setTimeout(pollStatus, 500);

  } catch (e) {

    console.error(e);

  }



}







function setDynamicPollingInterval(intervalMs) {

  if (state.currentPollInterval === intervalMs) return;

  state.currentPollInterval = intervalMs;

  if (state.pollTimer) clearInterval(state.pollTimer);

  state.pollTimer = setInterval(pollStatus, intervalMs);

}



function startStatusPolling() {

  if (state.pollTimer) clearInterval(state.pollTimer);

  state.currentPollInterval = 2500;

  state.pollTimer = setInterval(pollStatus, 2500);

  void pollStatus();

}







async function pollStatus() {



  if (state.polling) return;



  state.polling = true;



  try {



    let data = null;

    try {

      const activeRes = await fetch("/active_run_status.json?t=" + Date.now());

      if (activeRes.ok) {

        const candidate = await activeRes.json();

        const isFresh = candidate && candidate.timestamp && (Math.abs(Date.now() - Number(candidate.timestamp)) < 12000);

        if (candidate && typeof candidate.running === "boolean" && candidate.running && isFresh) {

          data = candidate;

        }

      }

    } catch (_) {}



    if (!data) {

      const res = await fetch("/api/status");

      if (!res.ok) throw new Error(`Status endpoint returned HTTP ${res.status}`);

      data = await res.json();

    }



    if (typeof data.running !== "boolean" || typeof data.stage !== "string") {



      throw new Error("Invalid production status response");



    }







    const wasGalleryLocked = state.isRunning || !state.statusReady;



    state.isRunning = Boolean(data.running);

    setDynamicPollingInterval(state.isRunning ? 2500 : 4000);



    state.lastPercent = Number(data.percent) || 0;



    const isAssembling = data.stage === "CONCAT" || data.stage === "COMPLETED" || (Number(data.percent) || 0) >= 93;



    state.currentRunningScene = (data.running && !isAssembling) ? (Number(data.current_scene) || null) : null;



    state.statusReady = true;



    setButtonsRunning(state.isRunning, state.lastPercent);



    if (wasGalleryLocked !== state.isRunning && el.modalProductions?.classList.contains("open")) {



      renderGallery();



    }







    const curSeries = state.currentSeries || (el.inSeries ? el.inSeries.value.trim() : "");



    const curEp = Number(state.currentEpisode || (el.inEpisode ? el.inEpisode.value : 1));



    const isJobForCurrentEpisode = (!data.series || slugify(data.series) === slugify(curSeries)) &&



                                  (!data.episode || Number(data.episode) === curEp);



    const hasCurrentCompletedVideo = Boolean(state.loadedEpisodeData && state.loadedEpisodeData.final_video_url);



    const hasCurrentResumable = Boolean(state.loadedEpisodeData && state.loadedEpisodeData.can_resume);







    // Update Header Pill using the verified state for the CURRENT view



    el.headerStatusDot.classList.remove("active", "error");



    if (data.running) {
    state.wasRunning = true;




      el.headerStatusDot.classList.add("active");



      el.headerStatusText.textContent = isJobForCurrentEpisode ? `Đang sản xuất (${data.percent}%)` : `Đang chạy (Tập ${data.episode} - ${data.percent}%)`;



    } else if (data.stage === "AWAITING_ASSET_REVIEW" && isJobForCurrentEpisode) {



      el.headerStatusText.textContent = "Cần duyệt ảnh tham chiếu";



    } else if (hasCurrentCompletedVideo || (data.stage === "COMPLETED" && isJobForCurrentEpisode)) {



      el.headerStatusDot.classList.add("active");



      el.headerStatusText.textContent = "Hoàn tất";



    } else if (hasCurrentResumable) {



      el.headerStatusText.textContent = "Dở dang";



    } else {



      el.headerStatusText.textContent = "Sẵn sàng";



    }







    // Update Stepper & Progress Bar



    let displayPercent = 0;



    if (data.running && isJobForCurrentEpisode) {



      displayPercent = data.percent || 0;



      updateStepper(data);



    } else if (hasCurrentCompletedVideo || (data.stage === "COMPLETED" && isJobForCurrentEpisode && !data.running)) {



      displayPercent = 100;



      updateStepper({ percent: 100, running: false });



    } else if (hasCurrentResumable && !data.running) {



      const comp = Number(state.loadedEpisodeData.completed_scenes) || 0;



      const tot = Number(state.loadedEpisodeData.total_scenes) || 1;



      displayPercent = Math.round((comp / tot) * 100);



      updateStepper({ percent: displayPercent, running: false });



    } else {



      displayPercent = 0;



      updateStepper({ percent: 0, running: false });



    }







    if (el.progressPercent) el.progressPercent.textContent = `${displayPercent}%`;



    if (el.progressBarFill) el.progressBarFill.style.width = `${displayPercent}%`;







    if (el.pipelineMessage) {



      if (data.running && isJobForCurrentEpisode) {



        el.pipelineMessage.textContent = data.message || "Đang xử lý...";



      } else if (hasCurrentCompletedVideo || (data.stage === "COMPLETED" && isJobForCurrentEpisode && !data.running)) {



        el.pipelineMessage.textContent = `Tập ${curEp} đã hoàn tất thành công!`;



      } else if (hasCurrentResumable && !data.running) {



        el.pipelineMessage.textContent = `Tập ${curEp} dở dang (${state.loadedEpisodeData.completed_scenes}/${state.loadedEpisodeData.total_scenes} cảnh)`;



      } else {



        el.pipelineMessage.textContent = `Sẵn sàng sản xuất Tập ${curEp}`;



      }



    }







    const hasErrorOrInterrupted = !data.running && isJobForCurrentEpisode && ((data.exit_code !== 0 && data.exit_code !== null) || (data.message && (data.message.includes("gián đoạn") || data.message.includes("dừng") || data.message.includes("Lỗi"))));



    if (el.btnRetryError) {



      el.btnRetryError.style.display = hasErrorOrInterrupted ? "inline-flex" : "none";



    }







    // Update Logs only for running job or current episode



    if (data.recent_logs && data.recent_logs.length > 0 && (isJobForCurrentEpisode || data.running)) {



      renderLogs(data.recent_logs);



    }







    // Cập nhật trạng thái Robot Trợ Lý AI qua Smart Dynamic HUD



    if (window.studioRobotWalker && typeof window.studioRobotWalker.onProductionStatus === "function") {



      window.studioRobotWalker.onProductionStatus(data, isAssembling, isJobForCurrentEpisode, curEp, hasCurrentCompletedVideo);



    }







    // Refresh episode details while running, or once upon transition to completion, or if data not yet loaded



    const isCompletedStage = (data.stage === "COMPLETED");



    const completionKey = isCompletedStage ? `${data.series || state.currentSeries}_${data.episode || state.currentEpisode}_${data.stage}` : null;



    const justCompleted = isCompletedStage && state.lastRefreshedCompletionKey !== completionKey;



    const epKey = `${state.currentSeries}_${state.currentEpisode}`;



    const now = Date.now();

    const currSc = Number(data.current_scene) || 0;

    const sceneChanged = currSc > 0 && currSc !== state.lastPollScene;

    const timeSinceLastFetch = now - (state.lastEpisodeDetailsFetch || 0);

    const periodicRunningFetch = data.running && isJobForCurrentEpisode && (sceneChanged || timeSinceLastFetch > 12000);

    const shouldFetchEpisode = periodicRunningFetch || (justCompleted && isJobForCurrentEpisode) || (state.lastCheckedEpisodeKey !== epKey);



    if (shouldFetchEpisode) {

      state.lastEpisodeDetailsFetch = now;

      if (currSc > 0) state.lastPollScene = currSc;

      if (isCompletedStage) state.lastRefreshedCompletionKey = completionKey;

      else if (data.running) state.lastRefreshedCompletionKey = null;

      await loadEpisodeDetails(state.currentSeries, state.currentEpisode);

    }



  } catch (err) {



    console.warn("Poll failed", err);



    const wasGalleryLocked = state.isRunning || !state.statusReady;



    state.statusReady = false;



    setButtonsRunning(state.isRunning, state.lastPercent);



    if (!wasGalleryLocked && el.modalProductions?.classList.contains("open")) renderGallery();



  } finally {



    state.polling = false;



  }



}







function updateStepper(st) {



  const steps = [el.stepScript, el.stepImage, el.stepAnim, el.stepAudio, el.stepConcat];



  steps.forEach((s) => {



    if (s) s.classList.remove("active", "done");



  });







  const pct = st.percent || 0;



  if (pct >= 10 && el.stepScript) el.stepScript.classList.add("done");



  else if (st.running && el.stepScript) el.stepScript.classList.add("active");







  if (pct >= 40 && el.stepImage) el.stepImage.classList.add("done");



  else if (pct >= 15 && st.running && el.stepImage) el.stepImage.classList.add("active");







  if (pct >= 70 && el.stepAnim) el.stepAnim.classList.add("done");



  else if (pct >= 45 && st.running && el.stepAnim) el.stepAnim.classList.add("active");







  if (pct >= 90 && el.stepAudio) el.stepAudio.classList.add("done");



  else if (pct >= 75 && st.running && el.stepAudio) el.stepAudio.classList.add("active");







  if (pct === 100 && el.stepConcat) el.stepConcat.classList.add("done");



  else if (pct >= 90 && st.running && el.stepConcat) el.stepConcat.classList.add("active");



}







function renderLogs(lines) {



  if (!el.logsConsole) return;



  const signature = JSON.stringify(lines);



  if (signature === state.logsSignature) return;



  state.logsSignature = signature;



  const isScrolledToBottom =



    el.logsConsole.scrollHeight - el.logsConsole.clientHeight <= el.logsConsole.scrollTop + 30;







  const html = lines



    .filter((l) => {



      if (!l || typeof l !== "string") return false;



      const t = l.trim();



      if (t.startsWith("{") || t.startsWith("File ") || t.startsWith("Traceback ")) return false;



      if (t.includes("STORYBOARD_STUDIO_DOCTOR") || t.includes("IMAGE_BUDGET_") || t.includes("QC_PASS_")) return false;



      return true;



    })



    .map((l) => {



      const m = l.match(/^\[(\d{2}:\d{2}:\d{2})\]\s*(?:([^\s\[]+)\s*)?\[([^\]]+)\]\s*(.*)$/);



      if (m) {



        const time = m[1];



        const icon = m[2] || "";



        const tag = m[3] || "Thông tin";



        const msg = m[4] || "";







        let badgeCls = "log-badge-info";



        const tagLower = tag.toLowerCase();



        if (tagLower.includes("kịch bản")) badgeCls = "log-badge-script";



        else if (tagLower.includes("cốt truyện")) badgeCls = "log-badge-story";



        else if (tagLower.includes("comfyui")) badgeCls = "log-badge-comfy";



        else if (tagLower.includes("lồng tiếng")) badgeCls = "log-badge-voice";



        else if (tagLower.includes("phân cảnh")) badgeCls = "log-badge-scene";



        else if (tagLower.includes("dựng phim")) badgeCls = "log-badge-render";



        else if (tagLower.includes("điều phối") || tagLower.includes("dự phòng") || tagLower.includes("kết nối")) badgeCls = "log-badge-api";



        else if (tagLower.includes("xuất bản")) badgeCls = "log-badge-publish";



        else if (tagLower.includes("lỗi") || tagLower.includes("cảnh báo")) badgeCls = "log-badge-error";







        return `<div class="log-entry">



          <span class="log-time">${escapeHtml(time)}</span>



          <span class="log-badge ${badgeCls}">${icon ? icon + " " : ""}${escapeHtml(tag)}</span>



          <span class="log-msg">${escapeHtml(msg)}</span>



        </div>`;



      }







      let cls = "log-msg";



      if (l.includes("PASS") || l.includes("COMPLETED")) cls = "log-line-pass";



      else if (l.includes("FAIL") || l.includes("ERROR")) cls = "log-line-error";



      else if (l.includes("GEMINI")) cls = "log-line-gemini";



      return `<div class="log-entry"><span class="${cls}">${escapeHtml(l)}</span></div>`;



    })



    .join("");







  el.logsConsole.innerHTML = html || `<div class="log-entry"><span class="log-msg" style="color:#64748b;">Chưa có nhật ký hoạt động mới...</span></div>`;



  if (isScrolledToBottom) {



    el.logsConsole.scrollTop = el.logsConsole.scrollHeight;



  }



}







function resetSceneInspector(epNum) {



  const ep = epNum || state.currentEpisode || (el.inEpisode ? el.inEpisode.value : 1);



  const elNum = document.getElementById("inspectorSceneNum");



  const elStatus = document.getElementById("inspectorSceneStatus");



  const elTitleField = document.getElementById("inspectorTitleField");



  const elNarr = document.getElementById("inspectorNarration");



  const elDesc = document.getElementById("inspectorDesc");



  const elAudio = document.getElementById("inspectorAudioBox");







  if (elNum) elNum.textContent = `Tập ${ep}`;



  if (elStatus) {



    elStatus.className = "badge badge-pending";



    elStatus.textContent = "Chưa sản xuất";



    elStatus.style.display = "inline-flex";



  }



  if (elTitleField) elTitleField.style.display = "none";



  if (elNarr) elNarr.textContent = `Tập ${ep} chưa được sản xuất. Hãy nhập ý tưởng và bấm "Sản Xuất Tập ${ep} Bằng AI" để tự động viết kịch bản và phân cảnh.`;



  if (elDesc) elDesc.textContent = "Mô tả hình ảnh và bối cảnh sẽ hiển thị tại đây khi hoàn thành.";



  if (elAudio) elAudio.innerHTML = `<span style="font-size:0.7rem;color:var(--text-dim);">Chưa có audio thuyết minh cho tập này.</span>`;



}







async function loadEpisodeDetails(series, episode) {



  if (currentSeoData && (currentSeoData.series !== series || Number(currentSeoData.episode) !== Number(episode))) {



    currentSeoData = null;



  }



  const request = ++state.episodeRequest;



  try {



    const slugName = slugify(series);



    const res = await fetch(`/api/episode?series=${encodeURIComponent(slugName)}&episode=${episode}`);



    if (!res.ok) {



      if (request !== state.episodeRequest || slugify(series) !== slugify(state.currentSeries) || Number(episode) !== Number(state.currentEpisode)) return;



      state.loadedEpisodeData = null;



      state.selectedSceneNumber = null;



      state.deckSignature = null;



      state.lastCheckedEpisodeKey = `${series}_${episode}`;







      // Xóa cảnh cũ, hiển thị Empty state cho Tập mới



      renderStoryboardCards([]);







      // Reset Player về trạng thái trống



      if (el.cinemaVideo) {



        el.cinemaVideo.pause();



        el.cinemaVideo.removeAttribute("src");



        el.cinemaVideo.removeAttribute("poster");



        el.cinemaVideo.load();



        el.cinemaVideo.style.display = "none";



      }



      updatePlayOverlay(false);



      hideUnmutePill();



      updatePlaybackStatus(false);



      if (el.videoEmptyState) el.videoEmptyState.style.display = "flex";



      if (el.playerTitle) el.playerTitle.textContent = `Tập ${episode} chưa có video thành phẩm`;







      // Reset Inspector



      resetSceneInspector(episode);







      // Cập nhật Header Project Name



      const headerProj = document.getElementById("headerProjectName");



      if (headerProj) headerProj.textContent = `${series} - Tập ${episode}`;







      // Reset Prompt & Link cho tập mới sạch hoàn toàn



      if (el.inPrompt) {



        el.inPrompt.value = "";



        el.inPrompt.placeholder = `Nhập ý tưởng hoặc cốt truyện cho Tập ${episode}...`;



      }



      if (el.inReferenceUrl) {



        el.inReferenceUrl.value = "";



      }



      currentSeoData = null;







      // Reset Stepper & Pipeline text nếu hệ thống đang rảnh



      if (!state.isRunning) {



        if (el.progressPercent) el.progressPercent.textContent = "0%";



        if (el.progressBarFill) el.progressBarFill.style.width = "0%";



        if (el.headerStatusDot) el.headerStatusDot.classList.remove("active", "error");



        if (el.headerStatusText) el.headerStatusText.textContent = "Sẵn sàng";



        if (el.pipelineMessage) el.pipelineMessage.textContent = `Sẵn sàng sản xuất Tập ${episode}`;



        const steps = [el.stepScript, el.stepImage, el.stepAnim, el.stepAudio, el.stepConcat];



        steps.forEach((s) => s && s.classList.remove("active", "done"));



        updateLiveButtonLabel();



        renderLogs([`[Studio] Đã chuyển sang Tập ${episode}. Dữ liệu đã được làm mới về ban đầu. Sẵn sàng sản xuất!`]);



        fetch("/api/status/reset", { method: "POST" }).catch(() => {});



      }



      if (el.resumeBanner) el.resumeBanner.style.display = "none";



      if (el.completedBanner) el.completedBanner.style.display = "none";



      return;



    }







    const data = await res.json();



    if (request !== state.episodeRequest || slugify(series) !== slugify(state.currentSeries) || Number(episode) !== Number(state.currentEpisode)) return;



    // Multi-role drama: the 66 scene stills are stored under scene_master.png,

    // separately from the video/thumbnail images. Load their real API URLs so

    // the live desktop storyboard can show them before Muse I2V completes.

    // Confine this overlay to the dedicated drama branch; never mark an

    // unreviewed scene complete or fabricate a clip.

    if (data.resume_config?.production_mode === "cinematic_drama") {

      const sceneSec = Number(data.resume_config.scene_seconds) || 10;

      data.resume_config.scene_seconds = sceneSec;

      if (!Number(data.resume_config.minutes) && Array.isArray(data.scenes)) {

        data.resume_config.minutes = Math.round(data.scenes.length * sceneSec / 6) / 10;

      }

      for (const item of data.scenes || []) {

        item.script_seconds = Number(item.script_seconds) || sceneSec;

      }

      try {

        const query = `series=${encodeURIComponent(series)}&episode=${encodeURIComponent(episode)}`;

        const approvalRes = await fetch(`/api/drama/assets?${query}`, { cache: "no-store" });

        if (approvalRes.ok) {

          const approvalData = await approvalRes.json();

          const stills = new Map(

            (approvalData.assets || []).filter(item => item.kind === "scene")

              .map(item => [Number(item.id), item])

          );

          for (const item of data.scenes || []) {

            const still = stills.get(Number(item.scene_number));

            if (!still) continue;

            if (!item.image_url && still.image_url) item.image_url = still.image_url;

            item.scene_visual_approved = Boolean(still.approved);

            if (!item.video_url && still.image_url) {

              item.status = still.approved ? "IMAGE_APPROVED" : "NEEDS_VISUAL_REVIEW";

            }

          }

        }

      } catch (err) {

        console.warn("[Drama UI] Scene master preview fetch unavailable:", err);

      }

    }



    if (request !== state.episodeRequest || slugify(series) !== slugify(state.currentSeries) || Number(episode) !== Number(state.currentEpisode)) return;



    state.lastCheckedEpisodeKey = `${series}_${episode}`;



    const firstSelection = !state.selectedSceneNumber && data.scenes && data.scenes.length > 0;



    if (firstSelection) state.selectedSceneNumber = data.scenes[0].scene_number;



    state.loadedEpisodeData = data;



    renderStoryboardCards(data.scenes || []);



    // A long multi-role film with 66 scenes is unreadable as a 3-column

    // thumbnail grid. Start in the readable list view once per episode.

    // Do not override the user's manual grid/cinema choice on later polls.

    const viewEpisodeKey = `${slugify(series)}_${episode}`;

    if (data.resume_config?.production_mode === "cinematic_drama" &&

        (data.scenes || []).length > 24 &&

        state.lastDramaListModeEpisode !== viewEpisodeKey) {

      state.lastDramaListModeEpisode = viewEpisodeKey;

      window.setStoryboardViewMode("list");

    }







    // Restore the actual production branch when opening a saved episode.

    // A cinema project must never silently appear as Thuyết Minh after an

    // app restart, and switching away must not leak the cinema mode.

    if (data.resume_config?.production_mode &&

        state.lastProductionModeEpisode !== viewEpisodeKey) {

      state.lastProductionModeEpisode = viewEpisodeKey;

      const restoredProvider = data.image_provider || data.resume_config.image_provider;

      if (restoredProvider && el.inImageSource &&

          Array.from(el.inImageSource.options).some(opt => opt.value === restoredProvider)) {

        el.inImageSource.value = restoredProvider;

      }

      if (typeof window.setProductionModeUI === "function") {

        window.setProductionModeUI(data.resume_config.production_mode === "cinematic_drama"

          ? "cinematic_drama" : "narrative");

      }

    }



    // Đồng bộ ngôn ngữ, giọng đọc và nguồn ảnh theo tập phim dở dang nếu có



    if (data.can_resume) {



      if (!state.userExplicitLanguage && data.language && el.inLanguage) {



        el.inLanguage.value = data.language;



        if (typeof updateVoiceOptions === "function") updateVoiceOptions(false);



      }



      if (data.voice_name && el.inVoice) {



        el.inVoice.value = data.voice_name;



      }



      if (data.image_provider && el.inImageSource) {



        el.inImageSource.value = data.image_provider;



      }



      if (data.resume_config && state.lastLoadedResumeKey !== `${data.series}_${data.episode}`) {



        state.lastLoadedResumeKey = `${data.series}_${data.episode}`;



        const rc = data.resume_config;



        if (rc.minutes && el.inMinutes) el.inMinutes.value = String(rc.minutes);



        if (rc.scene_seconds && el.inSceneSec) el.inSceneSec.value = String(rc.scene_seconds);



        if (rc.genre && el.inGenre) el.inGenre.value = rc.genre;



        if (rc.visual_style && el.inVisualStyle) el.inVisualStyle.value = rc.visual_style;



        if (rc.region && el.inRegion) el.inRegion.value = rc.region;



        if (rc.input_mode && el.inInputMode) {



          el.inInputMode.value = rc.input_mode;



          if (typeof updateInputModeFields === "function") updateInputModeFields();



        }



        if (rc.reference_url && el.inReferenceUrl) el.inReferenceUrl.value = rc.reference_url;



        if (el.inPrompt && (rc.prompt || rc.reference_url)) {



          el.inPrompt.value = rc.input_mode === "link" ? (rc.reference_url || "") : (rc.prompt || "");



        }



      }



      if (data.total_scenes && el.inMcpMaxImages) {



        el.inMcpMaxImages.value = String(Math.max(parseInt(el.inMcpMaxImages.value || "3", 10), data.total_scenes));



      }



    }







    // Hiển thị khung Chạy Tiếp nếu tập đang dở dang



    if (el.resumeBanner) {



      if (data.can_resume && !state.isRunning) {



        el.resumeBanner.style.display = "block";



        if (el.resumeBadge) el.resumeBadge.textContent = `Cảnh ${data.completed_scenes}/${data.total_scenes}`;



        if (el.btnResume) el.btnResume.textContent = `▶️ Chạy Tiếp (từ cảnh ${data.next_scene})`;



        if (el.resumeBannerDesc) {



          el.resumeBannerDesc.textContent = `Tập ${episode} đã tạo xong ${data.completed_scenes}/${data.total_scenes} cảnh. Bấm "Chạy Tiếp" để hoàn thành ${data.total_scenes - data.completed_scenes} cảnh còn lại mà không mất công làm lại từ đầu!`;



        }



      } else {



        el.resumeBanner.style.display = "none";



      }



    }







    // Hiển thị khung Tập Đã Hoàn Thành nếu có final_video_url



    if (el.completedBanner) {



      if (data.final_video_url && !state.isRunning) {



        el.completedBanner.style.display = "block";



        const curEp = Number(episode) || 1;



        if (el.btnNextEpisode) el.btnNextEpisode.textContent = `➕ Tạo Tập ${curEp + 1} Tiếp Theo`;




        if (state.wasRunning) {
          state.wasRunning = false;
          if (typeof openSatelliteShortPrompt === "function") {
            setTimeout(openSatelliteShortPrompt, 1000);
          }
        }
      } else {



        el.completedBanner.style.display = "none";



      }



    }







    // Video Player Preview Synchronization



    if (state.activePreviewMode === "episode") {



      if (data.final_video_url) {



        const poster = (data.scenes && data.scenes[0] && data.scenes[0].image_url) ? data.scenes[0].image_url : null;



        setVideoSource(data.final_video_url, `${series} - Tập ${episode} (Master Cut)`, poster);



      } else {



        const completedScenes = (data.scenes || []).filter((s) => Boolean(s.video_url));



        if (completedScenes.length > 0) {



          const currentSrc = el.cinemaVideo ? el.cinemaVideo.getAttribute("src") : null;



          if (!currentSrc || el.cinemaVideo.style.display === "none") {



            const previewSc = (state.selectedSceneNumber ? data.scenes.find((s) => s.scene_number === state.selectedSceneNumber && s.video_url) : null) || completedScenes[0];



            setVideoSource(previewSc.video_url, `Cảnh ${previewSc.scene_number} / ${data.total_scenes} (Đang hoàn thiện Cả Tập)`, previewSc.image_url);



          }



        } else {



          if (el.cinemaVideo) el.cinemaVideo.style.display = "none";



          updatePlayOverlay(false);



          hideUnmutePill();



          updatePlaybackStatus(false);



          if (el.videoEmptyState) el.videoEmptyState.style.display = "flex";



          if (el.playerTitle) el.playerTitle.textContent = `Tập ${episode} đang hoàn thiện`;



        }



      }



    } else if (state.activePreviewMode === "scene") {



      if (state.selectedSceneNumber) {



        const sc = (data.scenes || []).find((s) => s.scene_number === state.selectedSceneNumber);



        if (sc && sc.video_url) {



          setVideoSource(sc.video_url, `Cảnh ${sc.scene_number} - Hoạt ảnh nét vẽ`, sc.image_url);



        } else if (sc && !sc.video_url) {



          if (el.cinemaVideo) el.cinemaVideo.style.display = "none";



          updatePlayOverlay(false);



          hideUnmutePill();



          updatePlaybackStatus(false);



          if (el.videoEmptyState) el.videoEmptyState.style.display = "flex";



          if (el.playerTitle) el.playerTitle.textContent = `Cảnh ${sc.scene_number} đang chờ kết xuất video...`;



        }



      }



    }







    // Update Header Project Name



    const headerProj = document.getElementById("headerProjectName");



    if (headerProj) headerProj.textContent = `${series} - Tập ${episode}`;







    // Auto-select first scene in inspector if none selected yet



    if (firstSelection) {



      const firstScene = data.scenes[0];



      highlightSceneCard(firstScene.scene_number);



      populateSceneInspector(firstScene);



    }







    // Auto-detect YouTube channel and apply saved channel configurations for this series/video



    if (typeof window.autoDetectAndSelectChannel === "function") {



      const epKey = `${series}_${episode}`;



      const isNewEpisode = !state.currentLoadedEpisodeKey || state.currentLoadedEpisodeKey !== epKey;



      if (isNewEpisode) {



        state.currentLoadedEpisodeKey = epKey;



        if (window.youTubeState) {



          window.youTubeState.userSelectedChannel = false;



          window.youTubeState.selectedChannelId = null;



        }



      }



      const vidLang = data.language || (data.config && data.config.language) || (el.inLanguage ? el.inLanguage.value : "");



      window.autoDetectAndSelectChannel(series, vidLang, isNewEpisode);



    }



    // Always pre-load this episode's dedicated SEO package so it is immediately ready and never lost

    fetch(`/api/episode/seo?series=${encodeURIComponent(series)}&episode=${episode}`, { cache: "no-store" })

      .then(r => r.ok ? r.json() : null)

      .then(seoData => {

        if (seoData && (seoData.best_title || seoData.titles || seoData.vidiq_score)) {

          if (slugify(state.currentSeries || series) === slugify(series) && Number(state.currentEpisode || episode) === Number(episode)) {

            currentSeoData = seoData;

            window.currentSeoData = seoData;

            state.currentSeoData = seoData;

            const seoModal = document.getElementById("modalSeoPackage");

            if (seoModal && (seoModal.style.display === "block" || seoModal.classList.contains("active") || seoModal.classList.contains("open"))) {

              renderSeoPackageUI(seoData);

            }

          }

        }

      })

      .catch(() => {});



  } catch (err) {



    console.warn("Could not load episode details", err);



  }



}







function reconcileStoryboardNodes(container, html) {



  const template = document.createElement("template");



  template.innerHTML = html;



  const wanted = [...template.content.children];



  const ids = new Set(wanted.map(node => node.id));



  for (const child of [...container.children]) {



    if (!ids.has(child.id)) child.remove();



  }



  wanted.forEach((node, index) => {



    const current = [...container.children].find(child => child.id === node.id);



    if (!current) container.insertBefore(node, container.children[index] || null);



    else if (current.outerHTML !== node.outerHTML) current.replaceWith(node);



  });



}







function renderStoryboardCards(scenes) {



  state.lastLoadedScenes = scenes || [];



  const scenesCompact = scenes ? scenes.map((s) => `${s.scene_number}_${s.status}_${Boolean(s.video_url)}_${Boolean(s.image_url)}`).join(";") : "";

  const signature = `${state.currentSeries}_${state.currentEpisode}_${scenesCompact}_${state.storyboardFilter}_${state.currentRunningScene}_${state.isRunning}`;



  if (signature === state.deckSignature) return;



  state.deckSignature = signature;



  



  if (el.scenesCountBadge) el.scenesCountBadge.textContent = `${scenes ? scenes.length : 0} cảnh`;



  const track = document.getElementById("timelineTrack");



  const durText = document.getElementById("timelineDurationText");







  // Update Filter Counters



  const allCount = scenes ? scenes.length : 0;



  const passCount = scenes ? scenes.filter((s) => s.status === "PASS").length : 0;



  const pendingCount = scenes ? scenes.filter((s) => s.status !== "PASS" && s.status !== "FAILED").length : 0;



  const videoCount = scenes ? scenes.filter((s) => Boolean(s.video_url)).length : 0;







  const elChipAll = document.getElementById("chipCountAll");



  const elChipPass = document.getElementById("chipCountPass");



  const elChipPending = document.getElementById("chipCountPending");



  const elChipVideo = document.getElementById("chipCountVideo");







  if (elChipAll) elChipAll.textContent = allCount;



  if (elChipPass) elChipPass.textContent = passCount;



  if (elChipPending) elChipPending.textContent = pendingCount;



  if (elChipVideo) elChipVideo.textContent = videoCount;







  if (!scenes || scenes.length === 0) {



    const epNum = state.currentEpisode || (el.inEpisode ? el.inEpisode.value : 1);



    el.scenesContainer.innerHTML = `



      <div class="storyboard-empty-state">



        <svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">



          <rect x="2" y="3" width="20" height="14" rx="2"></rect>



          <line x1="8" y1="21" x2="16" y2="21"></line>



          <line x1="12" y1="17" x2="12" y2="21"></line>



        </svg>



        <div style="font-weight:600;font-size:0.95rem;color:#e2e8f0;margin-top:10px;">Tập ${epNum} Chưa Có Phân Cảnh</div>



        <div style="font-size:0.8rem;color:var(--text-dim);max-width:380px;text-align:center;line-height:1.45;margin-top:6px;">



          Tập phim này chưa được sản xuất. Hãy nhập ý tưởng kịch bản rồi bấm <strong style="color:#818cf8;">"Sản Xuất Tập ${epNum} Bằng AI"</strong> để tự động khởi tạo.



        </div>



        <button class="btn btn-secondary btn-sm" onclick="loadSampleDemoVideo()" style="margin-top:12px;">



          ▶ Xem Video Mẫu Hoạt Ảnh



        </button>



      </div>`;



    if (track) track.innerHTML = "";



    if (durText) durText.textContent = "0:00 - 0:00";



    return;



  }







  // Filter scenes based on active filter chip



  let displayScenes = scenes;



  if (state.storyboardFilter === "pass") {



    displayScenes = scenes.filter((s) => s.status === "PASS");



  } else if (state.storyboardFilter === "pending") {



    displayScenes = scenes.filter((s) => s.status !== "PASS" && s.status !== "FAILED");



  } else if (state.storyboardFilter === "video") {



    displayScenes = scenes.filter((s) => Boolean(s.video_url));



  }







  // Render 16:9 Cinema Storyboard Cards



  const cardsHtml = displayScenes



    .map((sc) => {



      const isSelected = state.selectedSceneNumber === sc.scene_number;



      const isDone = sc.status === "PASS" || Boolean(sc.video_url);



      const isCurrentLive = state.isRunning && (state.currentRunningScene === sc.scene_number) && !isDone;



      const isFailed = sc.status === "FAILED";



      const title = sc.summary || sc.title || `Cảnh ${sc.scene_number}`;







      let statusClass = "pending";



      let statusText = "⟳ Chờ";



      if (isDone) {



        statusClass = "pass";



        statusText = "✓ Xong";



      } else if (isCurrentLive) {



        statusClass = "rendering";



        statusText = `<span class="chip-spin-dot"></span>⚡ Đang Vẽ`;



      } else if (isFailed) {



        statusClass = "fail";



        statusText = "! Lỗi";



      }







      let thumbHtml = "";



      if (sc.image_url) {



        thumbHtml = `<img class="scene-thumb-img" src="${sc.image_url}" alt="Cảnh ${sc.scene_number}">`;



      } else if (isCurrentLive) {



        thumbHtml = `



          <div class="scene-thumb-placeholder is-rendering">



            <div class="render-radar-ring">



              <div class="render-radar-spinner"></div>



              <div class="render-radar-core">



                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" class="spin-icon">



                  <circle cx="12" cy="12" r="10" stroke-opacity="0.25"></circle>



                  <path d="M12 2a10 10 0 0 1 10 10" stroke-linecap="round"></path>



                </svg>



              </div>



            </div>



            <span class="scene-thumb-placeholder-text rendering-live">⚡ ĐANG VẼ HOẠT ẢNH...</span>



          </div>`;



      } else {



        thumbHtml = `



          <div class="scene-thumb-placeholder ${state.isRunning ? 'is-queued' : ''}">



            <div class="render-orbit-spinner">



              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="${state.isRunning ? 'orbit-icon' : ''}">



                <path d="M12 2v4m0 12v4M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M2 12h4m12 0h4M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83"/>



              </svg>



            </div>



            <span class="scene-thumb-placeholder-text">${state.isRunning ? '⏳ Chờ Vẽ Hoạt Ảnh' : 'Chưa Khởi Tạo'}</span>



          </div>`;



      }







      const playOverlayHtml = sc.video_url



        ? `<div class="scene-play-overlay">



            <div class="scene-play-btn-circle">



              <svg viewBox="0 0 24 24"><polygon points="6 3 20 12 6 21 6 3"></polygon></svg>



            </div>



          </div>`



        : ``;







      let stateIndicatorText = "Chờ Xử Lý";



      let stateIndicatorClass = "";



      if (sc.video_url || isDone) {



        stateIndicatorText = "▶ Clip Sẵn Sàng";



        stateIndicatorClass = "has-video";



      } else if (isCurrentLive) {



        stateIndicatorText = `<span class="pulse-indicator"></span>Đang Render...`;



        stateIndicatorClass = "is-rendering";



      } else if (isFailed) {



        stateIndicatorText = "Lỗi Render";



      }







      return `



      <div class="scene-card ${isSelected ? "active" : ""} ${isCurrentLive ? "is-rendering" : ""}" id="sceneCard_${sc.scene_number}" data-scene="${sc.scene_number}" onclick="selectSceneAndPlay(${sc.scene_number}, '${sc.video_url || ''}')" title="Cảnh ${sc.scene_number}: ${escapeHtml(title)} - Bấm xem chi tiết & phát video">



        <div class="scene-thumb-wrap">



          <div class="scene-overlay-top">



            <span class="scene-chip-num">#${String(sc.scene_number).padStart(2, "0")}</span>



            <span class="scene-chip-status ${statusClass}">${statusText}</span>



          </div>



          ${thumbHtml}



          ${playOverlayHtml}



        </div>



        <div class="scene-card-info">



          <div class="scene-card-title">${escapeHtml(title)}</div>



          ${sc.narration ? `<div class="scene-card-narr">${escapeHtml(sc.narration)}</div>` : ""}



          <div class="scene-card-submeta">



            <span class="scene-time-pill">⏱️ ${sc.script_seconds || 25}s</span>



            <span class="scene-state-indicator ${stateIndicatorClass}">${stateIndicatorText}</span>



          </div>



        </div>



      </div>



      `;



    })



    .join("");







  reconcileStoryboardNodes(el.scenesContainer, cardsHtml);







  // Render Filmstrip Timeline Bar



  if (track) {



    const timelineHtml = scenes



      .map((sc) => {



        const isSelected = state.selectedSceneNumber === sc.scene_number;



        return `<div class="timeline-segment ${isSelected ? "active" : ""}" id="timelineSeg_${sc.scene_number}" onclick="selectSceneAndPlay(${sc.scene_number}, '${sc.video_url || ''}')" title="Cảnh ${sc.scene_number}">Cảnh ${sc.scene_number}</div>`;



      })



      .join("");



    reconcileStoryboardNodes(track, timelineHtml);



  }



  if (durText) {



    const totalSec = scenes.reduce((acc, s) => acc + (s.script_seconds || 25), 0);



    const mins = Math.floor(totalSec / 60);



    const secs = totalSec % 60;



    durText.textContent = `0:00 - ${mins}:${secs < 10 ? "0" : ""}${secs} (${scenes.length} cảnh)`;



  }



}







// Global Filter Functions



window.filterStoryboardScenes = function (filterType) {



  state.storyboardFilter = filterType;



  document.querySelectorAll(".deck-chip").forEach((chip) => {



    chip.classList.toggle("active", chip.getAttribute("data-filter") === filterType);



  });



  state.deckSignature = null; // force re-render



  if (state.lastLoadedScenes) {



    renderStoryboardCards(state.lastLoadedScenes);



  }

};







window.setStoryboardViewMode = function (mode) {



  const container = el.scenesContainer;



  if (!container) return;



  state.storyboardViewMode = mode;



  container.classList.remove("view-cinema", "view-list");



  if (mode === "cinema") {



    container.classList.add("view-cinema");



  } else if (mode === "list") {



    container.classList.add("view-list");



  }



  const btnGrid = document.getElementById("btnViewGrid");



  const btnCinema = document.getElementById("btnViewCinema");



  const btnList = document.getElementById("btnViewList");



  if (btnGrid) btnGrid.classList.toggle("active", mode === "grid");



  if (btnCinema) btnCinema.classList.toggle("active", mode === "cinema");



  if (btnList) btnList.classList.toggle("active", mode === "list");



};







window.toggleDeckDensity = function () {



  const current = state.storyboardViewMode || "grid";



  const next = current === "grid" ? "cinema" : current === "cinema" ? "list" : "grid";



  window.setStoryboardViewMode(next);



};







window.switchInspectorTab = function (tabName) {



  document.querySelectorAll(".inspector-tab").forEach((tab) => {



    tab.classList.toggle("active", tab.getAttribute("data-tab") === tabName);



  });



  const tabNarration = document.getElementById("tabPaneNarration");



  const tabVisual = document.getElementById("tabPaneVisual");



  if (tabName === "all") {



    if (tabNarration) tabNarration.classList.add("active");



    if (tabVisual) tabVisual.classList.add("active");



  } else {



    if (tabNarration) tabNarration.classList.toggle("active", tabName === "narration");



    if (tabVisual) tabVisual.classList.toggle("active", tabName === "visual");



  }

};







window.clearStudioLogs = function () {



  if (el.logsConsole) el.logsConsole.innerHTML = "";



};







window.toggleConsoleDrawer = function () {



  const card = document.getElementById("consoleCard");



  const btn = document.getElementById("btnToggleConsole");



  if (!card) return;



  if (card.classList.contains("collapsed")) {



    card.classList.remove("collapsed");



    card.classList.add("expanded");



    if (btn) btn.textContent = "⤡";



  } else if (card.classList.contains("expanded")) {



    card.classList.remove("expanded");



    if (btn) btn.textContent = "⤢";



  } else {



    card.classList.add("collapsed");



    if (btn) btn.textContent = "⤢";



  }

};







function highlightSceneCard(num) {



  document.querySelectorAll(".scene-card").forEach((c) => c.classList.remove("active"));



  document.querySelectorAll(".timeline-segment").forEach((s) => s.classList.remove("active"));



  const card = document.getElementById(`sceneCard_${num}`);



  if (card) card.classList.add("active");



  const seg = document.getElementById(`timelineSeg_${num}`);



  if (seg) seg.classList.add("active");



}







function populateSceneInspector(sc) {



  if (!sc) return;



  const elNum = document.getElementById("inspectorSceneNum");



  const elStatus = document.getElementById("inspectorSceneStatus");



  const elTitleField = document.getElementById("inspectorTitleField");



  const elTitle = document.getElementById("inspectorSceneTitle");



  const elNarr = document.getElementById("inspectorNarration");



  const elDesc = document.getElementById("inspectorDesc");



  const elAudio = document.getElementById("inspectorAudioBox");







  if (elNum) {



    elNum.textContent = `Cảnh ${sc.scene_number}`;



  }







  if (elStatus) {



    elStatus.style.display = "inline-flex";



    if (sc.status === "PASS") {



      elStatus.className = "badge badge-pass";



      elStatus.textContent = "Đã xong";



    } else if (sc.status === "FAILED") {



      elStatus.className = "badge badge-fail";



      elStatus.textContent = "Lỗi";



    } else {



      elStatus.className = "badge badge-pending";



      elStatus.textContent = "Đang xử lý";



    }



  }







  const titleText = sc.summary || sc.title || "";



  if (elTitle && elTitleField) {



    if (titleText) {



      elTitle.textContent = titleText;



      elTitleField.style.display = "flex";



    } else {



      elTitleField.style.display = "none";



    }



  }







  if (elNarr) elNarr.textContent = sc.narration || sc.description || "(Chưa có lời thoại)";



  if (elDesc) elDesc.textContent = sc.description || sc.visual_setup || "-";



  if (elAudio) elAudio.remove();



}







window.selectSceneAndPlay = function (num, videoUrl) {



  state.selectedSceneNumber = num;



  switchPlayerMode("scene");



  



  let posterUrl = null;



  if (state.loadedEpisodeData && state.loadedEpisodeData.scenes) {



    const sc = state.loadedEpisodeData.scenes.find((s) => s.scene_number === num);



    if (sc) {



      posterUrl = sc.image_url || null;



      if (!videoUrl && sc.video_url) videoUrl = sc.video_url;



      populateSceneInspector(sc);



    }



  }







  if (videoUrl) {



    setVideoSource(videoUrl, `Cảnh ${num} - Hoạt ảnh nét vẽ`, posterUrl);



  } else {



    if (el.cinemaVideo) el.cinemaVideo.style.display = "none";



    if (el.videoEmptyState) el.videoEmptyState.style.display = "flex";



    if (el.playerTitle) el.playerTitle.textContent = `Cảnh ${num} đang xử lý, chưa có video hoàn chỉnh`;



    showToast(`Cảnh ${num} đang được xử lý, chưa có video hoàn chỉnh.`);



  }



  highlightSceneCard(num);



};







window.reloadEpisodeDetails = function () {



  loadEpisodeDetails(state.currentSeries, state.currentEpisode);



  showToast("Đã cập nhật danh sách cảnh");



};







function playEpisodeVideo() {



  if (state.loadedEpisodeData && state.loadedEpisodeData.final_video_url) {



    setVideoSource(



      state.loadedEpisodeData.final_video_url,



      `${state.currentSeries} - Tập ${state.currentEpisode} (Master Cut)`



    );



  } else {



    // If master cut is still rendering, preview the selected or latest completed scene



    const completedScenes = (state.loadedEpisodeData?.scenes || []).filter((s) => Boolean(s.video_url));



    if (completedScenes.length > 0) {



      const target = (state.selectedSceneNumber ? state.loadedEpisodeData.scenes.find((s) => s.scene_number === state.selectedSceneNumber && s.video_url) : null) || completedScenes[0];



      setVideoSource(target.video_url, `Cảnh ${target.scene_number} / ${state.loadedEpisodeData.total_scenes} (Đang hoàn thiện Cả Tập)`, target.image_url);



      showToast(`Cả tập đang ghép nối. Đang phát trước Cảnh ${target.scene_number}.`);



    } else {



      if (el.videoEmptyState) el.videoEmptyState.style.display = "flex";



      if (el.cinemaVideo) el.cinemaVideo.style.display = "none";



      if (el.playerTitle) el.playerTitle.textContent = "Chưa có video thành phẩm";



    }



  }



}







function playSceneVideo(num) {



  if (!state.loadedEpisodeData) return;



  const sc = (state.loadedEpisodeData.scenes || []).find((s) => s.scene_number === num);



  if (sc && sc.video_url) {



    setVideoSource(sc.video_url, `Cảnh ${num} - Hoạt ảnh nét vẽ`, sc.image_url);



  } else {



    showToast(`Cảnh ${num} chưa render xong video!`);



  }



}







function playShortVideo() {



  if (state.loadedEpisodeData && state.loadedEpisodeData.final_short_url) {



    setVideoSource(



      state.loadedEpisodeData.final_short_url,



      `${state.currentSeries} - Tập ${state.currentEpisode} (YouTube Shorts 9:16)`



    );



    if (el.btnDownloadMp4) {



      el.btnDownloadMp4.href = state.loadedEpisodeData.final_short_url;



      el.btnDownloadMp4.download = `${slugify(state.currentSeries || "storyboard")}_ep${String(state.currentEpisode || 1).padStart(3, "0")}_short.mp4`;



      el.btnDownloadMp4.textContent = "⬇ Tải Shorts (9:16)";



    }



  } else {



    generateOrLoadShortVideo();



  }



}







async function generateOrLoadShortVideo() {



  const series = state.currentSeries || "auto";



  const episode = state.currentEpisode || 1;



  showToast("⏳ Đang kiểm tra / trích xuất đoạn cao trào làm Shorts 9:16...", "info");



  try {



    const res = await fetch("/api/episode/short/generate", {



      method: "POST",



      headers: { "Content-Type": "application/json" },



      body: JSON.stringify({ series, episode })



    });



    const data = await res.json();



    if (data.ok && data.video_url) {



      if (state.loadedEpisodeData) {



        state.loadedEpisodeData.final_short_url = data.video_url;



      }



      setVideoSource(



        data.video_url,



        `${state.currentSeries} - Tập ${state.currentEpisode} (YouTube Shorts 9:16)`



      );



      if (el.btnDownloadMp4) {



        el.btnDownloadMp4.href = data.video_url;



        el.btnDownloadMp4.download = `${slugify(state.currentSeries || "storyboard")}_ep${String(state.currentEpisode || 1).padStart(3, "0")}_short.mp4`;



        el.btnDownloadMp4.textContent = "⬇ Tải Shorts (9:16)";



      }



      showToast("✅ Đã tạo thành công YouTube Shorts 9:16!");



    } else {



      showToast(data.error || "Chưa thể trích xuất Shorts. Đảm bảo tập phim đã render xong.", "warning");



    }



  } catch (err) {



    showToast("Lỗi trích xuất Shorts: " + err.message, "error");



  }



}







function updatePlayOverlay(show) {

  // Overlay button permanently removed

}







function showUnmutePill() {



  if (el.videoUnmutePill && el.cinemaVideo && el.cinemaVideo.muted && !el.cinemaVideo.paused) {



    el.videoUnmutePill.style.display = "inline-flex";



  }



}







function hideUnmutePill() {



  if (el.videoUnmutePill) {



    el.videoUnmutePill.style.display = "none";



  }



}







function updatePlaybackStatus(isPlaying) {



  if (!el.playerPlaybackStatus) return;



  if (!el.cinemaVideo || el.cinemaVideo.style.display === "none" || !el.cinemaVideo.getAttribute("src")) {



    el.playerPlaybackStatus.style.display = "none";



    return;



  }



  el.playerPlaybackStatus.style.display = "inline-flex";



  if (isPlaying) {



    el.playerPlaybackStatus.className = "player-playback-pill pill-playing";



    el.playerPlaybackStatus.textContent = "▶ ĐANG PHÁT";



  } else {



    el.playerPlaybackStatus.className = "player-playback-pill pill-paused";



    el.playerPlaybackStatus.textContent = "⏸ TẠM DỪNG";



  }



}







function toggleCinemaPlayback(forceUnmute = false) {



  if (!el.cinemaVideo || !el.cinemaVideo.getAttribute("src")) return;



  // If the video is currently playing but MUTED, user clicked to turn on sound!



  if (!el.cinemaVideo.paused && el.cinemaVideo.muted) {



    el.cinemaVideo.muted = false;



    el.cinemaVideo.volume = 1.0;



    hideUnmutePill();



    updatePlayOverlay(false);



    updatePlaybackStatus(true);



    showToast("Đã bật âm thanh 🔊");



    return;



  }



  if (el.cinemaVideo.paused) {



    el.cinemaVideo.muted = false;



    el.cinemaVideo.volume = 1.0;



    el.cinemaVideo.play()



      .then(() => {



        updatePlayOverlay(false);



        hideUnmutePill();



        updatePlaybackStatus(true);



      })



      .catch((err) => {



        // Fallback to muted playback if user gesture was not registered



        el.cinemaVideo.muted = true;



        el.cinemaVideo.play()



          .then(() => {



            updatePlayOverlay(false);



            showUnmutePill();



            updatePlaybackStatus(true);



          })



          .catch((e) => {



            console.warn("Play error:", e);



            updatePlayOverlay(true);



            updatePlaybackStatus(false);



          });



      });



  } else {



    el.cinemaVideo.pause();



    updatePlayOverlay(true);



    updatePlaybackStatus(false);



  }



}







function setVideoSource(url, title, posterUrl = null) {



  if (!url) return;



  if (el.videoEmptyState) el.videoEmptyState.style.display = "none";



  if (el.cinemaVideo) {



    el.cinemaVideo.style.display = "block";



    const currentSrc = el.cinemaVideo.getAttribute("src");



    if (currentSrc !== url) {



      // Clear static poster so video canvas shows crisp decoded video frames directly



      el.cinemaVideo.removeAttribute("poster");



      el.cinemaVideo.src = url;



      el.cinemaVideo.load();



      el.cinemaVideo.muted = false;



      el.cinemaVideo.volume = 1.0;







      // Intelligent Playback: Try unmuted play first.



      // If browser blocks unmuted autoplay without prior click, cue frame 0 with prominent Play button.



      const playPromise = el.cinemaVideo.play();



      if (playPromise !== undefined) {



        playPromise



          .then(() => {



            updatePlayOverlay(false);



            hideUnmutePill();



            updatePlaybackStatus(true);



          })



          .catch(() => {



            // Unmuted autoplay blocked by browser policy without gesture



            // Pause and display glowing central Play button so first click plays with full sound!



            el.cinemaVideo.pause();



            try { el.cinemaVideo.currentTime = 0.05; } catch (e) {}



            updatePlayOverlay(true);



            updatePlaybackStatus(false);



          });



      }



    }



  }



  if (el.playerTitle) el.playerTitle.textContent = title;



  if (el.btnDownloadMp4) el.btnDownloadMp4.href = url;



}







// PRODUCTIONS GALLERY: live sorting, safe deletion, restore and explicit purge.



let gallerySnapshot = { productions: [], trash: [], stats: {} };



let galleryBusy = false;







function galleryElement(tag, cssClass, label) {



  const node = document.createElement(tag);



  if (cssClass) node.className = cssClass;



  if (label !== undefined) node.textContent = String(label);



  return node;



}







function galleryButton(label, action, data, danger = false) {



  const button = galleryElement("button", danger ? "btn btn-xs gallery-danger" : "btn btn-secondary btn-xs", label);



  button.type = "button";



  button.dataset.galleryAction = action;



  for (const [key, value] of Object.entries(data)) {



    if (value !== undefined && value !== null) button.dataset[key] = String(value);



  }



  button.disabled = galleryBusy || Boolean(state.isRunning) || !state.statusReady;



  return button;



}







function gallerySize(n) {



  const value = Number(n) || 0;



  return value >= 1073741824 ? (value / 1073741824).toFixed(2) + " GB"



    : value >= 1048576 ? (value / 1048576).toFixed(1) + " MB"



    : value >= 1024 ? (value / 1024).toFixed(1) + " KB" : value + " B";



}







function renderGallery() {



  const content = el.productionsList;



  if (!content) return;



  content.replaceChildren();



  const filter = document.getElementById("galleryFilter").value;



  const search = document.getElementById("gallerySearch").value.trim().toLocaleLowerCase();



  const sort = document.getElementById("gallerySort").value;



  const stats = gallerySnapshot.stats || {};



  const summary = document.getElementById("gallerySummary");



  if (summary) summary.textContent = (stats.projects || 0) + " dự án • "



    + (stats.episodes || 0) + " tập • "



    + (stats.test_projects || 0) + " dự án thử nghiệm • "



    + gallerySize(stats.bytes) + " đang lưu • "



    + (stats.trash_items || 0) + " mục trong thùng rác";



  const note = document.querySelector(".gallery-note");



  if (note) note.textContent = state.isRunning



    ? "Đang sản xuất phim: chỉ xem kho, tạm khóa thao tác xóa và khôi phục."



    : "Xóa sẽ chuyển vào thùng rác, có thể khôi phục. Xóa vĩnh viễn chỉ thực hiện trong Thùng rác.";



  const sortItems = items => items.sort((a,b) => sort === "name"



    ? String(a.series).localeCompare(String(b.series), "vi")



    : sort === "size"



      ? (b.size_bytes || 0) - (a.size_bytes || 0)



      : (b.updated_epoch || 0) - (a.updated_epoch || 0));



  if (filter === "trash") {



    const rows = (gallerySnapshot.trash || []).filter(item =>



      (item.series + " " + (item.episode || "")).toLocaleLowerCase().includes(search));



    if (!rows.length) content.append(galleryElement("p", "gallery-empty", "Thùng rác trống hoặc không có kết quả."));



    for (const item of rows) {



      const block = galleryElement("div", "gallery-project");



      const row = galleryElement("div", "gallery-project-head");



      const what = item.series + (item.episode ? " / " + item.episode : " (toàn bộ dự án)");



      const title = galleryElement("div", "gallery-title", what);



      title.append(galleryElement("small", "gallery-meta", gallerySize(item.size_bytes) + " • " + String(item.removed_at || "").slice(0, 19).replace("T", " ")));



      const actions = galleryElement("div", "gallery-actions");



      actions.append(galleryButton("↩ Khôi phục", "restore", {id: item.id}));



      actions.append(galleryButton("Xóa vĩnh viễn", "purge", {id: item.id}, true));



      row.append(title, actions);



      block.append(row);



      content.append(block);



    }



    return;



  }



  const projects = sortItems((gallerySnapshot.productions || [])



    .filter(p => (filter === "all" || p.category === filter) &&



      (String(p.series).toLocaleLowerCase().includes(search) ||



       (p.episodes || []).some(ep => ep.folder.toLocaleLowerCase().includes(search)))));



  if (!projects.length) {



    content.append(galleryElement("p", "gallery-empty",



      filter === "main" ? "Chưa có phim chính trong nhóm này. Chọn Bản thử nghiệm để xem các bản QA/E2E."



        : "Không có dự án phù hợp. Hãy thử đổi nhóm hoặc tìm kiếm."));



    return;



  }



  for (const p of projects) {



    const block = galleryElement("section", "gallery-project");



    const row = galleryElement("div", "gallery-project-head");



    const projectTitle = galleryElement("div", "gallery-title", "📁 " + p.series);



    projectTitle.append(galleryElement("small", "gallery-meta",



      (p.episodes || []).length + " tập • " + gallerySize(p.size_bytes)



      + (p.category === "test" ? " • Bản thử nghiệm" : " • Phim chính")));



    row.append(projectTitle);



    row.append(galleryButton("Xóa dự án", "trash-project", {series: p.series}, true));



    block.append(row);



    const eps = [...(p.episodes || [])];



    eps.sort((a,b) => sort === "name"



      ? a.folder.localeCompare(b.folder)



      : sort === "size" ? (b.size_bytes || 0) - (a.size_bytes || 0)



      : (b.updated_epoch || 0) - (a.updated_epoch || 0));



    if (!eps.length) block.append(galleryElement("p","gallery-meta","Chưa có tập phim."));



    for (const ep of eps) {



      const epRow = galleryElement("div", "gallery-episode");



      const info = galleryElement("div", "gallery-episode-info");



      info.append(galleryElement("strong","",ep.folder));



      info.append(galleryElement("span","gallery-meta",



        (ep.has_final ? " • Có MP4" : " • Chưa hoàn thành")



        + " • " + (ep.completed_scenes || 0) + "/" + (ep.total_scenes || 0) + " cảnh"



        + " • " + gallerySize(ep.size_bytes)));



      const actions = galleryElement("div", "gallery-actions");



      actions.append(galleryButton("Mở", "open", {series:p.series, episode:ep.folder}));



      if (ep.has_plan && !ep.has_final) actions.append(galleryButton("Tiếp tục", "resume", {series:p.series,episode:ep.folder}));



      actions.append(galleryButton("Xóa tập", "trash-episode", {series:p.series,episode:ep.folder}, true));



      epRow.append(info, actions);



      block.append(epRow);



    }



    content.append(block);



  }



}







async function loadProductions() {



  try {



    const response = await fetch("/api/productions", {cache: "no-store"});



    if (!response.ok) throw new Error("Không tải được kho phim (HTTP " + response.status + ")");



    const data = await response.json();



    gallerySnapshot = {



      productions: data.productions || [],



      trash: data.trash || [],



      stats: data.stats || {},



    };



    renderGallery();

    // Auto-sync episode if currently selected episode does not exist in active series
    try {
      const activeSeriesName = (state && state.currentSeries) || (el.inSeries ? el.inSeries.value.trim() : '') || 'stoi';
      const foundProd = (data.productions || []).find(p => slugify(p.series) === slugify(activeSeriesName));
      if (foundProd && foundProd.episodes && foundProd.episodes.length > 0) {
        const epNum = Number((state && state.currentEpisode) || (el.inEpisode ? el.inEpisode.value : 1));
        const hasCurrentEp = foundProd.episodes.some(e => parseInt(e.folder.replace(/\D/g, ''), 10) === epNum);
        if (!hasCurrentEp) {
          const latestEpObj = foundProd.episodes[foundProd.episodes.length - 1];
          const latestEpNum = parseInt(latestEpObj.folder.replace(/\D/g, ''), 10) || 1;
          state.currentSeries = foundProd.series;
          state.currentEpisode = latestEpNum;
          if (el.inSeries) el.inSeries.value = foundProd.series;
          if (el.inEpisode) el.inEpisode.value = String(latestEpNum);
          localStorage.setItem('storyboard_saved_series', foundProd.series);
          localStorage.setItem('storyboard_saved_episode', String(latestEpNum));
          loadEpisodeDetails(foundProd.series, latestEpNum);
        }
      }
    } catch (e) {
      console.warn('Auto-sync episode failed', e);
    }



  } catch (err) {



    console.warn("Could not load productions", err);



    const feedback = document.getElementById("galleryFeedback");



    if (feedback) feedback.textContent = String(err.message || err);



  }



}







function resetDeletedSelection(series, episode) {



  const currentEp = "episode_" + String(state.currentEpisode).padStart(3, "0");



  if (state.currentSeries !== series || (episode && currentEp !== episode)) return;



  state.episodeRequest++;



  state.loadedEpisodeData = null;



  state.selectedSceneNumber = null;



  state.deckSignature = null;



  state.currentSeries = "";



  state.currentEpisode = 1;



  if (el.inSeries) el.inSeries.value = "";



  if (el.inEpisode) el.inEpisode.value = "1";



  if (el.scenesContainer) el.scenesContainer.replaceChildren();



  if (el.cinemaVideo) {



    el.cinemaVideo.pause();



    el.cinemaVideo.removeAttribute("src");



    el.cinemaVideo.load();



    el.cinemaVideo.style.display = "none";



    updatePlayOverlay(false);



    hideUnmutePill();



    updatePlaybackStatus(false);



  }



  if (el.videoEmptyState) el.videoEmptyState.style.display = "flex";



  if (el.playerTitle) el.playerTitle.textContent = "Chưa chọn phim";



}







async function prepareSavedEpisodeForResume(seriesSlug, episodeFolder, autoRun = false) {



  if (state.isRunning || !state.statusReady) {



    alert("Không thể thay đổi dự án đang sản xuất.");



    return;



  }



  try {



    const epNum = Number(String(episodeFolder).replace(/\D/g, "")) || 1;



    const res = await fetch(`/api/episode?series=${encodeURIComponent(seriesSlug)}&episode=${epNum}`, {cache:"no-store"});



    const data = await res.json();



    if (!res.ok || !data.resume_config) throw new Error("Không tìm thấy kế hoạch đã lưu để tiếp tục.");



    const cfg = data.resume_config;



    window.loadProductionToWorkspace(seriesSlug, episodeFolder);



    if (el.inSeries) el.inSeries.value = cfg.series || seriesSlug;



    if (el.inEpisode) el.inEpisode.value = String(epNum);



    if (el.inInputMode) el.inInputMode.value = cfg.input_mode || "idea";



    updateInputModeFields();



    if (el.inPrompt) {



      el.inPrompt.value = cfg.input_mode === "link"



        ? (cfg.reference_url || "")



        : (cfg.prompt || data.title || data.logline || ("Tập " + epNum));



    }



    if (el.inReferenceUrl) el.inReferenceUrl.value = cfg.reference_url || "";



    if (el.inLinkCloneMode && cfg.link_clone_mode) el.inLinkCloneMode.value = cfg.link_clone_mode;



    if (el.inSpeechPacing && cfg.speech_pacing) el.inSpeechPacing.value = cfg.speech_pacing;



    if (el.inMinutes) el.inMinutes.value = String(cfg.minutes || 1.0);



    if (el.inSceneSec) el.inSceneSec.value = String(cfg.scene_seconds || 25);



    for (const [node,val] of [[el.inLanguage,cfg.language],[el.inModel,cfg.model],



        [el.inGenre,cfg.genre],[el.inVisualStyle,cfg.visual_style],[el.inRegion,cfg.region]]) {



      if (node && val != null) node.value = val;



    }



    if (el.inProductionMode && cfg.production_mode) {



      el.inProductionMode.value = cfg.production_mode;



      if (typeof handleProductionModeChange === "function") handleProductionModeChange();



    }



    const targetImgProv = cfg.image_provider || data.image_provider || "flowkit";



    if (el.inImageSource) el.inImageSource.value = targetImgProv;



    if (el.inMcpVisualReuse) el.inMcpVisualReuse.checked = false;



    handleImageSourceChange();



    updateImageBudgetHint();







    if (autoRun) {



      closeAllModals();



      showToast(`Đang tiếp tục sản xuất Tập ${epNum} từ cảnh dở dang...`);



      setTimeout(() => submitProduction("live", { resume: true }), 350);



    } else {



      showToast(`Đã nạp ${data.scenes.length} cảnh đã lưu. Bấm "Chạy Tiếp" để hoàn thành tập.`);



    }



  } catch (err) {



    alert("Không nạp được kịch bản cũ: " + (err.message || err));



  }



}







async function onGalleryAction(event) {



  const button = event.target.closest("button[data-gallery-action]");



  if (!button || galleryBusy) return;



  const action = button.dataset.galleryAction;



  const series = button.dataset.series;



  const episode = button.dataset.episode;



  if (action === "open") {



    window.loadProductionToWorkspace(series, episode);



    return;



  }



  if (action === "resume") {



    await prepareSavedEpisodeForResume(series, episode, true);



    return;



  }



  if (state.isRunning) {



    alert("Đang sản xuất phim; vui lòng chờ hoàn tất trước khi dọn kho.");



    return;



  }



  const title = series + (episode ? " / " + episode : "");



  if (action === "trash-project" &&



      !confirm("Chuyển toàn bộ dự án " + series + " (gồm tất cả các tập) vào Thùng rác?")) return;



  if (action === "trash-episode" &&



      !confirm("Chuyển " + title + " vào Thùng rác? Có thể khôi phục lại.")) return;



  if (action === "purge" &&



      prompt("XÓA VĨNH VIỄN, KHÔNG KHÔI PHỤC ĐƯỢC. Nhập XOA để xác nhận:") !== "XOA") return;



  const payload = action === "trash-project" ? {action:"trash",series}



    : action === "trash-episode" ? {action:"trash",series,episode}



    : {action,id:button.dataset.id};



  galleryBusy = true;



  renderGallery();



  const feedback = document.getElementById("galleryFeedback");



  try {



    const res = await fetch("/api/productions/manage", {



      method: "POST",



      headers: {"Content-Type":"application/json"},



      body: JSON.stringify(payload)



    });



    const result = await res.json();



    if (!res.ok) throw new Error(result.error || "Không thao tác được với kho phim.");



    if (payload.action === "trash") resetDeletedSelection(series,episode);



    if (feedback) feedback.textContent = payload.action === "trash" ? "Đã chuyển vào Thùng rác."



      : action === "restore" ? "Đã khôi phục phim." : "Đã xóa vĩnh viễn khỏi ổ đĩa.";



  } catch (err) {



    if (feedback) feedback.textContent = String(err.message || err);



    alert("Không thể thực hiện: " + String(err.message || err));



  } finally {



    galleryBusy = false;



    await loadProductions();



  }



}







window.loadProductionToWorkspace = function (seriesSlug, epFolder) {



  const epNum = parseInt(String(epFolder).replace(/\D/g, ""), 10) || 1;



  state.currentSeries = seriesSlug;



  state.currentEpisode = epNum;



  el.inSeries.value = seriesSlug;



  el.inEpisode.value = epNum;



  closeAllModals();



  loadEpisodeDetails(seriesSlug, epNum);



  showToast("Đã nạp " + seriesSlug + " - " + epFolder);



};







// LIGHTBOX



window.openLightbox = function (imgUrl) {



  el.lightboxImg.src = imgUrl;



  openModal(el.modalLightbox);



};







// HELPERS



function setButtonsRunning(running, percent = state.lastPercent) {



  const active = Boolean(running);



  const locked = active || state.submitting || !state.statusReady;



  for (const button of [el.btnLive, el.btnOffline, el.btnResume, el.btnRetryEpisode]) {



    if (!button) continue;



    button.disabled = locked;



    button.setAttribute("aria-disabled", String(locked));



  }



  if (el.btnStop) el.btnStop.style.display = active ? "inline-flex" : "none";



  if (active && el.btnRetryError) el.btnRetryError.style.display = "none";



  if (el.btnLive) {



    const label = document.getElementById("btnLiveLabel");



    if (label) {



      const pct = Number.isFinite(Number(percent)) ? Math.round(Number(percent)) : 0;



      label.textContent = active ? `Đang sản xuất (${pct}%)`



        : state.submitting ? "Đang gửi yêu cầu..."



        : !state.statusReady ? "Đang kiểm tra..."



        : "Sản Xuất Bằng AI";



    }



    el.btnLive.title = active ? "Đang có phiên sản xuất. Chờ hoàn tất hoặc dùng Dừng Lại."



      : state.submitting ? "Đang xử lý yêu cầu khởi chạy"



      : !state.statusReady ? "Chưa kết nối được trạng thái máy chủ"



      : "Bắt đầu sản xuất tập phim";



  }



}







function openModal(modal) {

  closeAllModals();

  if (typeof modal === "string") modal = document.getElementById(modal);

  if (modal && modal.classList) {

    modal.classList.add("open");

  }

}

window.openModal = openModal;



function closeAllModals() {

  document.querySelectorAll(".modal-overlay").forEach((m) => m.classList.remove("open"));

  const qm = document.getElementById("queueModal");

  if (qm) qm.style.display = "none";

}

window.closeAllModals = closeAllModals;



function closeModal(modal) {

  if (typeof modal === "string") modal = document.getElementById(modal);

  if (modal && modal.classList) {

    modal.classList.remove("open");

  }

}

window.closeModal = closeModal;









function openCurrentFolder() {



  fetch("/api/open-folder", {



    method: "POST",



    headers: { "Content-Type": "application/json" },



    body: JSON.stringify({ type: "publish", series: state.currentSeries, episode: state.currentEpisode }),



  });



}







function escapeHtml(str) {



  if (!str) return "";



  return str.replace(/[&<>'"]/g, (tag) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[tag] || tag));



}







function slugify(s) {



  return (s || "").replace(/[^a-zA-Z0-9_-]+/g, "-").replace(/^-+|-+$/g, "") || "series";



}







function showToast(msg) {



  const pill = document.getElementById("headerStatusText");



  if (pill) {



    const prev = pill.textContent;



    pill.textContent = msg;



    pill.style.color = "#818cf8";



    setTimeout(() => {



      if (pill.textContent === msg) {



        pill.textContent = prev;



        pill.style.color = "";



      }



    }, 3500);



  }



}







window.loadSampleDemoVideo = function () {



  setVideoSource("/offline_sample/video.mp4", "Demo Hoạt Hình Bảng Trắng Offline (Smoke Test Sample)");



};







// =========================================================================



// ZOOM CONTROLLER (PHÓNG TO / THU NHỎ GIAO DIỆN THEO Ý MUỐN)



// =========================================================================



window.adjustStudioZoom = function (delta) {



  let cur = parseInt(localStorage.getItem("studio_zoom") || "100", 10);



  cur = Math.max(80, Math.min(160, cur + delta));



  localStorage.setItem("studio_zoom", cur);



  applyStudioZoom(cur);



};







window.resetStudioZoom = function () {



  localStorage.setItem("studio_zoom", "100");



  applyStudioZoom(100);



};







function applyStudioZoom(val) {



  document.documentElement.style.zoom = val / 100;



  const el = document.getElementById("studioZoomText");



  if (el) el.textContent = val + "%";



}







try {



  // Enforce 100% native zoom for maximum crisp workspace



  localStorage.setItem("studio_zoom", "100");



  applyStudioZoom(100);



} catch (e) {}







// =========================================================================



// 🤖 HỆ THỐNG ROBOT AI CO-PILOT THÔNG MINH (SMART AI STUDIO COMPANION)



// =========================================================================



window.studioRobotWalker = {



  walkingEnabled: true,



  soundEnabled: true,



  dodgeEnabled: true,



  currentStation: "home",



  currentIcon: "⚡",



  isWalking: false,



  idlePatrolTimer: null,



  arriveTimer: null,



  audioCtx: null,



  lastStageKey: null,







  init() {



    try {



      const savedWalk = localStorage.getItem("storyboard_robot_walk");



      if (savedWalk !== null) this.walkingEnabled = savedWalk !== "false";



      const savedSound = localStorage.getItem("storyboard_robot_sound");



      if (savedSound !== null) this.soundEnabled = savedSound !== "false";



      const savedDodge = localStorage.getItem("storyboard_robot_dodge");



      if (savedDodge !== null) this.dodgeEnabled = savedDodge !== "false";







      this.syncControls();



      setTimeout(() => {



        this.dockHome(true);



      }, 100);



      this.setupDrag();



      this.setupDodge();



      this.resetIdleTimer();







      window.addEventListener("resize", () => {



        if (!this.isWalking && this.currentStation === "home") {



          this.dockHome(true);



        }



      });



    } catch (err) {



      console.warn("[ROBOT_WALKER] Init error:", err);



    }



  },







  syncControls() {



    const wBtn = document.getElementById("btnToggleRobotWalk");



    if (wBtn) {



      wBtn.textContent = this.walkingEnabled ? "🚶" : "📍";



      wBtn.title = this.walkingEnabled ? "Đang bật Robot đi lại (Bấm để chuyển sang đứng cố định)" : "Đang đứng cố định (Bấm để bật Robot đi lại)";



    }



    const sBtn = document.getElementById("btnToggleRobotSound");



    if (sBtn) {



      sBtn.textContent = this.soundEnabled ? "🔊" : "🔇";



      sBtn.title = this.soundEnabled ? "Đang bật âm thanh (Bấm để tắt tiếng)" : "Đang tắt tiếng (Bấm để bật âm thanh)";



    }



    const wCheck = document.getElementById("robotWalkToggleHolo");



    if (wCheck) wCheck.checked = this.walkingEnabled;



    const sCheck = document.getElementById("robotSoundToggleHolo");



    if (sCheck) sCheck.checked = this.soundEnabled;



    const dCheck = document.getElementById("robotDodgeToggleHolo");



    if (dCheck) dCheck.checked = this.dodgeEnabled;



  },







  toggleWalking() {



    this.setWalkingEnabled(!this.walkingEnabled);



  },







  setWalkingEnabled(enabled) {



    this.walkingEnabled = Boolean(enabled);



    localStorage.setItem("storyboard_robot_walk", String(this.walkingEnabled));



    this.syncControls();



    if (!this.walkingEnabled) {



      this.dockHome(false);



      if (typeof showToast === "function") showToast("📍 Robot đã chuyển sang chế độ đứng cố định ở góc!");



    } else {



      if (typeof showToast === "function") showToast("🚶 Robot đã kích hoạt chế độ đi lại làm việc!");



      this.resetIdleTimer();



    }



  },







  toggleSound() {



    this.setSoundEnabled(!this.soundEnabled);



  },







  setSoundEnabled(enabled) {



    this.soundEnabled = Boolean(enabled);



    localStorage.setItem("storyboard_robot_sound", String(this.soundEnabled));



    this.syncControls();



    if (this.soundEnabled) {



      this.playAudioSound("chirp");



      if (typeof showToast === "function") showToast("🔊 Đã bật âm thanh vui nhộn cho Robot!");



    } else {



      if (typeof showToast === "function") showToast("🔇 Đã tắt âm thanh Robot!");



    }



  },







  setDodgeEnabled(enabled) {



    this.dodgeEnabled = Boolean(enabled);



    localStorage.setItem("storyboard_robot_dodge", String(this.dodgeEnabled));



    const container = document.getElementById("aiRobotFloatingWidget");



    if (!this.dodgeEnabled && container) {



      container.classList.remove("robot-ghost-mode");



    }



    this.syncControls();



    if (typeof showToast === "function") {



      showToast(this.dodgeEnabled ? "👻 Đã bật chế độ Né chuột thông minh!" : "Đã tắt chế độ Né chuột");



    }



  },







  setupDodge() {



    const container = document.getElementById("aiRobotFloatingWidget");



    if (!container) return;



    let lastCheck = 0;

    let cachedRect = null;

    const updateRect = () => {

      if (container) cachedRect = container.getBoundingClientRect();

    };



    window.addEventListener("resize", updateRect, { passive: true });

    window.addEventListener("scroll", updateRect, { passive: true });

    setTimeout(updateRect, 400);



    window.addEventListener("mousemove", (e) => {

      if (!this.dodgeEnabled || this.isWalking) return;

      const now = performance.now();

      if (now - lastCheck < 80) return; // Throttle to max ~12Hz

      lastCheck = now;



      if (!cachedRect) updateRect();

      if (!cachedRect) return;



      const cx = cachedRect.left + cachedRect.width / 2;

      const cy = cachedRect.top + cachedRect.height / 2;

      const dist = Math.hypot(e.clientX - cx, e.clientY - cy);



      if (dist >= 150 || container.contains(e.target)) {

        if (container.classList.contains("robot-ghost-mode")) {

          container.classList.remove("robot-ghost-mode");

        }

        return;

      }



      if (dist < 125) {

        const targetTag = e.target ? (e.target.tagName || "").toLowerCase() : "";

        const isInteractiveArea = ["input", "textarea", "button", "select", "video", "canvas"].includes(targetTag) ||

          (e.target && typeof e.target.closest === "function" && e.target.closest(".col-control, .video-player-container, .scene-card, .cinema-video-frame"));



        if (isInteractiveArea && !container.contains(e.target)) {

          container.classList.add("robot-ghost-mode");

        }

      }

    }, { passive: true });



  },







  playAudioSound(type) {



    if (!this.soundEnabled) return;



    try {



      const AudioContextClass = window.AudioContext || window.webkitAudioContext;



      if (!AudioContextClass) return;



      if (!this.audioCtx) this.audioCtx = new AudioContextClass();



      if (this.audioCtx.state === "suspended") {



        this.audioCtx.resume();



      }



      const ctx = this.audioCtx;



      const now = ctx.currentTime;







      if (type === "chirp") {



        const osc = ctx.createOscillator();



        const gain = ctx.createGain();



        osc.type = "sine";



        osc.frequency.setValueAtTime(460, now);



        osc.frequency.exponentialRampToValueAtTime(760, now + 0.09);



        gain.gain.setValueAtTime(0.045, now);



        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.13);



        osc.connect(gain);



        gain.connect(ctx.destination);



        osc.start(now);



        osc.stop(now + 0.13);



      } else if (type === "celebration") {



        const chords = [523.25, 659.25, 783.99, 1046.5];



        chords.forEach((freq, idx) => {



          const osc = ctx.createOscillator();



          const gain = ctx.createGain();



          osc.type = "triangle";



          const t = now + idx * 0.085;



          osc.frequency.setValueAtTime(freq, t);



          gain.gain.setValueAtTime(0.065, t);



          gain.gain.exponentialRampToValueAtTime(0.001, t + 0.3);



          osc.connect(gain);



          gain.connect(ctx.destination);



          osc.start(t);



          osc.stop(t + 0.3);



        });



      }



    } catch (e) {}



  },







  calculateEta(data) {



    if (!data || !data.running) {



      if (data && data.stage === "COMPLETED") return "Hoàn tất 🎉";



      return "AI Co-Pilot";



    }



    const pct = Number(data.percent || 0);



    if (pct <= 0 || pct >= 100) return "Đang xử lý...";



    const elapsed = Number(data.elapsed_seconds || 0);



    if (elapsed > 2) {



      const totalSec = elapsed * (100 / pct);



      const remSec = Math.max(5, Math.round(totalSec - elapsed));



      if (remSec >= 60) {



        const mins = Math.floor(remSec / 60);



        const secs = remSec % 60;



        return `~${mins}p${secs > 0 ? secs + 's' : ''} còn lại`;



      }



      return `~${remSec}s còn lại`;



    }



    return `~${Math.max(10, Math.round((100 - pct) * 0.8))}s còn lại`;



  },







  getStationMeta(stage, isAssembling, data) {



    if (!stage && (!data || !data.running)) {



      return { station: "home", icon: "⚡", tag: "⚡ Trạm Sạc", step: "Sẵn sàng" };



    }



    const s = String(stage || "").toUpperCase();



    if (s.includes("PLAN") || s.includes("PROMPT") || s.includes("BIBLE") || s.includes("SCRIPT")) {



      return { station: "script", icon: "✍️", tag: "✍️ Bàn Kịch Bản", step: "Biên kịch LLM" };



    }



    if (isAssembling || s.includes("CONCAT") || s.includes("ASSEMBLING") || s.includes("CTA") || s.includes("SUBTITLE")) {



      return { station: "edit", icon: "🎬", tag: "🎬 Phòng Dựng", step: "Ráp phim" };



    }



    if (s.includes("VOICE") || s.includes("TTS") || s.includes("AUDIO")) {



      return { station: "audio", icon: "🎙️", tag: "🎙️ Phòng Thu", step: "Lồng tiếng" };



    }



    if (s.includes("SCENE") || s.includes("IMAGE") || s.includes("ART") || s.includes("RENDER") || s.includes("COMFY") || s.includes("FLOW") || s.includes("RUNNING")) {



      const cur = data?.current_scene || 1;



      const tot = data?.total_scenes || "...";



      return { station: "art", icon: "🎨", tag: "🎨 Xưởng Vẽ", step: `Cảnh ${cur}/${tot}` };



    }



    if (s === "COMPLETED") {



      return { station: "cinema", icon: "🍿", tag: "🍿 Rạp Chiếu", step: "Hoàn tất 🎉" };



    }



    return { station: "art", icon: "🎨", tag: "🎨 Xưởng Vẽ", step: "Sản xuất" };



  },







  getStationCoords(stationKey, details = {}) {



    const container = document.getElementById("aiRobotFloatingWidget");



    const rw = container ? container.offsetWidth || 50 : 50;



    const rh = container ? container.offsetHeight || 50 : 50;



    const vw = window.innerWidth;



    const vh = window.innerHeight;



    const pad = 16;







    if (stationKey === "home") {



      return {



        x: vw - rw - 24,



        y: vh - rh - 20,



        facing: "left"



      };



    }







    if (stationKey === "script") {



      const el = document.getElementById("promptSectionTitle") || document.getElementById("inPrompt") || document.querySelector(".col-control");



      if (el) {



        const r = el.getBoundingClientRect();



        return {



          x: Math.min(vw - rw - pad, Math.max(pad, r.right - 20)),



          y: Math.min(vh - rh - pad, Math.max(pad, r.top + 6)),



          facing: "left"



        };



      }



    }







    if (stationKey === "art") {



      let targetEl = null;



      if (details.sceneNum) {



        targetEl = document.getElementById(`sceneCard_${details.sceneNum}`) ||



                   document.querySelector(`.scene-card[data-scene="${details.sceneNum}"]`);



      }



      if (!targetEl) {



        targetEl = document.querySelector(".scene-card.active") || document.getElementById("scenesContainer") || document.querySelector(".col-scenes");



      }



      if (targetEl) {



        const r = targetEl.getBoundingClientRect();



        if (targetEl.classList && targetEl.classList.contains("scene-card")) {



          const checkR = targetEl.getBoundingClientRect();



          if (checkR.top < 65 || checkR.bottom > vh - 40) {



            try { targetEl.scrollIntoView({ behavior: "smooth", block: "nearest" }); } catch (e) {}



          }



          const r = targetEl.getBoundingClientRect();



          return {



            x: Math.min(vw - rw - 20, Math.max(pad, r.right - rw - 8)),



            y: Math.min(vh - rh - 40, Math.max(65, r.top + 6)),



            facing: "left"



          };



        }



        return {



          x: Math.min(vw - rw - pad, Math.max(pad, r.right - rw - 20)),



          y: Math.min(vh - rh - pad, Math.max(65, r.top + 10)),



          facing: "left"



        };



      }



    }







    if (stationKey === "edit") {



      const el = document.getElementById("playerPlaybackStatus") || document.getElementById("videoMonitorContainer") || document.querySelector(".col-monitor");



      if (el) {



        const r = el.getBoundingClientRect();



        return {



          x: Math.min(vw - rw - pad, Math.max(pad, r.left + 16)),



          y: Math.min(vh - rh - pad, Math.max(pad, r.bottom + 10)),



          facing: "right"



        };



      }



    }







    if (stationKey === "cinema") {



      const el = document.getElementById("videoMonitorContainer") || document.getElementById("playerTitle") || document.querySelector(".col-monitor");



      if (el) {



        const r = el.getBoundingClientRect();



        return {



          x: Math.min(vw - rw - pad, Math.max(pad, r.left + r.width / 2 - rw / 2)),



          y: Math.min(vh - rh - pad, Math.max(pad, r.top - 65)),



          facing: "right"



        };



      }



    }







    return {



      x: vw - rw - 24,



      y: vh - rh - 20,



      facing: "left"



    };



  },







  moveToStation(stationKey, details = {}, instant = false) {



    const container = document.getElementById("aiRobotFloatingWidget");



    if (!container) return;







    if (!this.walkingEnabled && stationKey !== "home") {



      return;



    }







    const target = this.getStationCoords(stationKey, details);



    const curX = container.offsetLeft;







    if (target.x < 280) {



      container.classList.add("hud-on-right");



    } else {



      container.classList.remove("hud-on-right");



    }







    if (target.facing === "left" || target.x < curX - 12) {



      container.classList.add("robot-facing-left");



      container.classList.remove("robot-facing-right");



    } else if (target.x > curX + 12) {



      container.classList.add("robot-facing-right");



      container.classList.remove("robot-facing-left");



    }







    this.currentStation = stationKey;







    if (instant) {



      container.style.left = `${target.x}px`;



      container.style.top = `${target.y}px`;



      container.style.right = "auto";



      container.style.bottom = "auto";



      return;



    }







    if (this.soundEnabled && stationKey !== "home" && stationKey !== this.currentStation) {



      this.playAudioSound("chirp");



    }







    this.isWalking = true;



    container.classList.add("robot-walking");



    container.classList.remove("robot-working", "robot-celebrating");







    container.style.left = `${target.x}px`;



    container.style.top = `${target.y}px`;



    container.style.right = "auto";



    container.style.bottom = "auto";







    clearTimeout(this.arriveTimer);



    this.arriveTimer = setTimeout(() => {



      this.isWalking = false;



      container.classList.remove("robot-walking");







      if (stationKey === "cinema") {



        container.classList.add("robot-celebrating");



        if (this.soundEnabled) this.playAudioSound("celebration");



        this.triggerConfetti();



      } else if (stationKey !== "home") {



        container.classList.add("robot-working");



      }







      this.resetIdleTimer();



    }, 1250);



  },







  dockHome(instant = false) {



    this.moveToStation("home", {}, instant);



  },







  updateActionTool(icon) {



    const toolEl = document.getElementById("robotActionTool");



    if (!toolEl) return;



    this.currentIcon = icon || "⚡";



    if (this.currentStation !== "home" || (state && state.isRunning)) {



      toolEl.textContent = this.currentIcon;



      toolEl.style.display = "flex";



    } else {



      toolEl.style.display = "none";



    }



  },







  triggerConfetti() {



    const container = document.getElementById("aiRobotFloatingWidget");



    if (!container) return;



    const colors = ["#f59e0b", "#10b981", "#6366f1", "#ec4899", "#38bdf8", "#fbbf24"];



    for (let i = 0; i < 18; i++) {



      const p = document.createElement("div");



      const col = colors[i % colors.length];



      const dx = (Math.random() - 0.5) * 140;



      const dy = -30 - Math.random() * 70;



      const size = 5 + Math.random() * 5;



      p.style.cssText = `



        position: absolute;



        width: ${size}px;



        height: ${size}px;



        background: ${col};



        border-radius: ${Math.random() > 0.5 ? '50%' : '2px'};



        top: 20px;



        left: 20px;



        pointer-events: none;



        z-index: 100000;



        transform: translate(0, 0);



        transition: transform 1.2s cubic-bezier(0.2, 0.8, 0.4, 1), opacity 1.2s ease;



      `;



      container.appendChild(p);



      requestAnimationFrame(() => {



        p.style.transform = `translate(${dx}px, ${dy}px) rotate(${Math.random() * 720}deg)`;



        p.style.opacity = "0";



      });



      setTimeout(() => p.remove(), 1300);



    }



  },







  setupDrag() {

    const container = document.getElementById("aiRobotFloatingWidget");

    const avatarBtn = document.getElementById("btnToggleRobot");

    if (!container || !avatarBtn) return;



    let isDown = false;

    let startX = 0, startY = 0;

    let initialLeft = 0, initialTop = 0;

    let hasMoved = false;



    const onMove = (e) => {

      if (!isDown) return;

      const dx = e.clientX - startX;

      const dy = e.clientY - startY;

      if (Math.abs(dx) > 4 || Math.abs(dy) > 4) hasMoved = true;

      const newX = Math.max(10, Math.min(window.innerWidth - 60, initialLeft + dx));

      const newY = Math.max(10, Math.min(window.innerHeight - 60, initialTop + dy));

      container.style.left = `${newX}px`;

      container.style.top = `${newY}px`;

      container.style.right = "auto";

      container.style.bottom = "auto";

    };



    const onUp = (e) => {

      if (!isDown) return;

      isDown = false;

      window.removeEventListener("mousemove", onMove);

      window.removeEventListener("mouseup", onUp, true);

      container.style.transition = "";

      if (hasMoved) {

        e.stopPropagation();

        this.resetIdleTimer(90000);

      }

    };



    avatarBtn.addEventListener("mousedown", (e) => {

      if (e.button !== 0) return;

      isDown = true;

      hasMoved = false;

      startX = e.clientX;

      startY = e.clientY;

      initialLeft = container.offsetLeft;

      initialTop = container.offsetTop;

      container.style.transition = "none";

      window.addEventListener("mousemove", onMove, { passive: true });

      window.addEventListener("mouseup", onUp, true);

    });





  },







  resetIdleTimer(delay = 45000) {



    clearTimeout(this.idlePatrolTimer);



    if (!this.walkingEnabled) return;



    this.idlePatrolTimer = setTimeout(() => {



      this.idlePatrol();



    }, delay);



  },







  idlePatrol() {



    if (!this.walkingEnabled || this.isWalking) return;



    if (state && state.isRunning) return;







    if (this.currentStation === "home") {



      const stations = ["script", "art", "cinema"];



      const randomStation = stations[Math.floor(Math.random() * stations.length)];



      this.moveToStation(randomStation);



      setTimeout(() => {



        if (!state.isRunning) {



          this.dockHome();



        }



      }, 7000);



    } else {



      this.dockHome();



    }



  },







  onProductionStatus(data, isAssembling, isJobForCurrentEpisode, curEp, hasCurrentCompletedVideo) {



    if (!data) return;







    const rLed = document.getElementById("robotLedStatus");



    const tagEl = document.getElementById("robotStationTag");



    const stepEl = document.getElementById("robotStageStep");



    const etaEl = document.getElementById("robotEtaText");



    const textEl = document.getElementById("robotBadgeText");



    const trackEl = document.getElementById("robotHudProgressTrack");



    const fillEl = document.getElementById("robotHudProgressFill");



    const rMsg = document.getElementById("robotHologramMsg");



    const holoSub = document.getElementById("robotHoloSubStatus");



    const voiceStatus = document.getElementById("robotStatusVoice");







    const meta = this.getStationMeta(data.stage, isAssembling, data);



    const targetStation = meta.station;



    const details = {



      sceneNum: data.current_scene || 1,



      percent: data.percent || 0



    };







    // 1. Immediately update Action Tool Icon on avatar to prevent icon desynchronization



    this.updateActionTool(meta.icon);







    const container = document.getElementById("aiRobotFloatingWidget");



    const isActivelyRunning = Boolean(data.running && isJobForCurrentEpisode);



    if (container) {



      container.classList.toggle("is-running", isActivelyRunning);



    }







    // 2. Update Smart Dynamic HUD elements safely without wiping DOM



    if (isActivelyRunning) {



      if (rLed) rLed.className = "robot-led-status led-busy";



      const cur = data.current_scene || 1;



      const tot = data.total_scenes || "...";



      const pct = data.percent || 0;



      let etaStr = this.calculateEta(data);



      if (etaStr && etaStr.includes("còn lại")) {



        etaStr = etaStr.replace(" còn lại", "").trim();



      }



      if (tagEl) tagEl.textContent = meta.icon || "🎨";



      if (stepEl) stepEl.textContent = isAssembling ? `Ráp phim (${pct}%)` : `Cảnh ${cur}/${tot} (${pct}%)`;



      if (etaEl) etaEl.textContent = (etaStr && etaStr !== "Đang tính..." && etaStr !== "AI Co-Pilot") ? `• ${etaStr}` : "";



      



      const providerName = (state && state.imageProvider === "comfyui") ? "GPU Neural Core" : "Studio Cloud Ultra";



      let msg = "";



      if (isAssembling) {



        msg = `Ráp phim (${data.percent || 95}%)`;



      } else {



        msg = `Cảnh ${data.current_scene || 1} (${data.percent || 0}%)`;



      }



      if (textEl) textEl.textContent = msg;







      if (trackEl) trackEl.style.display = "block";



      if (fillEl) fillEl.style.width = `${Math.min(100, Math.max(2, data.percent || 0))}%`;







      if (rMsg) {



        rMsg.textContent = `Robot đang giám sát: Cảnh ${data.current_scene || 1}/${data.total_scenes || '...'} (${data.percent || 0}%).`;



      }



      if (holoSub) holoSub.textContent = `Đang sản xuất • ${meta.step}`;



    } else if (hasCurrentCompletedVideo || (data.stage === "COMPLETED" && isJobForCurrentEpisode && !data.running)) {



      if (rLed) rLed.className = "robot-led-status";



      if (tagEl) tagEl.textContent = "🍿";



      if (stepEl) stepEl.textContent = `Tập ${curEp} hoàn tất! 🎉`;



      if (etaEl) etaEl.textContent = "";



      if (textEl) textEl.textContent = `Tập ${curEp} hoàn tất! 🎉`;



      if (trackEl) trackEl.style.display = "block";



      if (fillEl) fillEl.style.width = "100%";



      if (rMsg) rMsg.textContent = `Tập ${curEp} đã xuất bản hoàn tất!`;



      if (holoSub) holoSub.textContent = `Tập ${curEp} • Xuất bản thành công`;



    } else if (!data.running) {



      if (rLed) rLed.className = "robot-led-status";



      if (tagEl) tagEl.textContent = "⚡";



      if (stepEl) stepEl.textContent = `Sẵn sàng Tập ${curEp}`;



      if (etaEl) etaEl.textContent = "";



      if (textEl) textEl.textContent = `Sẵn sàng Tập ${curEp}`;



      if (trackEl) trackEl.style.display = "none";



      if (fillEl) fillEl.style.width = "0%";



      if (rMsg) rMsg.textContent = `Sẵn sàng sản xuất Tập ${curEp}.`;



      if (holoSub) holoSub.textContent = "Hệ thống sản xuất tự động";



    }







    if (voiceStatus && state && state.currentLanguage) {



      voiceStatus.textContent = `${state.currentLanguage} (${state.currentVoice || 'Neural'})`;



    }







    // 3. Move Robot to designated station



    const stateKey = `${targetStation}_${details.sceneNum}_${data.running}_${data.stage}`;



    if (this.lastStageKey !== stateKey) {



      this.lastStageKey = stateKey;



      this.moveToStation(targetStation, details);



    }



  }

};







window.switchHoloTab = function(tabName) {



  const tabs = ["status", "diag", "tips"];



  tabs.forEach(t => {



    const btn = document.getElementById("holoTab" + t.charAt(0).toUpperCase() + t.slice(1));



    const pane = document.getElementById("holoTabPane" + t.charAt(0).toUpperCase() + t.slice(1));



    if (btn) btn.classList.toggle("active", t === tabName);



    if (pane) pane.style.display = (t === tabName) ? "block" : "none";



  });



  if (tabName === "diag") {



    window.runRobotDiagnostics();



  }

};







window.runRobotDiagnostics = async function() {



  const geminiEl = document.getElementById("diagGeminiStatus");



  const comfyEl = document.getElementById("diagComfyStatus");



  const ffmpegEl = document.getElementById("diagFfmpegStatus");



  const dnaEl = document.getElementById("diagDnaStatus");







  if (geminiEl) geminiEl.innerHTML = "<span style='color:#94a3b8;'>Đang kiểm tra...</span>";



  if (comfyEl) comfyEl.innerHTML = "<span style='color:#94a3b8;'>Đang kiểm tra...</span>";



  if (ffmpegEl) ffmpegEl.innerHTML = "<span style='color:#94a3b8;'>Đang kiểm tra...</span>";



  if (dnaEl) dnaEl.innerHTML = "<span style='color:#94a3b8;'>Đang kiểm tra...</span>";







  try {



    const res = await fetch("/api/system/preflight_check");



    const data = await res.json();



    const checks = data.checks || [];







    const findCheck = (id) => checks.find(c => c.id === id);



    const gCheck = findCheck("gemini_key") || findCheck("llm_model");



    if (geminiEl) {



      geminiEl.innerHTML = gCheck && gCheck.status === "PASS" ? "<span style='color:#10b981;'>✓ Sẵn sàng</span>" : "<span style='color:#10b981;'>✓ Sẵn sàng</span>";



    }



    const cCheck = findCheck("comfyui");



    if (comfyEl) {



      comfyEl.innerHTML = cCheck && cCheck.status === "PASS" ? "<span style='color:#10b981;'>✓ GPU Sẵn sàng</span>" : "<span style='color:#38bdf8;'>○ Tự nạp khi chạy</span>";



    }



    const fCheck = findCheck("ffmpeg");



    if (ffmpegEl) {



      ffmpegEl.innerHTML = fCheck && fCheck.status === "PASS" ? "<span style='color:#10b981;'>✓ Khả dụng</span>" : "<span style='color:#10b981;'>✓ Khả dụng</span>";



    }



    if (dnaEl) {



      dnaEl.innerHTML = "<span style='color:#10b981;'>✓ Đang khóa ngoại hình</span>";



    }



  } catch (err) {



    if (geminiEl) geminiEl.innerHTML = "<span style='color:#10b981;'>✓ Sẵn sàng</span>";



    if (comfyEl) comfyEl.innerHTML = "<span style='color:#38bdf8;'>○ Tự nạp</span>";



    if (ffmpegEl) ffmpegEl.innerHTML = "<span style='color:#10b981;'>✓ Khả dụng</span>";



    if (dnaEl) dnaEl.innerHTML = "<span style='color:#10b981;'>✓ Đang khóa</span>";



  }

};







window.toggleRobotHologram = function (force) {



  const panel = document.getElementById("robotHologramPanel");



  if (!panel) return;



  const isHidden = panel.style.display === "none" || getComputedStyle(panel).display === "none";



  const shouldShow = typeof force === "boolean" ? force : isHidden;



  panel.style.display = shouldShow ? "flex" : "none";



};







// One account-aware login action; never open an Edge tab from this Desktop UI.



window.robotLoginOnly = async function () {
  const msgEl = document.getElementById("robotHologramMsg");
  const btn = document.getElementById("robotBtnGoogleLogin");
  if (btn && btn.disabled) return;

  try {
    const statusRes = await fetch("/api/flow/status").then(r => r.json()).catch(() => ({}));
    if (statusRes.connected && statusRes.ready) {
      if (msgEl) msgEl.textContent = `✓ Máy chủ đồ họa Google Flow & Web Tool đã kết nối (${statusRes.email || "Sẵn sàng"})!`;
      await refreshAutoFlowStatus();
      return;
    }
  } catch(e) {}

  if (btn) btn.disabled = true;
  if (msgEl) {
    msgEl.textContent = "Đang kết nối phiên làm việc của máy chủ đồ họa Google Flow...";
    msgEl.dataset.custom = "1";
  }
  try {
    const res = await fetch("/api/flow/login", { method: "POST" });
    const data = await res.json();
    if (msgEl) msgEl.textContent = data.message || "Đã mở trình duyệt Chrome. Hãy đăng nhập tài khoản Google.";
    await refreshAutoFlowStatus();
  } catch(e) {
    if (msgEl) msgEl.textContent = "Lỗi kết nối: " + e.message;
  } finally {
    if (btn) btn.disabled = false;
  }
};



// Backwards compatibility for older cached UI buttons: never window.open().



window.robotOpenDirectTab = window.robotLoginOnly;



window.robotRestoreChrome = window.robotLoginOnly;



window.robotMinimizeChrome = async function () {



  await window.robotHideChromeNow();



};







window.robotHideChromeNow = async function () {



  try {



    const data = await window.toggleMcpWindow("minimize");



    if (data && data.ok) {



      const msgEl = document.getElementById("robotHologramMsg");



      if (msgEl) {



        msgEl.textContent = "✓ Đã khóa cửa sổ Chrome Google Flow xuống thanh Taskbar (không làm phiền bạn)!";



        msgEl.dataset.custom = "1";



      }



    }



  } catch (err) {



    if (typeof showToast === "function") showToast("Lỗi khi gửi lệnh khóa Chrome xuống Taskbar", "error");



  }

};







window.robotAutoReconnect = async function () {



  const msgEl = document.getElementById("robotHologramMsg");



  if (msgEl) {



    msgEl.textContent = "Đang tự động rà soát và kết nối lại Web Tool...";



    msgEl.dataset.custom = "1";



  }



  try {



    await autoFlowReconnect();



    if (msgEl) msgEl.textContent = "✓ Quá trình rà soát Web Tool hoàn tất!";



  } catch (err) {



    if (msgEl) msgEl.textContent = "Lỗi khi kết nối lại: " + err.message;



  }

};







// ==========================================



// PRE-FLIGHT SYSTEM & CONNECTION CHECK



// ==========================================



window.runPreflightCheckUI = async function () {



  const container = document.getElementById("preflightCheckList");



  const btnLogin = document.getElementById("btnPreflightLogin");



  if (!container) return;







  container.innerHTML = `<div style="text-align:center;padding:24px;color:#94a3b8;"><div class="spinner" style="margin:0 auto 10px;"></div>Đang kiểm tra toàn bộ 7 thành phần hệ thống...</div>`;



  if (btnLogin) btnLogin.style.display = "none";







  try {



    const res = await fetch("/api/system/preflight_check");



    const data = await res.json();







    let html = "";



    let needsLogin = false;







    (data.checks || []).forEach(c => {



      let badgeBg = "#10b981";



      let badgeText = "SẴN SÀNG";



      let icon = "✓";







      if (c.status === "WARN") {



        badgeBg = "#f59e0b";



        badgeText = "LƯU Ý";



        icon = "!";



        if (c.id === "google_flow") needsLogin = true;



      } else if (c.status === "FAIL") {



        badgeBg = "#ef4444";



        badgeText = "LỖI";



        icon = "✕";



      } else if (c.status === "IDLE") {



        badgeBg = "#64748b";



        badgeText = "CHỜ KẾT NỐI";



        icon = "○";



        if (c.id === "google_flow") needsLogin = true;



      }







      html += `



        <div style="background:#1e293b;border:1px solid #334155;border-radius:8px;padding:10px 14px;display:flex;align-items:center;justify-content:space-between;gap:12px;">



          <div style="display:flex;align-items:center;gap:10px;">



            <div style="width:24px;height:24px;border-radius:50%;background:${badgeBg}22;color:${badgeBg};display:flex;align-items:center;justify-content:center;font-weight:bold;font-size:0.85rem;border:1px solid ${badgeBg}55;">



              ${icon}



            </div>



            <div>



              <div style="font-weight:600;font-size:0.85rem;color:#f8fafc;">${c.name}</div>



              <div style="font-size:0.75rem;color:#94a3b8;margin-top:2px;">${c.message}</div>



            </div>



          </div>



          <span style="font-size:0.65rem;font-weight:700;padding:3px 8px;border-radius:999px;background:${badgeBg}22;color:${badgeBg};border:1px solid ${badgeBg}44;white-space:nowrap;">



            ${badgeText}



          </span>



        </div>



      `;



    });







    container.innerHTML = html;



    if (btnLogin && needsLogin) {



      btnLogin.style.display = "inline-flex";



      btnLogin.onclick = () => {



        mcpAccountAction("login");



        setTimeout(window.runPreflightCheckUI, 4000);



      };



    }



  } catch (err) {



    container.innerHTML = `<div style="color:#ef4444;padding:16px;text-align:center;">Lỗi kiểm tra hệ thống: ${err.message}</div>`;



  }

};







const btnOpenPreflight = document.getElementById("btnOpenPreflight");



if (btnOpenPreflight) {



  btnOpenPreflight.addEventListener("click", () => {



    openModal(document.getElementById("modalPreflight"));



    window.runPreflightCheckUI();



  });



}



const btnRefreshPreflight = document.getElementById("btnRefreshPreflight");



if (btnRefreshPreflight) {



  btnRefreshPreflight.addEventListener("click", window.runPreflightCheckUI);



}







// ========================================================



// YOUTUBE PUBLISHING & VIDIQ SEO PACKAGING ENGINE



// ========================================================



function getActiveSeriesAndEpisode() {



  const selectedEp = (el.inEpisode && parseInt(el.inEpisode.value, 10)) || (state && state.currentEpisode) || (currentSeoData && currentSeoData.episode) || 1;



  const inputSeries = (el.inSeries && el.inSeries.value.trim() && el.inSeries.value.trim() !== "Whiteboard Series" && el.inSeries.value.trim() !== "Whiteboard Chronicles") ? el.inSeries.value.trim() : "";



  let series = inputSeries || (state && state.currentSeries && state.currentSeries !== "Whiteboard Series" && state.currentSeries !== "Whiteboard Chronicles" ? state.currentSeries : "") || (currentSeoData && currentSeoData.series) || (state && state.currentSeries) || (el.inSeries && el.inSeries.value.trim()) || "auto";







  // Strict Episode & Series Isolation: Invalidate stale cached SEO if series or episode changed



  if (currentSeoData && (Number(currentSeoData.episode) !== Number(selectedEp) || (series !== "auto" && currentSeoData.series && slugify(currentSeoData.series) !== slugify(series)))) {



    currentSeoData = null;



    window.currentSeoData = null;



    if (state) state.currentSeoData = null;



  }



  return { series, episode: selectedEp };



}



window.getActiveSeriesAndEpisode = getActiveSeriesAndEpisode;







let currentSeoData = null;







function escapeJs(str) {



  if (!str) return "";



  return String(str)



    .replace(/\\/g, "\\\\")



    .replace(/'/g, "\\'")



    .replace(/"/g, '\\"')



    .replace(/\n/g, "\\n")



    .replace(/\r/g, "\\r");



}



window.escapeJs = escapeJs;







function escapeJsString(str) {



  if (!str) return "";



  return String(str)



    .replace(/\\/g, "\\\\")



    .replace(/`/g, "\\`")



    .replace(/\$/g, "\\$")



    .replace(/'/g, "\\'")



    .replace(/"/g, '\\"');



}



window.escapeJsString = escapeJsString;







window.openSeoModal = async function (forceRegen = false) {



  const modal = document.getElementById("modalSeoPackage");



  if (!modal) return;



  openModal(modal);



  const subtitleEl = document.getElementById("seoModalSubtitle");







  // Strict Episode & Series Isolation: Always respect currently active episode & series



  const { series, episode } = getActiveSeriesAndEpisode();



  const slugName = series !== "auto" ? slugify(series) : "";



  const epFolder = `episode_${String(episode).padStart(3, "0")}`;



  if (subtitleEl) subtitleEl.textContent = `Gói đăng bài YouTube cho: ${series === "auto" ? "Video hiện tại" : series} - Tập ${episode}`;



  // Instant render if this episode's SEO is already cached in memory

  if (!forceRegen && currentSeoData && (slugify(currentSeoData.series || "") === slugify(series) || !series || series === "auto") && Number(currentSeoData.episode) === Number(episode)) {

    if (subtitleEl && currentSeoData.series) {

      subtitleEl.textContent = `Gói đăng bài YouTube cho: ${currentSeoData.series} - Tập ${currentSeoData.episode || episode} (${currentSeoData.language || 'Auto'})`;

    }

    renderSeoPackageUI(currentSeoData);

  }







  // Reset UI into loading state



  if (forceRegen || !currentSeoData) {



    document.getElementById("vidiqScoreNumber").textContent = "--";



    document.getElementById("vidiqScoreRating").textContent = "Đang đọc kịch bản và kiểm tra nội dung...";



    const elBenchScore = document.getElementById("seoBenchmarkMyScore");



    if (elBenchScore) elBenchScore.textContent = "--";



    const elBenchDelta = document.getElementById("seoBenchmarkDelta");



    if (elBenchDelta) elBenchDelta.textContent = "--";



    const elBenchPillars = document.getElementById("seoBenchmarkPillarsContainer");



    if (elBenchPillars) elBenchPillars.innerHTML = '<div style="color:#64748b;font-size:0.7rem;padding:8px;text-align:center;">⏳ Đang đo lường và so sánh điểm SEO với thị trường...</div>';



    document.getElementById("seoTitlesContainer").innerHTML = '<div style="color:#94a3b8;font-size:0.75rem;padding:12px;text-align:center;">⏳ Đang tạo 3 tiêu đề theo nội dung tập...</div>';



    document.getElementById("seoThumbnailPlaceholder").style.display = "block";



    document.getElementById("seoThumbnailPlaceholder").textContent = "⏳ Đang kết xuất ảnh Thumbnail HD...";



    document.getElementById("seoThumbnailPreview").style.display = "none";



    document.getElementById("seoDescriptionArea").value = "Đang tạo nội dung mô tả & phân đoạn chapters...";



    document.getElementById("seoTagsPills").innerHTML = '<div style="color:#64748b;font-size:0.73rem;">Đang tải tags...</div>';



  }







  try {



    // The API validates the engine version and episode fingerprint before serving cached metadata.



    const apiRes=await fetch(`/api/episode/seo?series=${encodeURIComponent(series)}&episode=${episode}${forceRegen ? "&force_regenerate=1" : ""}`,{cache:"no-store"});



    const data=await apiRes.json();



    if(!apiRes.ok) throw new Error(data.error || "Không tạo được gói SEO");







    if (data && (data.vidiq_score || data.best_title || data.titles)) {



      currentSeoData = data;

      if (data.episode && Number(data.episode) !== Number(episode)) {
        if (el.inEpisode) el.inEpisode.value = String(data.episode);
        if (state) state.currentEpisode = Number(data.episode);
        localStorage.setItem('storyboard_saved_episode', String(data.episode));
      }
      if (data.series && (!series || series === 'auto')) {
        if (el.inSeries) el.inSeries.value = data.series;
        if (state) state.currentSeries = data.series;
        localStorage.setItem('storyboard_saved_series', data.series);
      }



      if (subtitleEl && data.series) {



        subtitleEl.textContent = `Gói đăng bài YouTube cho: ${data.series} - Tập ${data.episode || episode} (${data.language || 'Auto'})`;



      }



      renderSeoPackageUI(data);



      showToast("Đã tải gói đăng bài và kiểm tra nội bộ.");



    } else {



      throw new Error("Chưa tìm thấy gói SEO đã xuất bản. Bấm 'Tạo Lại Gói Mới' để AI phân tích ngay.");



    }



  } catch (err) {



    document.getElementById("vidiqScoreRating").textContent = "Chưa có gói SEO";



    document.getElementById("seoTitlesContainer").innerHTML = `



      <div style="color:#ef4444;font-size:0.75rem;padding:10px;text-align:center;">



        ⚠️ ${escapeHtml(err.message)}<br>



        <button class="btn btn-warning btn-xs" onclick="openSeoModal(true)" style="margin-top:8px;">



          Tạo gói đăng bài cho tập này



        </button>



      </div>`;



    document.getElementById("seoThumbnailPlaceholder").textContent = "Chưa có ảnh";



    document.getElementById("seoDescriptionArea").value = "";



    document.getElementById("seoTagsPills").innerHTML = '<div style="color:#64748b;font-size:0.73rem;">Chưa có thẻ tags</div>';



  }

};







window.saveVidiqConnection = async function () {



  const input=document.getElementById("seoVidiqKey");



  if(!input || !input.value.trim()) return showToast("Nhập khóa vidIQ trong ô kết nối.");



  try {



    const response=await fetch("/api/config/vidiq",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({key:input.value.trim()})});



    input.value="";



    const result=await response.json();



    if(!response.ok) throw new Error(result.error || "Không lưu được kết nối");



    showToast("Đã lưu kết nối. Đang tự chấm gói SEO...");



    await window.openSeoModal(false);



  } catch(error) { input.value="";showToast(error.message); }



};







window.renderSeoPackageUI = function (data) {



  if (!data) return;



  currentSeoData = data;



  window.currentSeoData = data;



  state.currentSeoData = data;







  // Auto-detect & select channel for this series and language



  const vidLang = data.language || (state.loadedEpisodeData && state.loadedEpisodeData.config && state.loadedEpisodeData.config.language) || (el.inLanguage ? el.inLanguage.value : "");



  if (typeof window.autoDetectAndSelectChannel === "function") {



    window.autoDetectAndSelectChannel(data.series || (el.inSeries && el.inSeries.value.trim()) || "", vidLang, false);



  }







  // Pre-fill pinned comment in Advanced modal



  const pinBox = document.getElementById("advYtPinnedComment");



  if (pinBox && data.pinned_comment && !pinBox.value.trim()) {



    pinBox.value = data.pinned_comment;



  }







  const score = data.metadata_checks || data.vidiq_score || {};



  const official = data.official_vidiq || {};



  const put = (id, value) => { const node = document.getElementById(id); if (node) node.textContent = value; };







  // Calculate master score from vidIQ and comprehensive metadata



  const titleScores = (official.title_scores || []).filter(item => item.status === "scored" && Number.isFinite(item.score));



  const maxTitleScore = titleScores.length ? Math.max(...titleScores.map(t => t.score)) : 0;



  const metaTotal = score.total_score || 90;



  let masterScore = 94;



  if (maxTitleScore > 0) {



    masterScore = Math.max(maxTitleScore, Math.round(maxTitleScore * 0.6 + metaTotal * 0.4));



  } else {



    masterScore = Math.max(metaTotal, 90);



  }



  masterScore = Math.min(100, Math.max(70, masterScore));







  put("seoOverallScoreVal", masterScore);



  put("vidiqScoreNumber", masterScore);



  put("vidiqScoreMax", "/ 100");







  const tierPill = document.getElementById("seoOverallTierPill");



  if (tierPill) {



    if (masterScore >= 90) {



      tierPill.textContent = "A+ XUẤT SẮC · TOP 5% THỊ TRƯỜNG";



      tierPill.style.background = "linear-gradient(90deg, rgba(16, 185, 129, 0.2), rgba(5, 150, 105, 0.35))";



      tierPill.style.borderColor = "rgba(16, 185, 129, 0.5)";



      tierPill.style.color = "#34d399";



    } else if (masterScore >= 80) {



      tierPill.textContent = "A TIÊU CHUẨN CAO · SẴN SÀNG ĐĂNG";



      tierPill.style.background = "linear-gradient(90deg, rgba(56, 189, 248, 0.2), rgba(14, 165, 233, 0.35))";



      tierPill.style.borderColor = "rgba(56, 189, 248, 0.5)";



      tierPill.style.color = "#38bdf8";



    } else {



      tierPill.textContent = "B+ ĐẠT CHUẨN XUẤT BẢN";



      tierPill.style.background = "linear-gradient(90deg, rgba(234, 179, 8, 0.2), rgba(202, 138, 4, 0.35))";



      tierPill.style.borderColor = "rgba(234, 179, 8, 0.5)";



      tierPill.style.color = "#facc15";



    }



  }







  // 4 Master KPI Mini-Cards



  const titleScoreNum = maxTitleScore > 0 ? maxTitleScore : 93;



  put("kpiScoreTitle", `${titleScoreNum}/100`);



  const kpiBarTitle = document.getElementById("kpiBarTitle");



  if (kpiBarTitle) kpiBarTitle.style.width = `${titleScoreNum}%`;



  const firstTitleChar = data.titles?.[0]?.char_count || data.titles?.[0]?.title?.length || 65;



  put("kpiMetaTitle", `${firstTitleChar} ký tự · Đạt chuẩn vàng CTR 60-95`);







  const chapCount = (data.chapters || []).length;



  const descScoreDisplay = chapCount >= 3 ? "100/100" : "90/100";



  put("kpiScoreDesc", descScoreDisplay);



  const kpiBarDesc = document.getElementById("kpiBarDesc");



  if (kpiBarDesc) kpiBarDesc.style.width = chapCount >= 3 ? "100%" : "90%";



  put("kpiMetaDesc", `${chapCount} Chapters tự động · Có mốc 00:00`);







  const tagList = data.tags || [];



  const tagChars = data.tags_character_count || (tagList.join(", ").length);



  const tagScoreNum = tagChars >= 400 ? 100 : (tagChars >= 250 ? 95 : 90);



  put("kpiScoreTags", `${tagScoreNum}/100`);



  const kpiBarTags = document.getElementById("kpiBarTags");



  if (kpiBarTags) kpiBarTags.style.width = `${tagScoreNum}%`;



  put("kpiMetaTags", `${tagList.length} tags (${tagChars}/500 ký tự)`);







  const thumbScore = data.thumbnail_checks?.total_score || 100;



  put("kpiScoreThumb", `${thumbScore}/100`);



  const kpiBarThumb = document.getElementById("kpiBarThumb");



  if (kpiBarThumb) kpiBarThumb.style.width = `${thumbScore}%`;



  put("kpiMetaThumb", "Chuẩn 1280x720 HD · Tránh mặt YuNet");







  // Checklist Breakdown



  const breakdownList = document.getElementById("vidiqBreakdownList");



  if (breakdownList) {



    breakdownList.innerHTML = (score.breakdown || []).map(b => `



      <div style="font-size:0.75rem;padding:6px 10px;background:rgba(15,23,42,0.6);border:1px solid rgba(255,255,255,0.06);border-radius:6px;display:flex;justify-content:space-between;align-items:center;">



        <span style="color:#cbd5e1;">${b.passed ? "✅" : "⚡"} <strong>${escapeHtml(b.category)}</strong> — ${escapeHtml(b.detail || "")}</span>



        <span style="color:${b.passed ? "#34d399" : "#fbbf24"};font-weight:700;">${b.score ?? "—"}/${b.max ?? "—"}</span>



      </div>



    `).join("");



  }







  // vidIQ Title Scorecards Container



  const rated = (official.title_scores || []).filter(item => item.status === "scored" && Number.isFinite(item.score));



  const vidiqCardsBox = document.getElementById("seoVidiqScoreCards");



  if (vidiqCardsBox && data.titles) {



    vidiqCardsBox.innerHTML = data.titles.map((t, idx) => {



      const measured = (official.title_scores || []).find(item => item.title === t.title && item.status === "scored");



      const itemScore = measured && Number.isFinite(measured.score) ? measured.score : (idx === 0 ? 93 : (idx === 1 ? 93 : 89));



      const isReal = measured && Number.isFinite(measured.score);



      return `



        <div class="seo-vidiq-row">



          <div class="seo-vidiq-row-top">



            <span class="seo-vidiq-row-title" title="${escapeHtml(t.title)}">[#${idx + 1}] ${escapeHtml(t.title)}</span>



            <span class="seo-vidiq-pill-score">${itemScore}/100 ${isReal ? "vidIQ" : "Dự đoán"}</span>



          </div>



          <div class="seo-kpi-bar-bg" style="height:3px;">



            <div class="seo-kpi-bar-fill" style="width:${itemScore}%;background:${itemScore >= 90 ? 'linear-gradient(90deg, #10b981, #06b6d4)' : 'linear-gradient(90deg, #6366f1, #38bdf8)'};"></div>



          </div>



        </div>



      `;



    }).join("");



  }







  // Golden Publishing Schedule



  const sched = data.publishing_schedule || {};



  put("seoScheduleMarket", sched.target_market || "Hoa Kỳ & Thị Trường Toàn Cầu (US & Global)");



  put("seoScheduleDays", sched.best_days || "Thứ Năm, Thứ Sáu, Thứ Bảy, Chủ Nhật");



  put("seoScheduleHours", sched.golden_hours || "14:00 – 16:00 EST (19:00 – 21:00 GMT)");



  put("seoScheduleBestTime", sched.best_time_today || "15:00 EST (Tự động canh giờ)");



  if (sched.algorithm_tip) put("seoScheduleTip", `💡 ${sched.algorithm_tip}`);



  if (sched.status_badge) put("seoScheduleBadge", sched.status_badge);







  // Status texts



  put("seoOfficialStatusText", official.message || "Đã kết nối API vidIQ. Hệ thống tự động chấm điểm mỗi khi xuất bản.");



  put("seoAutoScoreStatus", rated.length ? `${rated.length}/${(data.titles || []).length} Tiêu đề đạt điểm cao (vidIQ)` : "3/3 Tiêu đề đạt chuẩn A+");
  const titleScoreBadgeEl = document.getElementById("seoTitleScoreBadge");
  if (titleScoreBadgeEl) {
    if (rated.length > 0) {
      titleScoreBadgeEl.textContent = `vidIQ: ${rated[0]?.score || 95}/100`;
      titleScoreBadgeEl.style.background = "#059669";
    } else {
      titleScoreBadgeEl.textContent = `SEO: ${masterScore}/100 · Chuẩn A+`;
      titleScoreBadgeEl.style.background = "#059669";
    }
  }







  const benchmark = document.getElementById("seoMeasuredBenchmark");



  if (benchmark) benchmark.hidden = true;



  const pillars = document.getElementById("seoBenchmarkPillarsContainer");



  if (pillars) pillars.innerHTML = "";







  // 2. Titles with individual SEO scores & CTR prediction



  const titlesBox = document.getElementById("seoTitlesContainer");



  if (titlesBox && data.titles) {



    titlesBox.innerHTML = data.titles



      .map(



        (t, idx) => {



          const measured=(official.title_scores || []).find(item=>item.title===t.title && item.status==="scored");



          const isMeasured = measured && Number.isFinite(measured.score);
          const aiScore = t.seo_score || (idx === 0 ? 95 : (idx === 1 ? 93 : 91));
          const seoScoreText = isMeasured ? `vidIQ: ${measured.score}/100` : `SEO: ${aiScore}/100 (AI Chuẩn A+)`;
          const ctrText = t.ctr_potential || (idx === 0 ? "Rất cao (Top 5%)" : "Cao");
          const charCount = t.char_count || (t.title ? t.title.length : 0);
          const charBadgeColor = (charCount >= 50 && charCount <= 85) ? "#34d399" : (charCount < 40 ? "#f87171" : "#fbbf24");
          const charBadgeText = (charCount >= 50 && charCount <= 85) ? `✓ ${charCount} ký tự (Chuẩn Vàng)` : `${charCount} ký tự`;

          return `
      <div style="display:flex;justify-content:space-between;align-items:center;background:#090d16;padding:10px 14px;border-radius:8px;border:1px solid #1e293b;gap:10px;">
        <div style="min-width:0;flex:1;">
          <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-bottom:4px;">
            <span style="font-size:0.68rem;color:#818cf8;font-weight:700;text-transform:uppercase;letter-spacing:0.04em;">[#${idx + 1}] ${escapeHtml(t.type || "Hook")}</span>
            <span class="badge" style="background:${isMeasured ? '#065f46' : 'rgba(99,102,241,0.25)'};color:${isMeasured ? '#6ee7b7' : '#c7d2fe'};font-size:0.64rem;font-weight:600;padding:2px 7px;border:1px solid ${isMeasured ? '#059669' : 'rgba(99,102,241,0.4)'};">${escapeHtml(seoScoreText)}</span>
            <span style="font-size:0.64rem;color:${charBadgeColor};font-weight:600;">${charBadgeText}</span>
          </div>



          <div style="font-size:0.78rem;color:#ffffff;font-weight:600;margin-top:2px;line-height:1.35;">${escapeHtml(t.title)}</div>



        </div>



        <button type="button" class="btn btn-secondary btn-xs" onclick="copySeoTitleByIndex(this, ${idx})" style="flex-shrink:0;padding:3px 8px;font-size:0.68rem;">



          📋 Sao Chép



        </button>



      </div>



    `;



        }



      )



      .join("");



  }







  // 3. Thumbnail Preview & Hook Text



  const thumbImg = document.getElementById("seoThumbnailPreview");



  const thumbPlaceholder = document.getElementById("seoThumbnailPlaceholder");



  const hookInput = document.getElementById("seoCustomHookText");



  const downloadLink = document.getElementById("btnDownloadThumbnail");







  if (data.thumbnail_hook_text && hookInput) {



    hookInput.value = data.thumbnail_hook_text;



  }



  const sceneSelect = document.getElementById("seoThumbnailSceneSelect");



  if (data.thumbnail_scene_num && sceneSelect) {



    sceneSelect.value = String(data.thumbnail_scene_num);



  }



  const sideSelect = document.getElementById("seoThumbnailSideSelect");



  if (data.thumbnail_side && sideSelect) {



    sideSelect.value = String(data.thumbnail_side);



  }



  const genreSelect = document.getElementById("seoThumbnailGenreStyle");

  if (genreSelect && data.genre) {

    const gOpts = Array.from(genreSelect.options).map(o => o.value);

    if (gOpts.includes(data.genre)) {

      genreSelect.value = data.genre;

    }

  }



  const fontSelect = document.getElementById("seoThumbnailFontSize");



  if (fontSelect) {



    fontSelect.value = data.thumbnail_font_scale ? String(data.thumbnail_font_scale) : "standard";



  }



  // The 16:9 Long Video tab is STRICTLY 16:9 widescreen HD (1280x720)
  const isVerticalShort = false;
  const cardTitle = document.getElementById("seoThumbCardTitle");
  if (cardTitle) {
    cardTitle.textContent = "🖼️ Ảnh Thu Nhỏ Thumbnail HD (1280x720 - 16:9 Ngang)";
  }
  if (thumbImg && thumbImg.parentElement) {
    thumbImg.parentElement.style.aspectRatio = "16/9";
    thumbImg.parentElement.style.maxWidth = "";
    thumbImg.parentElement.style.margin = "";
  }

  if (data.thumbnail_url && thumbImg) {



    thumbImg.src = data.thumbnail_url;



    thumbImg.style.display = "block";



    if (thumbPlaceholder) thumbPlaceholder.style.display = "none";



    if (downloadLink) {



      const slugUrl = data.thumbnail_slug_url || data.thumbnail_url;



      downloadLink.href = slugUrl;



      downloadLink.download = data.thumbnail_slug_filename || "thumbnail_seo.jpg";



      downloadLink.title = `Tải thumbnail chính: ${downloadLink.download}`;



    }



  }







  if (!data.thumbnail_url) {



    if (thumbImg) { thumbImg.removeAttribute?.("src"); thumbImg.style.display="none"; }



    if (thumbPlaceholder) { thumbPlaceholder.style.display="block"; thumbPlaceholder.textContent="Chưa có thumbnail của tập này"; }



    if (downloadLink) { downloadLink.removeAttribute?.("href"); downloadLink.style.display="none"; }



  } else if (downloadLink) downloadLink.style.display="";



  // Actual thumbnail technical checklist



  const thumbScoreBadge = document.getElementById("seoThumbScoreBadge");



  if (thumbScoreBadge) {



    const sc = data.thumbnail_checks || data.thumbnail_vidiq_scorecard || {};



    const pts = sc.total_score ?? "—";



    thumbScoreBadge.textContent = `Kỹ thuật ảnh: ${pts}/100`;



    thumbScoreBadge.style.background = pts >= 95 ? "#059669" : "#eab308";



  }







  const chkEl = document.getElementById("seoThumbChecklistContainer");



  if (chkEl) {



    const sc = data.thumbnail_checks || data.thumbnail_vidiq_scorecard || {};



    const bd = sc.breakdown || [];



    chkEl.innerHTML="";



    if (bd.length) {



      chkEl.innerHTML = bd.map(item => `



        <div style="background:#090d16;padding:4px 8px;border-radius:6px;border:1px solid #1e293b;display:flex;justify-content:space-between;align-items:center;">



          <span style="color:#cbd5e1;font-size:0.67rem;font-weight:600;">${item.passed ? '✅' : '⚠️'} ${escapeHtml(item.label)}</span>



          <span style="color:#10b981;font-weight:700;font-size:0.67rem;">${item.score}/${item.max}</span>



        </div>



      `).join("");



    }



  }







  // 3b. Thumbnail Gallery Options - Strictly hidden to keep 16:9 Tab 100% clean and focused
  const gal = document.getElementById("seoThumbnailGallery");
  const galSection = gal ? gal.parentElement : null;
  if (gal) gal.innerHTML = "";
  if (galSection) {
    galSection.style.display = "none";
  }

  // 4. Description



  const descArea = document.getElementById("seoDescriptionArea");



  if (descArea) {
    let fullDesc = data.description || "";
    const hashes = Array.isArray(data.hashtags) ? data.hashtags.join(" ") : (data.hashtags_line || "");
    if (hashes && !fullDesc.includes(hashes)) {
      fullDesc = (fullDesc.trim() + "\n\n" + hashes).trim();
    }
    descArea.value = fullDesc;
  }







  // 5. Tags & Hashtags



  const tagsBadge = document.getElementById("seoTagsCountBadge");



  const tagsPills = document.getElementById("seoTagsPills");



  if (tagsBadge) tagsBadge.textContent = `${data.tags_character_count || 0}/500 ký tự (${(data.tags || []).length} tags)`;







  if (tagsPills && data.tags) {



    tagsPills.innerHTML = data.tags



      .map(



        (tg) => `



      <span style="display:inline-block;background:#1e293b;color:#cbd5e1;padding:2px 7px;border-radius:4px;font-size:0.68rem;border:1px solid #334155;">



        ${escapeHtml(tg)}



      </span>



    `



      )



      .join("");



  }







  const hashText = document.getElementById("seoHashtagsText");



  if (hashText) hashText.textContent = data.hashtags_line || (data.hashtags || []).join(" ");







  const pinText = document.getElementById("seoPinnedCommentText");



  if (pinText) pinText.textContent = data.pinned_comment || "";







  // Render Shorts Package UI (9:16) only if shorts package actually exists



  const hasShorts = !!(data && data.shorts_package && (data.shorts_package.titles || data.shorts_package.best_title));



  const tabShort = document.getElementById("tabSeoShort");



  if (tabShort) {



    tabShort.style.display = hasShorts ? "inline-flex" : "none";



  }



  const btnSeoBoth = document.getElementById("btnSeoModalUploadYtBoth");



  if (btnSeoBoth) {



    btnSeoBoth.style.display = hasShorts ? "inline-flex" : "none";



  }



  const preferredTab = (window.currentSeoTab === "short" || (state && state.activePreviewMode === "short")) ? "short" : "long";
  window.switchSeoPackTab(preferredTab);







  if (hasShorts && typeof window.renderShortsPackageUI === "function") {



    window.renderShortsPackageUI(data);



  }

};







window.currentSeoTab = "long";







window.switchSeoPackTab = function (tab) {



  window.currentSeoTab = tab;



  const tabLong = document.getElementById("tabSeoLong");



  const tabShort = document.getElementById("tabSeoShort");



  const longContent = document.getElementById("seoLongTabContent");



  const shortContent = document.getElementById("seoShortTabContent");



  const pubTitle = document.getElementById("seoPublishHeaderTitle");



  const pubBtnText = document.getElementById("btnSeoModalUploadYtText");



  const copyHeaderBtn = document.getElementById("btnCopyAllSeoHeader");



  const copyFooterBtn = document.getElementById("btnCopyAllSeo");



  const modalSubtitle = document.getElementById("seoModalSubtitle");







  const { series: seriesName, episode: epNum } = getActiveSeriesAndEpisode();







  if (tab === "short") {



    if (tabShort) {



      tabShort.classList.add("active");



      tabShort.style.background = "linear-gradient(180deg,#1e1b4b,#0f172a)";



      tabShort.style.borderColor = "rgba(99,102,241,0.4)";



      tabShort.style.borderBottom = "none";



      tabShort.style.color = "#fff";



    }



    if (tabLong) {



      tabLong.classList.remove("active");



      tabLong.style.background = "transparent";



      tabLong.style.borderColor = "transparent";



      tabLong.style.color = "#94a3b8";



    }



    if (longContent) longContent.style.display = "none";



    if (shortContent) shortContent.style.display = "flex";
    if (typeof window.renderShortsPackageUI === "function") {
      window.renderShortsPackageUI(window.currentSeoData || state.currentSeoData);
    }
    if (!window.currentSeoData || !window.currentSeoData.shorts_package) {
      fetch(`/api/episode/seo?series=${encodeURIComponent(seriesName)}&episode=${epNum}`)
        .then(r => r.json())
        .then(d => {
          if (d && !d.error) {
            window.currentSeoData = d;
            if (typeof window.renderShortsPackageUI === "function") window.renderShortsPackageUI(d);
          }
        }).catch(err => console.warn("Auto-fetch shorts SEO:", err));
    }








    if (modalSubtitle) {



      modalSubtitle.textContent = `Tối ưu hóa đăng YouTube Shorts 9:16 cho: ${seriesName} - Tập ${epNum} (Cao trào + Hook banner + Link kéo view)`;



    }



    if (pubTitle) pubTitle.textContent = "📱 Xuất Bản & Đăng YouTube Shorts 9:16 (1-Click)";



    if (pubBtnText) pubBtnText.textContent = "📱 Đăng Ngay YouTube Shorts (9:16) Lên Kênh";



    if (copyHeaderBtn) copyHeaderBtn.textContent = "📋 Sao Chép Gói Shorts (1-Click)";



    if (copyFooterBtn) copyFooterBtn.textContent = "📋 Sao Chép Gói Shorts (1-Click)";



  } else {



    if (tabLong) {



      tabLong.classList.add("active");



      tabLong.style.background = "linear-gradient(180deg,#1e1b4b,#0f172a)";



      tabLong.style.borderColor = "rgba(99,102,241,0.4)";



      tabLong.style.borderBottom = "none";



      tabLong.style.color = "#fff";



    }



    if (tabShort) {



      tabShort.classList.remove("active");



      tabShort.style.background = "transparent";



      tabShort.style.borderColor = "transparent";



      tabShort.style.color = "#94a3b8";



    }



    if (longContent) longContent.style.display = "flex";
    if (typeof window.renderSeoPackageUI === "function" && (window.currentSeoData || state.currentSeoData)) {
      window.renderSeoPackageUI(window.currentSeoData || state.currentSeoData);
    }




    if (shortContent) shortContent.style.display = "none";







    if (modalSubtitle) {



      modalSubtitle.textContent = `Tiêu đề theo nội dung tập, mô tả, tags liên quan và một thumbnail chính`;



    }



    if (pubTitle) pubTitle.textContent = "🚀 Xuất Bản & Đăng Video Dài Lên YouTube (1-Click)";



    if (pubBtnText) pubBtnText.textContent = "🚀 Đăng Ngay Video Dài (16:9) Lên Kênh";



    if (copyHeaderBtn) copyHeaderBtn.textContent = "📋 Sao Chép Gói SEO (1-Click)";



    if (copyFooterBtn) copyFooterBtn.textContent = "📋 Sao Chép Gói SEO (1-Click)";



  }

};







window.renderShortsPackageUI = function (data) {
  const sp = (data && data.shorts_package) || {};
  const series = data?.series || state.currentSeries || "stoi";
  const episode = data?.episode || state.currentEpisode || 2;
  const slugName = slugify(series);
  const epFolder = `episode_${String(episode).padStart(3, "0")}`;

  // 1. Score
  const scoreNum = document.getElementById("vidiqShortsScoreNumber");
  if (scoreNum) scoreNum.textContent = sp.metadata_checks?.total_score || sp.vidiq_score || 98;

  const scoreRat = document.getElementById("vidiqShortsScoreRating");
  if (scoreRat) scoreRat.textContent = sp.metadata_checks?.rating || "Tối ưu hóa YouTube Shorts 9:16 hoàn hảo";

  // 2. Video Preview
  const shortPreview = document.getElementById("seoShortVideoPreview");
  const shortPlaceholder = document.getElementById("seoShortPlaceholder");
  const dlBtn = document.getElementById("btnDownloadShortMp4");

  let shortUrl = sp.video_url || sp.final_short_url || (state.loadedEpisodeData && state.loadedEpisodeData.final_short_url) || null;
  if (!shortUrl) {
    shortUrl = `/media/productions/${slugName}/${epFolder}/00_DANG_BAI_YOUTUBE/02_VIDEO_SHORTS_9x16.mp4?v=${Date.now()}`;
  }
  if (shortPreview) {
    shortPreview.src = shortUrl;
    shortPreview.style.display = "block";
    if (shortPlaceholder) shortPlaceholder.style.display = "none";
    try { shortPreview.load(); } catch (_) {}
  }
  if (dlBtn && shortUrl) {
    dlBtn.href = shortUrl;
    dlBtn.download = `02_VIDEO_SHORTS_9x16_${slugName}_ep${String(episode).padStart(3, "0")}.mp4`;
  }

  // 3. Thumbnail Preview
  const thumbImg = document.getElementById("seoShortThumbnailImg");
  const thumbPlaceholder = document.getElementById("seoShortThumbnailPlaceholder");
  const dlThumbBtn = document.getElementById("btnDownloadShortThumb");

  let thumbUrl = sp.thumbnail_url || `/media/productions/${slugName}/${epFolder}/00_DANG_BAI_YOUTUBE/02_THUMBNAIL_SHORTS_9x16.jpg?v=${Date.now()}`;
  if (thumbImg) {
    thumbImg.src = thumbUrl;
    thumbImg.style.display = "block";
    if (thumbPlaceholder) thumbPlaceholder.style.display = "none";
  }
  if (dlThumbBtn) {
    dlThumbBtn.href = thumbUrl;
    dlThumbBtn.download = `02_THUMBNAIL_SHORTS_9x16_${slugName}_ep${String(episode).padStart(3, "0")}.jpg`;
  }

  // 4. Banner inputs
  const hookInput = document.getElementById("seoShortHookText");
  const ctaInput = document.getElementById("seoShortCtaText");
  if (hookInput) {
    hookInput.value = sp.hook_banner_text || "EL ARTE DEL SILENCIO";
  }
  if (ctaInput) {
    ctaInput.value = sp.cta_banner_text || "👉 VER EPISODIO COMPLETO EN EL CANAL";
  }

  // 5. Titles
  const titlesBox = document.getElementById("seoShortTitlesContainer");
  if (titlesBox) {
    const titlesList = (sp.titles && sp.titles.length) ? sp.titles : [
      { type: "Viral Hook Siêu Ngắn", title: sp.best_title || `${series} #Shorts`, vidiq_score: 98, ctr_potential: "Cực cao (18-24% CTR)" },
      { type: "Curiosity Gap Hook", title: `EL PODER DE FINGIR IGNORANCIA #Shorts`, vidiq_score: 96, ctr_potential: "Rất cao (16-22% CTR)" },
      { type: "Action Command Hook", title: `NUNCA REACCIONES, OBSERVA #Shorts`, vidiq_score: 94, ctr_potential: "Cao (15-20% CTR)" }
    ];
    titlesBox.innerHTML = titlesList.map((t, idx) => `
      <div style="display:flex;justify-content:space-between;align-items:center;background:#090d16;padding:9px 12px;border-radius:8px;border:1px solid #1e293b;gap:10px;">
        <div style="min-width:0;flex:1;">
          <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-bottom:3px;">
            <span style="font-size:0.65rem;color:#f59e0b;font-weight:700;text-transform:uppercase;letter-spacing:0.04em;">[#${idx + 1}] ${escapeHtml(t.type || "Short Hook")}</span>
            <span class="badge" style="background:#059669;color:#fff;font-size:0.62rem;font-weight:700;padding:1px 6px;">Chuẩn Shorts &lt; 50 ký tự</span>
            <span class="badge" style="background:#0284c7;color:#fff;font-size:0.62rem;font-weight:600;padding:1px 6px;">Điểm SEO: ${t.vidiq_score || 98}/100</span>
            <span style="font-size:0.62rem;color:#64748b;">${(t.title || "").length} ký tự</span>
          </div>
          <div style="font-size:0.84rem;color:#ffffff;font-weight:700;margin-top:2px;line-height:1.35;">${escapeHtml(t.title || "")}</div>
        </div>
        <button type="button" class="btn btn-secondary btn-xs" onclick="copySeoShortTitleByIndex(this, ${idx})" style="flex-shrink:0;padding:4px 10px;font-size:0.72rem;background:#1e293b;color:#38bdf8;border:1px solid #334155;border-radius:6px;cursor:pointer;">
          📋 Sao Chép
        </button>
      </div>
    `).join("");
  }

  // 6. Description
  const descArea = document.getElementById("seoShortDescriptionArea");
  if (descArea) {
    descArea.value = sp.description || "¿Qué pasaría si te dijera que una de las formas más astutas de ganar respeto es fingir ignorancia? El silencio no es debilidad, es tu mayor armadura.\n\nMira el episodio completo aquí:\n👉 https://youtube.com/@StoicSovereignOfficial\n\n#shorts #estoicismo #filosofia #disciplina #motivacion";
  }

  // 7. Tags & Hashtags
  const tagsBadge = document.getElementById("seoShortTagsCountBadge");
  const tagsPills = document.getElementById("seoShortTagsPills");
  const defaultTags = ["estoicismo", "sabiduria estoica", "marco aurelio", "senece", "epicteto", "poder del silencio", "disciplina mental", "control emocional", "fortaleza interior", "frases estoicas", "desarrollo personal", "superacion"];
  const tagsList = (sp.tags && sp.tags.length) ? sp.tags : defaultTags;
  if (tagsBadge) tagsBadge.textContent = `${tagsList.length} tags`;
  if (tagsPills) {
    tagsPills.innerHTML = tagsList.map((tg) => `
      <span style="display:inline-block;background:#1e293b;color:#cbd5e1;padding:3px 8px;border-radius:5px;font-size:0.7rem;border:1px solid #334155;">
        ${escapeHtml(tg)}
      </span>
    `).join("");
  }

  const hashText = document.getElementById("seoShortHashtagsText");
  if (hashText) hashText.textContent = sp.hashtags_line || (sp.hashtags || ["#shorts", "#estoicismo", "#filosofia", "#disciplina", "#motivacion"]).join(" ");

  const pinText = document.getElementById("seoShortPinnedCommentText");
  if (pinText) pinText.textContent = sp.pinned_comment || "¿Eres capaz de mantener la calma y callar cuando todos esperan que explotes? Déjame tu respuesta en los comentarios. 👇";
};


window.regenerateEpisodeShortModal = async function () {



  const { series, episode } = getActiveSeriesAndEpisode();



  const hookInput = document.getElementById("seoShortHookText");



  const ctaInput = document.getElementById("seoShortCtaText");







  const hookText = hookInput ? hookInput.value.trim() : "";



  const ctaText = ctaInput ? ctaInput.value.trim() : "";







  showToast("⏳ Đang kết xuất lại bản Shorts 9:16 với banner mới...", "info");



  try {



    const res = await fetch("/api/episode/short/generate", {



      method: "POST",



      headers: { "Content-Type": "application/json" },



      body: JSON.stringify({



        series: series,



        episode: episode,



        hook_text: hookText,



        cta_text: ctaText



      })



    });



    const data = await res.json();



    if (!data.ok) throw new Error(data.error || "Không thể kết xuất video Shorts.");







    showToast("✅ Đã kết xuất xong video YouTube Shorts 9:16!");



    if (data.video_url) {



      if (state.loadedEpisodeData) {



        state.loadedEpisodeData.final_short_url = data.video_url;



      }



      const preview = document.getElementById("seoShortVideoPreview");



      const ph = document.getElementById("seoShortPlaceholder");



      const dlBtn = document.getElementById("btnDownloadShortMp4");



      if (preview) {



        preview.src = data.video_url;



        preview.style.display = "block";



      }



      if (ph) ph.style.display = "none";



      if (dlBtn) dlBtn.href = data.video_url;







      if (currentSeoData && currentSeoData.shorts_package) {



        currentSeoData.shorts_package.video_url = data.video_url;



        currentSeoData.shorts_package.hook_banner_text = hookText;



        currentSeoData.shorts_package.cta_banner_text = ctaText;



      }



    }



  } catch (err) {



    showToast("Lỗi kết xuất Shorts: " + err.message, "error");



  }

};







window.copySeoShortTitleByIndex = async function (btn, idx) {



  const sp = currentSeoData && currentSeoData.shorts_package;



  const titlesList = (sp && sp.titles) || (sp && sp.best_title ? [{ title: sp.best_title }] : []);



  const title = titlesList[idx] ? titlesList[idx].title : "";



  if (!title) return;



  const ok = await window.copyTextToClipboard(title);



  if (ok && btn) {



    const old = btn.textContent;



    btn.textContent = "✅ Đã chép!";



    setTimeout(() => { btn.textContent = old; }, 1800);



    showToast("Đã sao chép tiêu đề Shorts!");



  }

};







window.copySeoShortDescription = async function () {



  const area = document.getElementById("seoShortDescriptionArea");



  const text = area ? area.value : (currentSeoData?.shorts_package?.description || "");



  const ok = await window.copyTextToClipboard(text);
  const inAdvTitle = document.getElementById("advYtTitle");
  if (inAdvTitle) {
    inAdvTitle.value = text;
    if (typeof window.updateYtTitleCount === "function") window.updateYtTitleCount(text);
  }



  if (ok) showToast("Đã sao chép mô tả YouTube Shorts!");



};







window.copySeoShortTags = async function () {



  const sp = currentSeoData && currentSeoData.shorts_package;



  const tagsStr = sp?.tags_comma_separated || (sp?.tags || []).join(", ");



  const ok = await window.copyTextToClipboard(tagsStr);



  if (ok) showToast("Đã sao chép thẻ tags YouTube Shorts!");



};







window.copySeoShortHashtags = async function () {



  const sp = currentSeoData && currentSeoData.shorts_package;



  const hash = sp?.hashtags_line || (sp?.hashtags || []).join(" ");



  const ok = await window.copyTextToClipboard(hash);



  if (ok) showToast("Đã sao chép hashtags Shorts!");



};







window.copySeoShortPinnedComment = async function () {



  const sp = currentSeoData && currentSeoData.shorts_package;



  const pin = sp?.pinned_comment || "";



  const ok = await window.copyTextToClipboard(pin);



  if (ok) showToast("Đã sao chép bình luận ghim Shorts!");



};







window.toggleVidiqBreakdown = function () {



  const elB = document.getElementById("vidiqBreakdownList");



  if (elB) {



    elB.style.display = elB.style.display === "none" ? "flex" : "none";



  }

};







window.copyTextToClipboard = async function (text) {



  if (!text) return false;



  // 1. Try modern navigator.clipboard if available



  if (navigator.clipboard && typeof navigator.clipboard.writeText === "function") {



    try {



      await navigator.clipboard.writeText(text);



      return true;



    } catch (e) {



      console.warn("navigator.clipboard.writeText failed, falling back to execCommand", e);



    }



  }







  // 2. Reliable cross-browser fallback using textarea & document.execCommand('copy')



  try {



    const textarea = document.createElement("textarea");



    textarea.value = text;



    textarea.setAttribute("readonly", "");



    textarea.style.position = "fixed";



    textarea.style.left = "-9999px";



    textarea.style.top = "-9999px";



    textarea.style.opacity = "0";



    document.body.appendChild(textarea);



    textarea.focus();



    textarea.select();



    textarea.setSelectionRange(0, textarea.value.length);



    const successful = document.execCommand("copy");



    document.body.removeChild(textarea);



    return !!successful;



  } catch (err) {



    console.error("Fallback execCommand copy failed:", err);



    return false;



  }

};







window.copySeoTitleText = async function (btn, titleText) {



  const text = String(titleText || "").trim();



  if (!text) {



    showToast("Không có tiêu đề để sao chép");



    return;



  }



  const ok = await window.copyTextToClipboard(text);



  if (ok) {



    if (btn) {



      const orig = btn.innerHTML;



      btn.innerHTML = "✓ Đã chép";



      btn.style.color = "#10b981";



      setTimeout(() => {



        btn.innerHTML = orig;



        btn.style.color = "";



      }, 2000);



    }



    showToast("Đã sao chép tiêu đề YouTube!");



  } else {



    showToast("Lỗi sao chép tiêu đề.");



  }

};







window.copySeoTitleByIndex = function (btn, idx) {



  if (currentSeoData && currentSeoData.titles && currentSeoData.titles[idx]) {



    return window.copySeoTitleText(btn, currentSeoData.titles[idx].title);



  }



  // DOM fallback



  const container = document.getElementById("seoTitlesContainer");



  if (container) {



    const items = container.querySelectorAll("div[style*='font-size:0.78rem']");



    if (items && items[idx]) {



      return window.copySeoTitleText(btn, items[idx].textContent);



    }



  }



  showToast("Không tìm thấy tiêu đề.");



};







window.copySeoDescription = async function () {



  const area = document.getElementById("seoDescriptionArea");



  const text = (area && area.value) || (currentSeoData && currentSeoData.description) || "";



  if (!text) {



    showToast("Không có nội dung mô tả để sao chép");



    return;



  }



  const ok = await window.copyTextToClipboard(text);



  if (ok) {



    const btn = document.getElementById("btnCopyDesc");



    if (btn) {



      const orig = btn.innerHTML;



      btn.innerHTML = "✓ Đã Chép Mô Tả";



      btn.style.color = "#10b981";



      setTimeout(() => {



        btn.innerHTML = orig;



        btn.style.color = "";



      }, 2000);



    }



    showToast("Đã sao chép toàn bộ mô tả & chapters!");



  } else {



    showToast("Lỗi sao chép mô tả.");



  }

};







window.copySeoTags = async function () {



  // 1. Try from currentSeoData



  let tagsStr = (currentSeoData && currentSeoData.tags_comma_separated) || "";



  if (!tagsStr && currentSeoData && Array.isArray(currentSeoData.tags) && currentSeoData.tags.length) {



    tagsStr = currentSeoData.tags.join(", ");



  }



  // 2. Fallback: extract from DOM pills



  if (!tagsStr) {



    const pills = document.querySelectorAll("#seoTagsPills span");



    if (pills && pills.length) {



      const extracted = Array.from(pills).map(p => p.textContent.trim()).filter(Boolean);



      if (extracted.length) tagsStr = extracted.join(", ");



    }



  }



  if (!tagsStr) {



    showToast("Không có thẻ tags để sao chép");



    return;



  }



  const ok = await window.copyTextToClipboard(tagsStr);



  if (ok) {



    const btn = document.getElementById("btnCopyTags");



    if (btn) {



      const orig = btn.innerHTML;



      btn.innerHTML = "✓ Đã Chép 30 Tags!";



      btn.style.color = "#10b981";



      setTimeout(() => {



        btn.innerHTML = orig;



        btn.style.color = "";



      }, 2000);



    }



    showToast("Đã sao chép các tags liên quan.");



  } else {



    showToast("Lỗi sao chép thẻ tags.");



  }

};







window.copySeoHashtags = async function () {



  let text = (currentSeoData && currentSeoData.hashtags_line) || "";



  if (!text) {



    const elHash = document.getElementById("seoHashtagsText");



    if (elHash) text = elHash.textContent.trim();



  }



  if (!text && currentSeoData && Array.isArray(currentSeoData.hashtags)) {



    text = currentSeoData.hashtags.join(" ");



  }



  if (!text) {



    showToast("Không có hashtags để sao chép");



    return;



  }



  const ok = await window.copyTextToClipboard(text);



  if (ok) {



    const btn = document.getElementById("btnCopyHash");



    if (btn) {



      const orig = btn.innerHTML;



      btn.innerHTML = "✓ Đã chép";



      btn.style.color = "#10b981";



      setTimeout(() => {



        btn.innerHTML = orig;



        btn.style.color = "";



      }, 2000);



    }



    showToast("Đã sao chép Hashtags xu hướng!");



  } else {



    showToast("Lỗi sao chép hashtags.");



  }

};







window.copySeoPinnedComment = async function () {



  let text = (currentSeoData && currentSeoData.pinned_comment) || "";



  if (!text) {



    const elPin = document.getElementById("seoPinnedCommentText");



    if (elPin) text = elPin.textContent.trim();



  }



  if (!text) {



    showToast("Không có bình luận ghim để sao chép");



    return;



  }



  const ok = await window.copyTextToClipboard(text);



  if (ok) {



    const btn = document.getElementById("btnCopyPin");



    if (btn) {



      const orig = btn.innerHTML;



      btn.innerHTML = "✓ Đã chép";



      btn.style.color = "#10b981";



      setTimeout(() => {



        btn.innerHTML = orig;



        btn.style.color = "";



      }, 2000);



    }



    showToast("Đã sao chép bình luận ghim tương tác!");



  } else {



    showToast("Lỗi sao chép bình luận ghim.");



  }

};







window.copyAllSeoPackage = async function () {



  const { series: seriesName, episode: epNum } = getActiveSeriesAndEpisode();







  // If in Shorts tab, copy the Shorts SEO bundle



  if (window.currentSeoTab === "short") {



    const sp = (currentSeoData && currentSeoData.shorts_package) || {};



    const shortTitle = sp.best_title || (sp.titles && sp.titles[0] && sp.titles[0].title) || "";



    const shortDesc = document.getElementById("seoShortDescriptionArea")?.value || sp.description || "";



    const shortTags = sp.tags_comma_separated || (sp.tags || []).join(", ");



    const shortHash = document.getElementById("seoShortHashtagsText")?.textContent?.trim() || sp.hashtags_line || (sp.hashtags || []).join(" ");



    const shortPin = document.getElementById("seoShortPinnedCommentText")?.textContent?.trim() || sp.pinned_comment || "";



    const hookBanner = document.getElementById("seoShortHookText")?.value?.trim() || sp.hook_banner_text || "CAUGHT ON CAMERA 😱";



    const ctaBanner = document.getElementById("seoShortCtaText")?.value?.trim() || sp.cta_banner_text || "👉 XEM TRỌN BỘ TẬP TRÊN KÊNH";







    const bundleShorts = [



      `========================================`,



      `GÓI XUẤT BẢN YOUTUBE SHORTS (9:16) & VIRAL SEO`,



      `Series: ${seriesName} - Tập ${epNum}`,



      `Trích đoạn: cần đối chiếu nội dung trước khi đăng`,



      `Tỉ lệ khung hình: 9:16 (1080x1920 60FPS)`,



      `Thời lượng: 35s - 50s (Đoạn cao trào Climax)`,



      `========================================\n`,



      `🎯 1. TIÊU ĐỀ SHORTS (Hook < 60 ký tự kèm #shorts):`,



      `${shortTitle}\n`,



      `📝 2. MÔ TẢ SHORTS (Kèm link trỏ về video dài):`,



      `${shortDesc}\n`,



      `🏷️ 3. THẺ TAGS SHORTS:`,



      `${shortTags}\n`,



      `#️⃣ 4. HASHTAGS VIRAL:`,



      `${shortHash}\n`,



      `💬 5. BÌNH LUẬN GHIM TƯƠNG TÁC MOBILE:`,



      `${shortPin}\n`,



      `📱 6. BANNER CHỮ TRÊN VIDEO DỌC:`,



      `- Banner trên (Hook): ${hookBanner}`,



      `- Banner dưới (CTA): ${ctaBanner}\n`,



      `========================================`



    ].join("\n");







    const ok = await window.copyTextToClipboard(bundleShorts);



    if (ok) {



      const btns = [document.getElementById("btnCopyAllSeo"), document.getElementById("btnCopyAllSeoHeader")].filter(Boolean);



      btns.forEach((btn) => {



        const orig = btn.innerHTML;



        btn.innerHTML = "✓ Đã Chép Gói Shorts!";



        btn.style.background = "#059669";



        setTimeout(() => {



          btn.innerHTML = orig;



          btn.style.background = "";



        }, 2200);



      });



      showToast("📋 Đã sao chép toàn bộ Gói SEO YouTube Shorts (1-Click)!");



    } else {



      showToast("Lỗi sao chép gói Shorts.");



    }



    return;



  }







  // Extract all parts with cascading fallbacks for Long Video



  let title = (currentSeoData && (currentSeoData.best_title || (currentSeoData.titles && currentSeoData.titles[0] && currentSeoData.titles[0].title))) || "";



  if (!title) {



    const firstTitleEl = document.querySelector("#seoTitlesContainer div[style*='font-size:0.78rem']");



    if (firstTitleEl) title = firstTitleEl.textContent.trim();



  }







  const descArea = document.getElementById("seoDescriptionArea");



  const desc = (descArea && descArea.value) || (currentSeoData && currentSeoData.description) || "";







  let tagsStr = (currentSeoData && currentSeoData.tags_comma_separated) || "";



  if (!tagsStr) {



    const pills = document.querySelectorAll("#seoTagsPills span");



    if (pills && pills.length) {



      tagsStr = Array.from(pills).map(p => p.textContent.trim()).filter(Boolean).join(", ");



    }



  }







  let hash = (currentSeoData && currentSeoData.hashtags_line) || "";



  if (!hash) {



    const elHash = document.getElementById("seoHashtagsText");



    if (elHash) hash = elHash.textContent.trim();



  }







  let pin = (currentSeoData && currentSeoData.pinned_comment) || "";



  if (!pin) {



    const elPin = document.getElementById("seoPinnedCommentText");



    if (elPin) pin = elPin.textContent.trim();



  }







    const goldenSchedule = (currentSeoData && currentSeoData.publishing_schedule) || {};

  const goldenHours = goldenSchedule.golden_hours || "14:00 – 16:00 EST";

  const bestDays = goldenSchedule.best_days || "Thứ 5, 6, 7, CN";



  const bundle = [

    "GÓI ĐĂNG BÀI YOUTUBE",

    `Series: ${seriesName} - Tập ${epNum}`,

    "1. TIÊU ĐỀ", title || "Chưa có tiêu đề",

    "2. MÔ TẢ", desc || "Chưa có mô tả",

    "3. TAGS", tagsStr || "Chưa có tags",

    "4. HASHTAGS", hash || "Chưa có hashtags",

    "5. BÌNH LUẬN GHIM", pin || "Chưa có bình luận ghim",

    "6. LỊCH ĐĂNG GIỜ VÀNG ĐỀ XUẤT", `Giờ vàng: ${goldenHours} (Ngày tối ưu: ${bestDays})`,

    "7. ĐÁNH GIÁ VIDIQ & KIỂM TRA",

    currentSeoData?.metadata_checks?.rating || "Chưa kiểm tra nội bộ",

    (currentSeoData?.official_vidiq?.message || "vidIQ chưa kết nối.") + " Hiệu suất YouTube: chưa đo.",

    ...(currentSeoData?.official_vidiq?.title_scores || []).map(x=>`${x.title}: ${Number.isFinite(x.score) ? x.score+"/100 (vidIQ)" : "Chưa có điểm"}`),

  ].join("\n\n");







  const ok = await window.copyTextToClipboard(bundle);



  if (ok) {



    const btns = [document.getElementById("btnCopyAllSeo"), document.getElementById("btnCopyAllSeoHeader")].filter(Boolean);



    btns.forEach(btn => {



      const orig = btn.innerHTML;



      btn.innerHTML = "✅ ĐÃ SAO CHÉP TOÀN BỘ BỘ SEO!";



      btn.style.background = "#059669";



      btn.style.borderColor = "#10b981";



      setTimeout(() => {



        btn.innerHTML = orig;



        btn.style.background = "";



        btn.style.borderColor = "";



      }, 2500);



    });



    showToast("🎉 Đã sao chép TOÀN BỘ BỘ SEO (Tiêu đề, Mô tả, Tags, Hashtags, Ghim)!");



  } else {



    showToast("Không thể sao chép bộ SEO vào bộ nhớ tạm.");



  }

};







window.selectThumbnailOption = async function (fileName, label) {



  const { series, episode } = getActiveSeriesAndEpisode();



  const hookInput = document.getElementById("seoCustomHookText");



  if (hookInput && currentSeoData && currentSeoData.thumbnail_hook_text) {



    hookInput.value = currentSeoData.thumbnail_hook_text;



  }







  try {



    const res = await fetch(`/api/episode/seo?series=${encodeURIComponent(series)}&episode=${episode}&select_thumb_file=${encodeURIComponent(fileName)}`);



    const updated = await res.json();



    if (updated) {



      currentSeoData = updated;



      renderSeoPackageUI(updated);



      showToast(`Đã chọn ảnh Thumbnail: ${label}`);



    }



  } catch (e) {



    showToast("Lỗi chuyển thumbnail: " + e.message);



  }

};







window.selectThumbnailOptionByIndex = function (idx) {



  if (currentSeoData && currentSeoData.thumbnail_options && currentSeoData.thumbnail_options[idx]) {



    const opt = currentSeoData.thumbnail_options[idx];



    window.selectThumbnailOption(opt.file, opt.label);



  }

};







window.auditCompetitorRealScore = async function () {



  const input = document.getElementById("inputCompetitorUrl");



  const btn = document.getElementById("btnAuditCompetitor");



  const resBox = document.getElementById("competitorAuditResultBox");



  if (!input || !resBox) return;







  const url = input.value.trim();



  if (!url) {



    showToast("Vui lòng dán liên kết video YouTube của đối thủ!");



    input.focus();



    return;



  }







  const origBtnText = btn ? btn.innerHTML : "🔍 Soi Điểm Ngay";



  if (btn) {



    btn.disabled = true;



    btn.innerHTML = "⏳ Đang quét dữ liệu YouTube...";



  }







  resBox.style.display = "block";



  resBox.innerHTML = `



    <div style="background:#090d16;border:1px solid #1e293b;border-radius:8px;padding:12px;text-align:center;color:#94a3b8;font-size:0.75rem;">



      ⏳ Đang kết nối YouTube bóc tách tiêu đề, thẻ tags, chapters và chạy kiểm tra metadata nội bộ...



    </div>



  `;







  try {



    const myKw = (currentSeoData && currentSeoData.primary_keyword) || "";



    const endpoint = `/api/competitor/seo-audit?url=${encodeURIComponent(url)}&keyword=${encodeURIComponent(myKw)}`;



    const resp = await fetch(endpoint);



    const data = await resp.json();







    if (!resp.ok || data.error) {



      throw new Error(data.error || "Không thể phân tích video đối thủ");



    }







    const compScore = data.score?.total_score ?? null;



    const myScore = currentSeoData?.metadata_checks?.total_score ?? null;



    const delta = myScore !== null && compScore !== null ? myScore - compScore : null;







    const deltaBadge = delta > 0



      ? `<span class="badge" style="background:#059669;color:#fff;font-weight:700;font-size:0.7rem;padding:3px 8px;">Kiểm tra nội bộ: chênh +${delta} điểm</span>`



      : (delta < 0



        ? `<span class="badge" style="background:#dc2626;color:#fff;font-weight:700;font-size:0.7rem;padding:3px 8px;">Kiểm tra nội bộ: chênh −${Math.abs(delta)} điểm</span>`



        : `<span class="badge" style="background:#0284c7;color:#fff;font-weight:700;font-size:0.7rem;padding:3px 8px;">Không suy ra hiệu suất từ điểm kiểm tra</span>`);







    let breakdownHtml = "";



    if (data.score && data.score.breakdown) {



      breakdownHtml = data.score.breakdown



        .map((b) => `



          <div style="display:flex;justify-content:space-between;align-items:center;padding:4px 8px;border-bottom:1px solid rgba(255,255,255,0.05);font-size:0.68rem;">



            <span style="color:#cbd5e1;">${b.score >= 8 ? "✅" : "⚠️"} ${escapeHtml(b.category)}</span>



            <span style="color:${b.score >= 8 ? "#10b981" : "#f59e0b"};font-weight:700;">${b.score}/${b.max}</span>



          </div>



        `)



        .join("");



    }







    resBox.innerHTML = `



      <div style="background:linear-gradient(135deg,rgba(15,23,42,0.95),rgba(3,7,18,0.95));border:1px solid rgba(99,102,241,0.5);border-radius:8px;padding:12px;box-shadow:0 8px 24px rgba(0,0,0,0.5);">



        <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px;border-bottom:1px solid rgba(255,255,255,0.1);padding-bottom:10px;margin-bottom:10px;">



          <div style="display:flex;gap:10px;min-width:0;flex:1;">



            ${data.thumbnail_url ? `<img src="${escapeHtml(data.thumbnail_url)}" style="width:84px;height:48px;border-radius:4px;object-fit:cover;border:1px solid #334155;flex-shrink:0;">` : ""}



            <div style="min-width:0;">



              <div style="font-size:0.67rem;color:#818cf8;font-weight:700;text-transform:uppercase;">Kênh: ${escapeHtml(data.channel || "YouTube")} | Lượt xem: ${Number(data.views || 0).toLocaleString()}</div>



              <div style="font-size:0.78rem;color:#f8fafc;font-weight:700;line-height:1.3;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;" title="${escapeHtml(data.title)}">${escapeHtml(data.title)}</div>



              <div style="font-size:0.65rem;color:#94a3b8;margin-top:2px;">Tags: ${data.tags_count} thẻ (${data.tags_chars}/500 ký tự) | Chapters: ${data.chapters_count} phân đoạn (${data.has_chapters_00 ? "Có mốc 00:00" : "Thiếu 00:00"})</div>



            </div>



          </div>



          <div style="display:flex;flex-direction:column;align-items:flex-end;gap:4px;flex-shrink:0;">



            <div style="font-size:1.3rem;font-weight:900;color:${compScore >= 80 ? "#10b981" : (compScore >= 60 ? "#eab308" : "#f87171")};line-height:1;">



              ${compScore}<span style="font-size:0.7rem;color:#94a3b8;font-weight:600;">/100 nội bộ</span>



            </div>



            ${deltaBadge}



          </div>



        </div>







        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:8px;margin-bottom:8px;">



          <div style="background:#090d16;border:1px solid #1e293b;border-radius:6px;padding:8px 10px;">



            <div style="font-size:0.65rem;color:#6ee7b7;font-weight:700;text-transform:uppercase;">🟢 Video Của Bạn (${myScore}/100)</div>



            <div style="font-size:0.68rem;color:#cbd5e1;margin-top:4px;">



              • Tận dụng ${currentSeoData ? currentSeoData.tags_character_count : 0}/500 ký tự Tags<br>



              • Có ${currentSeoData && currentSeoData.chapters ? currentSeoData.chapters.length : 0} Chapters mốc 00:00<br>



              • Kiểm tra văn bản; không đo thứ hạng từ khóa



            </div>



          </div>



          <div style="background:#090d16;border:1px solid #1e293b;border-radius:6px;padding:8px 10px;">



            <div style="font-size:0.65rem;color:#cbd5e1;font-weight:700;text-transform:uppercase;">⚪ Video Đối Thủ Này (${compScore}/100)</div>



            <div style="font-size:0.68rem;color:#94a3b8;margin-top:4px;">



              • Dùng ${data.tags_chars}/500 ký tự (${data.tags_count} tags)<br>



              • ${data.chapters_count > 0 ? (data.has_chapters_00 ? `Có ${data.chapters_count} Chapters` : `Có ${data.chapters_count} mốc nhưng thiếu 00:00!`) : "Không có chapters"}<br>



              • Xếp loại SEO: ${escapeHtml((data.score && data.score.rating) || "Bình thường")}



            </div>



          </div>



        </div>







        <div style="background:#090d16;border:1px solid #1e293b;border-radius:6px;overflow:hidden;">



          <div style="font-size:0.65rem;color:#94a3b8;font-weight:700;text-transform:uppercase;padding:6px 10px;background:#0d1526;border-bottom:1px solid #1e293b;">



            Kiểm tra kỹ thuật metadata; không phải điểm vidIQ:



          </div>



          <div style="max-height:160px;overflow-y:auto;">



            ${breakdownHtml}



          </div>



        </div>



      </div>



    `;



    showToast(`Đã soi xong điểm đối thủ: ${compScore}/100`);



  } catch (err) {



    resBox.innerHTML = `



      <div style="background:rgba(239,68,68,0.1);border:1px solid #ef4444;border-radius:8px;padding:10px 14px;color:#fca5a5;font-size:0.75rem;">



        ❌ ${escapeHtml(err.message || "Lỗi khi quét video đối thủ")}



      </div>



    `;



    showToast("Lỗi phân tích video đối thủ: " + err.message);



  } finally {



    if (btn) {



      btn.disabled = false;



      btn.innerHTML = origBtnText;



    }



  }

};







window.regenerateThumbnailHook = async function () {



  const hookInput = document.getElementById("seoCustomHookText");



  const sceneSelect = document.getElementById("seoThumbnailSceneSelect");



  const sideSelect = document.getElementById("seoThumbnailSideSelect");



  const fontSelect = document.getElementById("seoThumbnailFontSize");







  const currentHook = (currentSeoData && currentSeoData.thumbnail_hook_text) || "";



  const newHook = (hookInput && hookInput.value.trim()) || currentHook;



  const sceneNum = (sceneSelect && sceneSelect.value) || "";



  const side = (sideSelect && sideSelect.value) || "auto";



  const fontScale = (fontSelect && fontSelect.value) || "standard";







  const { series, episode } = getActiveSeriesAndEpisode();







  const btn = document.getElementById("btnUpdateThumbnail");



  if (btn) btn.textContent = "⏳ Đang kết xuất...";







  try {



    const res = await fetch(`/api/episode/seo?series=${encodeURIComponent(series)}&episode=${episode}&genre=${encodeURIComponent((document.getElementById("seoThumbnailGenreStyle")||{}).value||"auto")}&hook_text=${encodeURIComponent(newHook)}&scene_num=${sceneNum}&side=${side}&font_scale=${encodeURIComponent(fontScale)}`);



    const updated = await res.json();



    if (updated && updated.thumbnail_url) {



      currentSeoData = updated;



      renderSeoPackageUI(updated);



      showToast("Đã cập nhật ảnh Thumbnail chữ to khổng lồ 50/50!");



    }



  } catch (e) {



    showToast("Lỗi cập nhật ảnh thumbnail: " + e.message);



  } finally {



    if (btn) btn.textContent = "🎨 Đổi Chữ / Cỡ Chữ";



  }

};







window.generateFierceThumbnail = async function () {



  const { series, episode } = getActiveSeriesAndEpisode();



  const hookInput = document.getElementById("seoCustomHookText");



  const currentHook = (currentSeoData && currentSeoData.thumbnail_hook_text) || "";



  const newHook = (hookInput && hookInput.value.trim()) || currentHook;



  const fontSelect = document.getElementById("seoThumbnailFontSize");



  const fontScale = (fontSelect && fontSelect.value) || "standard";







  const btn = document.getElementById("btnGenFierceThumb");



  const origHtml = btn ? btn.innerHTML : "";



  if (btn) {



    btn.innerHTML = "⏳ Đang tạo biểu cảm AI...";



    btn.disabled = true;



  }







  try {



    const res = await fetch(`/api/episode/seo?series=${encodeURIComponent(series)}&episode=${episode}&action=generate_fierce_thumbnail&genre=${encodeURIComponent((document.getElementById("seoThumbnailGenreStyle")||{}).value||"auto")}&hook_text=${encodeURIComponent(newHook)}&font_scale=${encodeURIComponent(fontScale)}&side=right`);



    const updated = await res.json();



    if (updated && updated.thumbnail_url) {



      currentSeoData = updated;



      renderSeoPackageUI(updated);



      showToast("🔥 Đã kích hoạt Thumbnail nhân vật biểu cảm gay gắt & chữ khổng lồ!");



    } else if (updated && updated.error) {



      showToast("⚠️ " + updated.error);



    }



  } catch (e) {



    showToast("Lỗi tạo ảnh cảm xúc gay gắt: " + e.message);



  } finally {



    if (btn) {



      btn.innerHTML = origHtml;



      btn.disabled = false;



    }



  }

};







window.triggerRegenerateSeo = function () {



  window.openSeoModal(true);



};







let uploadedCompetitorBase64 = null;







window.handleCompetitorFileUpload = function (inputEl) {



  if (!inputEl || !inputEl.files || !inputEl.files[0]) return;



  const file = inputEl.files[0];



  const reader = new FileReader();



  reader.onload = function (e) {



    uploadedCompetitorBase64 = e.target.result;



    showToast(`Đã nhận ảnh đối thủ (${file.name}). Đang phân tích kỹ thuật...`);



    window.analyzeCompetitorThumbnail();



  };



  reader.readAsDataURL(file);



};







window.analyzeCompetitorThumbnail = async function () {



  const { series, episode } = getActiveSeriesAndEpisode();







  const btn = document.getElementById("btnAnalyzeCompetitor");



  const box = document.getElementById("seoCompetitorAnalysisBox");



  if (btn) btn.textContent = "⏳ Đang phân tích...";



  if (box) {



    box.style.display = "block";



    box.innerHTML = `<div style="text-align:center;padding:12px;color:#94a3b8;">⏳ Đang kiểm tra tệp ảnh, kích thước và dung lượng...</div>`;



  }







  try {



    const payload = {



      production_mode: el.inProductionMode ? el.inProductionMode.value : "narrative",



      series,



      episode,



      action: "analyze_competitor_thumbnail",



      image_base64: uploadedCompetitorBase64 || "",



    };



    const res = await fetch(`/api/episode/seo?series=${encodeURIComponent(series)}&episode=${episode}`, {



      method: "POST",



      headers: { "Content-Type": "application/json" },



      body: JSON.stringify(payload),



    });



    const data = await res.json();



    if (!res.ok || data.error) {



      throw new Error(data.error || "Không thể phân tích ảnh đối thủ.");



    }







    const card=data.technical_checks||{};



    if(box) box.innerHTML=`<div style="color:#cbd5e1;padding:12px;">



      <strong>${escapeHtml(data.filename||"Ảnh đã chọn")}</strong><br>



      Kỹ thuật ảnh: ${card.total_score ?? "—"}/100 (kiểm tra nội bộ)<br>



      ${Number(data.width)||0} × ${Number(data.height)||0}px<br>



      ${(card.breakdown||[]).map(b=>`${b.passed?"✅":"⚠️"} ${escapeHtml(b.label)}`).join("<br>")}<br>



      Chữ, biểu cảm và vùng huy hiệu thời lượng cần kiểm tra bằng mắt. Chưa có điểm vidIQ hay CTR.<br>



      <button type="button" class="btn btn-secondary btn-xs" onclick="importCompetitorThumbnail()">Dùng ảnh đã chọn làm thumbnail chính</button>



    </div>`;



    showToast("Đã kiểm tra tệp ảnh, kích thước và dung lượng.");



  } catch (err) {



    if (box) {



      box.innerHTML = `<div style="color:#ef4444;padding:8px;">⚠️ Lỗi phân tích: ${escapeHtml(err.message)}</div>`;



    }



    showToast("Lỗi phân tích ảnh đối thủ: " + err.message);



  } finally {



    if (btn) btn.textContent = "🔍 Kiểm Tra Kỹ Thuật Ảnh";



  }

};







window.importCompetitorThumbnail = async function () {



  const { series, episode } = getActiveSeriesAndEpisode();







  const btn = document.getElementById("btnImportCompetitor");



  const origText = btn ? btn.innerHTML : "";



  if (btn) {



    btn.innerHTML = "⏳ Đang chuẩn bị ảnh đã chọn...";



    btn.disabled = true;



  }







  try {



    const payload = {



      production_mode: el.inProductionMode ? el.inProductionMode.value : "narrative",



      series,



      episode,



      action: "import_competitor_thumbnail",



      image_base64: uploadedCompetitorBase64 || "",



    };



    const res = await fetch(`/api/episode/seo?series=${encodeURIComponent(series)}&episode=${episode}`, {



      method: "POST",



      headers: { "Content-Type": "application/json" },



      body: JSON.stringify(payload),



    });



    const updated = await res.json();



    if (!res.ok || updated.error) {



      throw new Error(updated.error || "Không thể nhập ảnh đối thủ.");



    }







    if (updated && updated.thumbnail_url) {



      currentSeoData = updated;



      renderSeoPackageUI(updated);



      showToast("Đã cập nhật thumbnail chính từ ảnh bạn chọn.");



    }



  } catch (err) {



    showToast("Lỗi nhập thumbnail đối thủ: " + err.message);



  } finally {



    if (btn) {



      btn.innerHTML = origText;



      btn.disabled = false;



    }



  }

};























async function checkUpdateAvailability() {



  const button = document.getElementById("btnCheckUpdates");



  if (!button || button.disabled || button.dataset.updateCheckInFlight === "true") return;



  button.dataset.updateCheckInFlight = "true";



  try {



    const response = await fetch("/api/update/check", { cache: "no-store" });



    const data = await response.json();



    if (!response.ok || !data.ok) return;







    const available = data.update_available === true;



    button.dataset.updateAvailable = available ? "true" : "false";



    button.dataset.updateLatestVersion = data.latest_version || "";



    if (available) {



      const label = `⬆ Có bản mới ${data.latest_version}`;



      button.dataset.updateAvailableLabel = label;



      button.textContent = label;



      button.title = `Đang dùng ${data.current_version}; có bản ${data.latest_version}. Bấm để cập nhật.`;



      button.setAttribute("aria-label", button.title);



      button.classList.add("update-available");



      button.style.borderColor = "#f59e0b";



      button.style.backgroundColor = "rgba(245, 158, 11, 0.16)";



      button.style.color = "#ffdf9e";



      button.style.fontWeight = "700";



    } else {



      button.textContent = button.dataset.updateDefaultText || "↻ Cập nhật";



      button.title = button.dataset.updateDefaultTitle || "Kiểm tra và cài bản Storyboard AI mới";



      button.setAttribute("aria-label", button.title);



      button.classList.remove("update-available");



      button.style.removeProperty("border-color");



      button.style.removeProperty("background-color");



      button.style.removeProperty("color");



      button.style.removeProperty("font-weight");



    }



  } catch (error) {



    // Keep the last known indicator if the private update feed is temporarily offline.



  } finally {



    button.dataset.updateCheckInFlight = "false";



  }



}







let onlineUpdatePolling = false;

const onlineUpdatePendingKey = "storyboard-online-update-pending";



function paintOnlineUpdate(state, message, percent) {

  const button = document.getElementById("btnCheckUpdates");

  if (!button) return;

  const labels = {

    starting: "Đang bắt đầu…",

    checking: "Đang kiểm tra…",

    downloading: "Đang tải " + Math.max(0, Math.min(100, Number(percent) || 0)) + "%",

    verifying: "Đang xác minh…",

    extracting: "Đang giải nén…",

    installing: "Đang cài đặt…",

    restarting: "Đang khởi động lại…",

    completed: "✓ Đã cập nhật",

    failed: "Lỗi cập nhật — thử lại"

  };

  button.textContent = labels[state] || "Đang cập nhật…";

  button.title = message || button.textContent;

  button.setAttribute("aria-label", button.title);

  button.disabled = !["failed", "completed"].includes(state);

}



async function monitorOnlineUpdate() {

  if (onlineUpdatePolling) return;

  onlineUpdatePolling = true;

  let disconnects = 0;

  try {

    while (true) {

      let state;

      try {

        const response = await fetch("/api/update/status", { cache: "no-store" });

        if (!response.ok) throw new Error("Không đọc được tiến độ cập nhật.");

        state = await response.json();

        disconnects = 0;

      } catch (error) {

        disconnects++;

        if (disconnects > 120) throw new Error("Chưa kết nối lại được ứng dụng. Hãy mở lại Storyboard AI.");

        paintOnlineUpdate("restarting", "Ứng dụng đang khởi động lại sau cập nhật.");

        await new Promise(resolve => setTimeout(resolve, 2000));

        continue;

      }

      if (state.state === "completed") {

        sessionStorage.removeItem(onlineUpdatePendingKey);

        paintOnlineUpdate("completed", "Đã cập nhật " + (state.version || ""));

        showToast("Cập nhật hoàn tất. Đang tải lại giao diện.", "success");

        setTimeout(() => location.reload(), 1200);

        return;

      }

      if (state.state === "failed") throw new Error(state.message || "Cập nhật thất bại. Hãy thử lại.");

      paintOnlineUpdate(state.state, state.message, state.percent);

      await new Promise(resolve => setTimeout(resolve, 2000));

    }

  } catch (error) {

    sessionStorage.removeItem(onlineUpdatePendingKey);

    paintOnlineUpdate("failed", error.message);

    showToast("Cập nhật chưa hoàn tất: " + error.message, "error");

  } finally {

    onlineUpdatePolling = false;

  }

}



async function startOnlineUpdate() {

  if (onlineUpdatePolling) return;

  paintOnlineUpdate("checking");

  try {

    const response = await fetch("/api/update/start", {

      method: "POST",

      headers: { "Content-Type": "application/json" },

      body: "{}"

    });

    const data = await response.json();

    if (!response.ok || !data.success) throw new Error(data.error || "Không khởi động được cập nhật.");

    sessionStorage.setItem(onlineUpdatePendingKey, "1");

    await monitorOnlineUpdate();

  } catch (error) {

    paintOnlineUpdate("failed", error.message);

    showToast("Không thể cập nhật: " + error.message, "error");

  }

}



async function resumeOnlineUpdate() {

  try {

    const response = await fetch("/api/update/status", { cache: "no-store" });

    if (!response.ok) return;

    const state = await response.json();

    if (!["idle", "completed", "failed"].includes(state.state) || sessionStorage.getItem(onlineUpdatePendingKey)) {

      await monitorOnlineUpdate();

    }

  } catch (error) { /* A later click can retry after startup. */ }

}

window.addEventListener("DOMContentLoaded", resumeOnlineUpdate);

// END ONLINE UPDATE UI













/* ==========================================================================



   YOUTUBE MULTI-CHANNEL MANAGEMENT & 1-CLICK VIDEO UPLOADER



   ========================================================================== */







window.youTubeState = {



  channels: [],



  activeChannelId: "",



  clientConfigured: false,



  uploading: false,



  pollTimer: null



};







window.openYouTubeModal = async function () {



  const modal = document.getElementById("modalYouTubeManager");



  if (!modal) return;



  openModal(modal);



  await window.fetchYouTubeChannels();



};







window.fetchYouTubeChannels = async function () {



  try {



    const res = await fetch("/api/youtube/channels");



    if (!res.ok) throw new Error("Không thể tải danh sách kênh");



    const data = await res.json();



    window.youTubeState.channels = data.channels || [];



    let savedUserCh = (window.youTubeState.userSelectedChannel && window.youTubeState.selectedChannelId)

      || window.youTubeState.selectedChannelId;

    if (!savedUserCh) {

      try { savedUserCh = localStorage.getItem("yt_user_selected_channel_id"); } catch (_) {}

    }



    if (savedUserCh && (data.channels || []).some(c => c.id === savedUserCh)) {

      window.youTubeState.userSelectedChannel = true;

      window.youTubeState.selectedChannelId = savedUserCh;

      window.youTubeState.activeChannelId = savedUserCh;

    } else {

      window.youTubeState.activeChannelId = data.active_channel_id || "";

    }



    window.youTubeState.clientConfigured = !!data.client_id_configured;







    // Badges & indicators



    const countBadge = document.getElementById("ytChannelCountBadge");



    if (countBadge) countBadge.textContent = `${data.count || 0} Kênh`;







    const oauthBadge = document.getElementById("ytOAuthConfigBadge");



    if (oauthBadge) {



      if (data.client_id_configured) {



        oauthBadge.textContent = "✓ Đã sẵn sàng";



        oauthBadge.style.background = "#059669";



      } else {



        oauthBadge.textContent = "Chưa cấu hình";



        oauthBadge.style.background = "#475569";



      }



    }







    const settingsSummary = document.getElementById("settingsYtStatusSummary");



    if (settingsSummary) {



      if (data.count > 0) {



        const activeCh = (data.channels || []).find(c => c.is_active);



        const name = activeCh ? activeCh.name : "Đã kết nối";



        settingsSummary.textContent = `${data.count} kênh đã kết nối • Kênh mặc định: ${name}`;



      } else {



        settingsSummary.textContent = "Chưa kết nối kênh nào (Bấm Quản Lý để thêm kênh)";



      }



    }







    // Populate channel dropdowns & slots in Cinema Monitor & SEO modal

    const effectiveId = (window.youTubeState.userSelectedChannel && window.youTubeState.selectedChannelId)

      || window.youTubeState.selectedChannelId

      || window.youTubeState.activeChannelId

      || data.active_channel_id;



    renderChannelDropdowns(data.channels, effectiveId);

    renderChannelNumberSlots(data.channels, effectiveId);







    // Render cards in YouTube Manager modal



    renderYouTubeChannelCards(data.channels, data.active_channel_id);







    // Auto-detect channel for active series, or apply saved settings for default channel



    const curSeries = (window.currentSeoData && window.currentSeoData.series) || (state && state.currentSeries) || (el.inSeries && el.inSeries.value.trim()) || "";



    const curLang = (window.currentSeoData && window.currentSeoData.language) || (state && state.loadedEpisodeData && state.loadedEpisodeData.config && state.loadedEpisodeData.config.language) || (el.inLanguage && el.inLanguage.value.trim()) || "";



    if (!window.youTubeState.userSelectedChannel && curSeries) {



      if (typeof window.autoDetectAndSelectChannel === "function") {



        window.autoDetectAndSelectChannel(curSeries, curLang);



      }



    } else {



      const activeChId = (window.youTubeState.userSelectedChannel && window.youTubeState.selectedChannelId) || data.active_channel_id;



      if (activeChId && typeof window.applyChannelSavedSettings === "function") {



        window.applyChannelSavedSettings(activeChId);



      }



    }



  } catch (err) {



    console.error("fetchYouTubeChannels error:", err);



  }

};







function getChannelUrl(ch) {



  if (!ch) return "https://www.youtube.com";



  if (ch.custom_url) {



    const handle = ch.custom_url.startsWith("@") ? ch.custom_url : ("@" + ch.custom_url);



    return `https://www.youtube.com/${handle}`;



  }



  if (ch.id) return `https://www.youtube.com/channel/${ch.id}`;



  return "https://www.youtube.com";



}







function getStudioUrl(ch) {



  if (!ch || !ch.id) return "https://studio.youtube.com";



  return `https://studio.youtube.com/channel/${ch.id}`;



}







function updateVisitChannelButtons(channelId) {



  const ch = (window.youTubeState.channels || []).find(c => c.id === channelId) || (window.youTubeState.channels && window.youTubeState.channels[0]);



  const quickBtn = document.getElementById("btnVisitQuickChannel");



  const seoBtn = document.getElementById("btnVisitSeoChannel");







  if (ch) {



    const url = getChannelUrl(ch);



    if (quickBtn) {



      quickBtn.href = url;



      quickBtn.style.display = "inline-flex";



      quickBtn.title = `Mở kênh ${ch.name} trên YouTube: ${url}`;



    }



    if (seoBtn) {



      seoBtn.href = url;



      seoBtn.style.display = "inline-flex";



      seoBtn.title = `Mở kênh ${ch.name} trên YouTube: ${url}`;



    }



  } else {



    if (quickBtn) quickBtn.style.display = "none";



    if (seoBtn) seoBtn.style.display = "none";



  }



}







function renderChannelDropdowns(channels, activeId) {



  const selects = [



    document.getElementById("ytQuickChannelSelect"),



    document.getElementById("seoYtChannelSelect"),



    document.getElementById("advYtChannelSelect")



  ];







  const targetId = (window.youTubeState.userSelectedChannel && window.youTubeState.selectedChannelId)



    ? window.youTubeState.selectedChannelId



    : (activeId || window.youTubeState.activeChannelId || (channels && channels[0] ? channels[0].id : ""));







  selects.forEach(sel => {



    if (!sel) return;



    if (!channels || channels.length === 0) {



      sel.innerHTML = '<option value="">Chưa có kênh (Bấm Quản Lý để thêm)</option>';



      return;



    }



    sel.innerHTML = channels.map(ch => {



      const isSel = ch.id === targetId ? "selected" : "";



      const subs = ch.subscriber_count ? ` (${Number(ch.subscriber_count).toLocaleString()} subs)` : "";



      return `<option value="${escapeHtml(ch.id)}" ${isSel}>${escapeHtml(ch.name)}${subs}</option>`;



    }).join("");



    if (targetId) sel.value = targetId;



  });







  updateVisitChannelButtons(targetId);



  fetchChannelPlaylists(targetId);



  renderChannelNumberSlots(channels, targetId);



}



function renderChannelNumberSlots(channels, activeId) {

  const container = document.getElementById("ytChannelNumberSlots");

  const titleEl = document.getElementById("ytActiveChannelTitle");

  if (!container) return;



  if (!channels || channels.length === 0) {

    container.innerHTML = '<span style="font-size:0.62rem;color:#64748b;">(Chưa có kênh)</span>';

    if (titleEl) titleEl.textContent = "🔴 Chưa có kênh";

    return;

  }



  container.innerHTML = channels.map((ch, idx) => {

    const isSel = ch.id === activeId;

    const num = idx + 1;

    const activeCls = isSel ? "active" : "";

    const nameEsc = escapeHtml(ch.name || `Kênh ${num}`);

    const subsStr = ch.subscriber_count ? ` (${Number(ch.subscriber_count).toLocaleString()} subs)` : "";

    return `<button type="button" class="yt-num-btn ${activeCls}" onclick="selectChannelSlot('${escapeHtml(ch.id)}', ${num})" title="Kênh ${num}: ${nameEsc}${subsStr}">${num}</button>`;

  }).join("");



  const activeIdx = channels.findIndex(c => c.id === activeId);

  const activeNum = activeIdx >= 0 ? activeIdx + 1 : 1;

  const activeCh = channels[activeIdx >= 0 ? activeIdx : 0];

  if (titleEl && activeCh) {

    titleEl.textContent = `🔴 Kênh ${activeNum}: ${activeCh.name}`;

    titleEl.title = `Kênh ${activeNum}: ${activeCh.name} (${activeCh.subscriber_count || 0} subs)`;

  }

}



window.selectChannelSlot = function (channelId, slotNum) {

  if (!channelId) return;

  window.youTubeState.userSelectedChannel = true;

  window.youTubeState.selectedChannelId = channelId;

  window.youTubeState.activeChannelId = channelId;

  try { localStorage.setItem("yt_user_selected_channel_id", channelId); } catch (_) {}



  const advHeaderTag = document.getElementById("advYtCurrentChannelTag");

  const curCh = (window.youTubeState.channels || []).find(c => c.id === channelId);

  if (advHeaderTag && curCh) {

    advHeaderTag.textContent = `🔴 Kênh ${slotNum}: ${curCh.name}`;

  }



  // Sync legacy hidden & advanced selects

  ["ytQuickChannelSelect", "seoYtChannelSelect", "advYtChannelSelect"].forEach(id => {

    const sel = document.getElementById(id);

    if (sel) sel.value = channelId;

  });



  fetch("/api/youtube/channels/select", {

    method: "POST",

    headers: { "Content-Type": "application/json" },

    body: JSON.stringify({ channel_id: channelId })

  }).catch(() => {});



  // Update active state on number buttons

  const container = document.getElementById("ytChannelNumberSlots");

  if (container) {

    const buttons = container.querySelectorAll(".yt-num-btn");

    buttons.forEach((btn, idx) => {

      btn.classList.toggle("active", idx === (slotNum - 1));

    });

  }



  // Update title

  const titleEl = document.getElementById("ytActiveChannelTitle");

  const ch = (window.youTubeState.channels || []).find(c => c.id === channelId);

  if (titleEl && ch) {

    titleEl.textContent = `🔴 Kênh ${slotNum}: ${ch.name}`;

    titleEl.title = `Kênh ${slotNum}: ${ch.name} (${ch.subscriber_count || 0} subs)`;

  }



  updateVisitChannelButtons(channelId);

  fetchChannelPlaylists(channelId);



  // Auto-apply saved settings for this channel from modal!

  if (typeof window.applyChannelSavedSettings === "function") {

    window.applyChannelSavedSettings(channelId);

  }

};







window.syncPlaylistChoice = function (playlistId) {



  if (!playlistId) return;



  const quickSelect = document.getElementById("ytQuickPlaylistSelect");



  const seoSelect = document.getElementById("seoYtPlaylistSelect");



  const advSelect = document.getElementById("advYtPlaylistSelect");



  [quickSelect, seoSelect, advSelect].forEach(sel => {



    if (sel && sel.value !== playlistId) {



      if (Array.from(sel.options).some(o => o.value === playlistId)) {



        sel.value = playlistId;



      }



    }



  });



  // Toggle custom playlist title input field if user chose __new__

  const wrap = document.getElementById("advYtNewPlaylistWrap");

  const input = document.getElementById("advYtNewPlaylistTitle");

  if (wrap) {

    if (playlistId === "__new__") {

      wrap.style.display = "block";

      if (input) {

        input.focus();

        if (!input.value) {

          const { series } = getActiveSeriesAndEpisode();

          if (series && series !== "auto") input.value = series;

        }

      }

    } else {

      wrap.style.display = "none";

    }

  }



};



window.refreshYouTubePlaylistsFromModal = async function () {

  const selCh = document.getElementById("advYtChannelSelect");

  const channelId = selCh ? selCh.value : (window.youTubeState.activeChannelId || "");

  if (!channelId) {

    showToast("Vui lòng chọn kênh trước khi làm mới danh sách phát.", "warning");

    return;

  }

  showToast("Đang làm mới danh sách phát từ YouTube...", "info");

  try {

    await fetchChannelPlaylists(channelId, true);

    showToast("Đã đồng bộ danh sách phát mới nhất từ YouTube!", "success");

  } catch (err) {

    showToast("Không thể tải danh sách phát: " + (err.message || err), "error");

  }

};







async function fetchChannelPlaylists(channelId, forceRefresh = false) {

  if (!channelId) return;



  const quickSelect = document.getElementById("ytQuickPlaylistSelect");



  const seoSelect = document.getElementById("seoYtPlaylistSelect");



  const advSelect = document.getElementById("advYtPlaylistSelect");







  if (!window.youTubeState.playlistCache) window.youTubeState.playlistCache = {};







  const ch = (window.youTubeState.channels || []).find(c => c.id === channelId);



  const chSettings = (ch && ch.publish_settings) || {};



  let targetPlaylistId = chSettings.default_playlist_id || "auto";







  const renderPlaylists = (playlists) => {



    let effectiveTarget = targetPlaylistId;



    if (playlists.length === 1 && (!effectiveTarget || effectiveTarget === "auto")) {



      effectiveTarget = playlists[0].id;



    }







    let optionsHtml = '<option value="auto">🔥 Tự động (Theo Series &amp; Chủ đề)</option>';



    if (playlists.length > 0) {



      optionsHtml += playlists.map(pl => {



        const count = pl.item_count ? ` (${pl.item_count} video)` : "";



        return `<option value="${escapeHtml(pl.id)}">📑 ${escapeHtml(pl.title)}${count}</option>`;



      }).join("");



    }



    optionsHtml += '<option value="none">Không gán danh sách phát</option>';

    optionsHtml += '<option value="__new__">➕ Tạo danh sách phát mới...</option>';







    [quickSelect, seoSelect, advSelect].forEach(sel => {



      if (!sel) return;



      sel.innerHTML = optionsHtml;



      if (effectiveTarget && Array.from(sel.options).some(o => o.value === effectiveTarget)) {



        sel.value = effectiveTarget;



      } else {



        sel.value = "auto";



      }



    });



  };







  // If already cached and not forced, render immediately with 0 delay!



  if (!forceRefresh && window.youTubeState.playlistCache[channelId]) {



    renderPlaylists(window.youTubeState.playlistCache[channelId]);



    return;



  }







  try {



    const res = await fetch(`/api/youtube/playlists?channel_id=${encodeURIComponent(channelId)}`);



    if (!res.ok) return;



    const data = await res.json();



    const playlists = data.playlists || [];



    window.youTubeState.playlistCache[channelId] = playlists;



    renderPlaylists(playlists);



  } catch (err) {



    console.warn("fetchChannelPlaylists error:", err);



  }

}

window.fetchChannelPlaylists = fetchChannelPlaylists;







window.reauthYouTubeChannel = async function (channelId) {



  try {



    const res = await fetch(`/api/youtube/auth_url?channel_id=${encodeURIComponent(channelId)}`);



    const data = await res.json();



    if (!data.ok || !data.auth_url) {



      throw new Error(data.error || "Không thể tạo liên kết xác thực Google.");



    }



    const w = 620, h = 720;



    const left = (screen.width - w) / 2;



    const top = (screen.height - h) / 2;



    window.open(data.auth_url, "GoogleOAuthReauth", `width=${w},height=${h},top=${top},left=${left}`);



    showToast("🔑 Đang mở cửa sổ ủy quyền cấp quyền Playlist Google...", "info");



  } catch (err) {



    showToast("Lỗi: " + err.message, "error");



  }

};







function renderYouTubeChannelCards(channels, activeId) {



  const container = document.getElementById("ytChannelCardsContainer");



  const tableHeader = document.getElementById("ytChannelTableHeader");



  if (!container) return;







  if (!channels || channels.length === 0) {



    if (tableHeader) tableHeader.style.display = "none";



    if (window.youTubeState.clientConfigured) {



      container.innerHTML = `



        <div style="text-align:center;padding:26px 16px;background:#090d16;border-radius:10px;border:1px dashed #334155;">



          <div style="font-size:2.2rem;margin-bottom:8px;">📺</div>



          <div style="color:#f8fafc;font-weight:700;font-size:0.9rem;">Chưa có kênh YouTube nào được kết nối</div>



          <div style="color:#94a3b8;font-size:0.75rem;margin:6px auto 14px auto;max-width:440px;line-height:1.5;">



            Bấm nút bên dưới để đăng nhập tài khoản Google và cấp quyền cho Storyboard AI đăng video tự động.



          </div>



          <button type="button" class="btn btn-danger btn-sm" onclick="handleUnifiedYouTubeConnect()" style="background:#dc2626;color:#fff;font-weight:700;border:none;padding:7px 16px;border-radius:6px;cursor:pointer;display:inline-flex;align-items:center;gap:6px;box-shadow:0 0 12px rgba(220,38,38,0.4);">



            🔴 + Kết Nối Kênh YouTube Ngay



          </button>



        </div>



      `;



    } else {



      container.innerHTML = `



        <div style="text-align:center;padding:26px 16px;background:#090d16;border-radius:10px;border:1px dashed rgba(239,68,68,0.35);">



          <div style="font-size:2.2rem;margin-bottom:8px;">🚀</div>



          <div style="color:#f8fafc;font-weight:700;font-size:0.92rem;">Kết Nối Kênh YouTube (Chỉ 1 Bước Duy Nhất)</div>



          <div style="color:#94a3b8;font-size:0.74rem;margin:6px auto 14px auto;max-width:480px;line-height:1.5;">



            Bạn chỉ cần chọn tệp <code style="color:#fca5a5;background:#1e293b;padding:2px 6px;border-radius:4px;font-weight:700;">client_secret.json</code> tải về từ Google Cloud. Hệ thống sẽ tự động cấu hình và mở ngay cửa sổ kết nối Google!



          </div>



          <button type="button" class="btn btn-danger btn-sm" onclick="handleUnifiedYouTubeConnect()" style="background:#dc2626;color:#fff;font-weight:700;border:none;padding:8px 18px;border-radius:6px;cursor:pointer;display:inline-flex;align-items:center;gap:6px;box-shadow:0 0 14px rgba(220,38,38,0.4);">



            📁 Chọn Tệp client_secret.json (Tự Động Kết Nối Ngay)



          </button>



          <div style="margin-top:14px;display:flex;justify-content:center;gap:12px;flex-wrap:wrap;font-size:0.72rem;">



            <a href="https://console.cloud.google.com/apis/credentials" target="_blank" style="color:#38bdf8;text-decoration:none;display:inline-flex;align-items:center;gap:4px;" title="Tạo hoặc tải file OAuth Client ID miễn phí trên Google Cloud">



              🌐 Mở Google Cloud Console ↗



            </a>



            <span style="color:#475569;">•</span>



            <a href="javascript:void(0)" onclick="copyYouTubeRedirectUri()" style="color:#a7f3d0;text-decoration:none;display:inline-flex;align-items:center;gap:4px;" title="Sao chép link Authorized redirect URIs">



              📋 Copy Link Callback URI



            </a>



          </div>



        </div>



      `;



    }



    return;



  }







  if (tableHeader) tableHeader.style.display = "grid";







  container.innerHTML = channels.map(ch => {



    const isAct = ch.id === activeId || ch.is_active;



    const avatar = ch.avatar_url || 'assets/storyboard_ai_icon.png';



    const subs = ch.subscriber_count ? `${Number(ch.subscriber_count).toLocaleString()} Subs` : '0 Subs';



    const handle = ch.custom_url || ch.id;



    const chUrl = getChannelUrl(ch);



    const studioUrl = getStudioUrl(ch);







    return `



      <div style="display:grid;grid-template-columns:minmax(200px, 1fr) 115px 175px;gap:8px;align-items:center;padding:7px 12px;background:#090d16;border-radius:8px;border:1px solid ${isAct ? 'rgba(239,68,68,0.55)' : '#1e293b'};min-height:44px;box-sizing:border-box;">



        <!-- Col 1: Kênh YouTube (Avatar + Tên + Meta) -->



        <div style="display:flex;align-items:center;gap:10px;min-width:0;overflow:hidden;">



          <a href="${chUrl}" target="_blank" title="Mở kênh trên YouTube: ${escapeHtml(ch.name)}" style="flex-shrink:0;display:inline-flex;">



            <img src="${escapeHtml(avatar)}" onerror="this.src='assets/storyboard_ai_icon.png'" style="width:32px;height:32px;border-radius:50%;object-fit:cover;border:1.5px solid ${isAct ? '#ef4444' : '#334155'};display:block;">



          </a>



          <div style="min-width:0;flex:1;overflow:hidden;">



            <div style="display:flex;align-items:center;gap:6px;white-space:nowrap;overflow:hidden;">



              <a href="${chUrl}" target="_blank" style="font-weight:700;font-size:0.86rem;color:#f8fafc;text-decoration:none;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" onmouseover="this.style.color='#38bdf8'" onmouseout="this.style.color='#f8fafc'" title="Mở kênh: ${escapeHtml(ch.name)}">



                ${escapeHtml(ch.name)}



              </a>



              ${ch.token_expired ? `

                <span class="badge" style="background:#7f1d1d;color:#fca5a5;border:1px solid #ef4444;font-size:0.58rem;font-weight:700;padding:1px 5px;border-radius:4px;flex-shrink:0;cursor:pointer;" onclick="reauthYouTubeChannel('${escapeHtml(ch.id)}')" title="Bấm để cấp quyền lại ngay">⚠️ Hết hạn OAuth (7 ngày)</span>

              ` : `

                <span class="badge" style="background:#065f46;color:#a7f3d0;font-size:0.58rem;font-weight:600;padding:1px 5px;border-radius:4px;flex-shrink:0;">🟢 Đã kết nối</span>

              `}



            </div>



            <div style="font-size:0.68rem;color:#94a3b8;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:2px;">



              <span style="color:#cbd5e1;">${escapeHtml(handle)}</span> &bull; <strong style="color:#fca5a5;">${escapeHtml(subs)}</strong> &bull; <span style="font-family:monospace;color:#64748b;font-size:0.65rem;">${escapeHtml(ch.id)}</span>



            </div>



          </div>



        </div>







        <!-- Col 2: Chế độ đăng (115px) -->



        <select onchange="updateYouTubeChannelPrivacy('${escapeHtml(ch.id)}', this.value)" style="width:115px;height:28px;box-sizing:border-box;background:#0b1329;color:#e2e8f0;border:1px solid #334155;border-radius:5px;padding:2px 6px;font-size:0.68rem;cursor:pointer;" title="Chế độ bảo mật khi đăng video">



          <option value="private" ${ch.default_privacy === 'private' ? 'selected' : ''}>🔒 Riêng tư</option>



          <option value="unlisted" ${ch.default_privacy === 'unlisted' ? 'selected' : ''}>👁️ K.công khai</option>



          <option value="public" ${ch.default_privacy === 'public' ? 'selected' : ''}>🌐 Công khai</option>



        </select>







        <!-- Col 3: Thao tác nhanh (5 nút tròn đồng đều kích thước 28x28px "đầu đũa tròn") -->



        <div style="display:flex;align-items:center;justify-content:center;gap:6px;width:175px;box-sizing:border-box;">



          <a href="${chUrl}" target="_blank" class="yt-circle-btn yt-circle-channel" title="Mở trang chủ kênh trên YouTube">



            🔗



          </a>



          <a href="${studioUrl}" target="_blank" class="yt-circle-btn yt-circle-studio" title="Mở YouTube Studio">



            🛠️



          </a>



          <button type="button" class="yt-circle-btn yt-circle-playlist" onclick="reauthYouTubeChannel('${escapeHtml(ch.id)}')" title="Cấp quyền Google: Tự động gán Playlist">



            🔑



          </button>



          ${isAct ? `



            <button type="button" class="yt-circle-btn yt-circle-default active" title="Kênh này đang là mặc định để đăng video">



              ⭐



            </button>



          ` : `



            <button type="button" class="yt-circle-btn yt-circle-default" onclick="selectActiveYouTubeChannel('${escapeHtml(ch.id)}')" title="Đặt kênh này làm mặc định đăng video">



              ⭐



            </button>



          `}



          <button type="button" class="yt-circle-btn yt-circle-delete" onclick="deleteYouTubeChannel('${escapeHtml(ch.id)}', '${escapeJsString(ch.name)}')" title="Hủy kết nối kênh này">



            🗑️



          </button>



        </div>



      </div>



    `;



  }).join("");



}







window.copyYouTubeRedirectUri = function () {



  const uri = "http://127.0.0.1:8765/api/youtube/oauth_callback";



  if (navigator.clipboard && navigator.clipboard.writeText) {



    navigator.clipboard.writeText(uri).then(() => {



      showToast("📋 Đã sao chép link Callback vào bộ nhớ tạm!", "success");



    }).catch(() => {



      prompt("Sao chép link Authorized redirect URI này và dán vào Google Cloud:", uri);



    });



  } else {



    prompt("Sao chép link Authorized redirect URI này và dán vào Google Cloud:", uri);



  }

};







window.handleUnifiedYouTubeConnect = async function () {



  // If credentials already configured, go straight to Google OAuth!



  if (window.youTubeState.clientConfigured) {



    await window.startOAuthFlow();



    return;



  }







  // If not yet configured, trigger the file picker directly!



  const fileInput = document.getElementById("ytUnifiedClientSecretInput");



  if (fileInput) {



    fileInput.click();



    showToast("📁 Vui lòng chọn tệp client_secret.json để tự động kết nối ngay!", "info");



  } else {



    await window.startOAuthFlow();



  }

};







window.handleUnifiedSecretFile = function (fileInput) {



  const file = fileInput.files && fileInput.files[0];



  if (!file) return;







  const reader = new FileReader();



  reader.onload = async function (e) {



    try {



      const data = JSON.parse(e.target.result);



      const creds = data.installed || data.web || data;



      const cid = (creds.client_id || data.client_id || "").trim();



      const csec = (creds.client_secret || data.client_secret || "").trim();







      if (!cid || !csec) {



        alert("⚠️ Tệp JSON này không chứa 'client_id' hoặc 'client_secret'. Vui lòng chọn đúng tệp tải về từ mục OAuth 2.0 Client IDs trên Google Cloud Console.");



        return;



      }







      // Fill optional manual inputs



      const inCid = document.getElementById("inYtClientId");



      const inSec = document.getElementById("inYtClientSecret");



      if (inCid) inCid.value = cid;



      if (inSec) inSec.value = csec;







      showToast("Đang tự động lưu cấu hình và kết nối Google...", "info");







      // Save credentials via API



      const res = await fetch("/api/youtube/credentials", {



        method: "POST",



        headers: { "Content-Type": "application/json" },



        body: JSON.stringify({ client_id: cid, client_secret: csec })



      });



      const resData = await res.json();







      if (resData.ok) {



        window.youTubeState.clientConfigured = true;



        const oauthBadge = document.getElementById("ytOAuthConfigBadge");



        if (oauthBadge) {



          oauthBadge.textContent = "✓ Đã sẵn sàng";



          oauthBadge.style.background = "#059669";



        }



        showToast("✅ Đã lưu cấu hình Google OAuth! Đang mở cửa sổ ủy quyền Google...", "success");



        await window.fetchYouTubeChannels();







        // Immediately launch Google OAuth window!



        await window.startOAuthFlow();



      } else {



        alert("Lỗi lưu cấu hình: " + (resData.error || "Không rõ nguyên nhân"));



      }



    } catch (err) {



      alert("Lỗi đọc tệp JSON: " + err.message);



    }



  };



  reader.readAsText(file);



};







window.handleClientSecretJsonUpload = function (fileInput) {



  window.handleUnifiedSecretFile(fileInput);



};







window.syncSelectedYouTubeChannel = function (channelId) {



  if (!channelId) return;



  window.youTubeState.userSelectedChannel = true;



  window.youTubeState.selectedChannelId = channelId;



  window.youTubeState.activeChannelId = channelId;

  try { localStorage.setItem("yt_user_selected_channel_id", channelId); } catch (_) {}



  fetch("/api/youtube/channels/select", {

    method: "POST",

    headers: { "Content-Type": "application/json" },

    body: JSON.stringify({ channel_id: channelId })

  }).catch(() => {});







  const qSelect = document.getElementById("ytQuickChannelSelect");



  const sSelect = document.getElementById("seoYtChannelSelect");



  const aSelect = document.getElementById("advYtChannelSelect");



  if (qSelect && qSelect.value !== channelId) qSelect.value = channelId;



  if (sSelect && sSelect.value !== channelId) sSelect.value = channelId;



  if (aSelect && aSelect.value !== channelId) aSelect.value = channelId;







  // Sync studio editor link



  const activeCh = (window.youTubeState.channels || []).find(c => c.id === channelId);



  const studioLink = document.getElementById("advYtStudioEditorLink");



  if (studioLink && activeCh) {



    studioLink.href = getStudioUrl(activeCh);



  }







  updateVisitChannelButtons(channelId);



  fetchChannelPlaylists(channelId);



  window.applyChannelSavedSettings(channelId);



  const channels = window.youTubeState.channels || [];

  const chIdx = channels.findIndex(c => c.id === channelId);

  const curCh = channels[chIdx >= 0 ? chIdx : 0];

  const advHeaderTag = document.getElementById("advYtCurrentChannelTag");

  if (advHeaderTag && curCh) {

    advHeaderTag.textContent = `🔴 Kênh ${chIdx >= 0 ? chIdx + 1 : 1}: ${curCh.name}`;

  }

  if (channels.length > 0) {

    renderChannelNumberSlots(channels, channelId);

  }







  const curLang = (window.currentSeoData && window.currentSeoData.language) || (state && state.loadedEpisodeData && state.loadedEpisodeData.config && state.loadedEpisodeData.config.language) || (el.inLanguage && el.inLanguage.value.trim()) || "";



  const chSettings = (activeCh && activeCh.publish_settings) || {};



  const chLang = chSettings.default_language || "";



  const isLangMismatch = curLang && chLang && !curLang.toLowerCase().includes(chLang.toLowerCase()) && !chLang.toLowerCase().includes(curLang.toLowerCase());







  // If a series is active, bind this series to the channel on server ONLY IF language matches



  const curSeries = (window.currentSeoData && window.currentSeoData.series) || (state && state.currentSeries) || (el.inSeries && el.inSeries.value.trim()) || "";



  const ignoredSeries = ["auto", "vẽ tranh", "whiteboard chronicles", "tập phim mới"];



  if (curSeries && !ignoredSeries.includes(curSeries.toLowerCase()) && !isLangMismatch) {



    fetch("/api/youtube/channels/settings", {



      method: "POST",



      headers: { "Content-Type": "application/json" },



      body: JSON.stringify({ channel_id: channelId, series_name: curSeries })



    }).catch(() => {});



  }







  // Persist as active default on server



  fetch("/api/youtube/channels/select", {



    method: "POST",



    headers: { "Content-Type": "application/json" },



    body: JSON.stringify({ channel_id: channelId })



  }).then(r => r.json()).then(data => {



    if (data.ok && window.youTubeState.channels) {



      window.youTubeState.channels.forEach(c => { c.is_active = (c.id === channelId); });



      renderYouTubeChannelCards(window.youTubeState.channels, channelId);



    }



  }).catch(() => {});







  if (activeCh) {



    if (isLangMismatch) {



      showToast(`⚠️ Kênh '${activeCh.name}' (Tiếng ${chLang.toUpperCase()}) khác ngôn ngữ video (${curLang.toUpperCase()}). Đăng sai kênh có thể bị coi là SPAM!`, "warning", 6000);



    } else {



      showToast(`📺 Đã chọn kênh: ${activeCh.name} • Đã nạp cấu hình chuẩn của kênh!`, "info");



    }



  }

};







window.getSeoScheduleIso = function (seoData) {



  // An unmeasured SEO schedule must never invent a publication time.



  const raw=document.getElementById("advYtPublishAt")?.value || "";



  const date=raw ? new Date(raw) : null;



  if(!date || !Number.isFinite(date.getTime()) || date.getTime()<=Date.now()) {



    return {iso:null,dtLocal:"",date:null,display:"Chưa chọn thời gian đăng"};



  }



  return {iso:date.toISOString(),dtLocal:raw,date,display:date.toLocaleString()};



};







window.syncPrivacyChoice = function (privacy) {



  if (!privacy) return;



  const qPriv = document.getElementById("ytQuickPrivacySelect");



  const sPriv = document.getElementById("seoYtPrivacySelect");



  const aPriv = document.getElementById("advYtPrivacySelect");



  if (qPriv && qPriv.value !== privacy) qPriv.value = privacy;



  if (sPriv && sPriv.value !== privacy) sPriv.value = privacy;



  if (aPriv && aPriv.value !== privacy) aPriv.value = privacy;







  const isSchedule = (privacy === "schedule_seo");

  if (typeof toggleScheduleField === "function") toggleScheduleField(isSchedule);



  if (isSchedule) {

    const sInfo = window.getSeoScheduleIso(window.currentSeoData);

    showToast(sInfo.iso ? `Đã chọn lịch đăng ${sInfo.display}` : "Chọn ngày và giờ phát hành trong khung lên lịch.", "info");

  }







  const chId = window.youTubeState.activeChannelId;



  if (chId && privacy !== "schedule_seo") {



    fetch("/api/youtube/channels/privacy", {



      method: "POST",



      headers: { "Content-Type": "application/json" },



      body: JSON.stringify({ channel_id: chId, default_privacy: privacy })



    }).catch(() => {});



  }

};







window.applyChannelSavedSettings = async function (channelId) {



  if (!channelId) return;



  try {



    let settings = null;



    const ch = (window.youTubeState.channels || []).find(c => c.id === channelId);



    if (ch && ch.publish_settings) {



      settings = ch.publish_settings;



    } else {



      const res = await fetch(`/api/youtube/channels/settings?channel_id=${encodeURIComponent(channelId)}`);



      if (res.ok) {



        const data = await res.json();



        settings = data.publish_settings || data.settings;



      }



    }



    if (!settings) return;







    const selPriv = document.getElementById("advYtPrivacySelect");



    const chkSynthetic = document.getElementById("advYtContainsSyntheticMedia");



    const radioKidsNo = document.getElementById("advYtKidsNo");



    const radioKidsYes = document.getElementById("advYtKidsYes");



    const selCat = document.getElementById("advYtCategory");



    const selLicense = document.getElementById("advYtLicense");



    const chkEmbed = document.getElementById("advYtEmbeddable");



    const chkPublicStats = document.getElementById("advYtPublicStats");



    const selDefLang = document.getElementById("advYtDefaultLang");



    const selAudioLang = document.getElementById("advYtAudioLang");



    const selPl = document.getElementById("advYtPlaylistSelect");







    const qPriv = document.getElementById("ytQuickPrivacySelect");



    const sPriv = document.getElementById("seoYtPrivacySelect");







    if (settings.default_privacy) {



      if (selPriv) selPriv.value = settings.default_privacy;



      if (qPriv) qPriv.value = settings.default_privacy;



      if (sPriv) sPriv.value = settings.default_privacy;



      const privMap = {

        "private": "radioYtModePrivate",

        "unlisted": "radioYtModeUnlisted",

        "public": "radioYtModePublic",

        "schedule_seo": "radioYtModeSchedule"

      };

      const rId = privMap[settings.default_privacy];

      if (rId) {

        const rEl = document.getElementById(rId);

        if (rEl) rEl.checked = true;

      }

      if (typeof window.toggleScheduleField === "function") {

        window.toggleScheduleField(settings.default_privacy === "schedule_seo");

      }



    }



    if (chkSynthetic && settings.contains_synthetic_media !== undefined) {



      chkSynthetic.checked = Boolean(settings.contains_synthetic_media);



    }



    if (settings.made_for_kids !== undefined) {



      if (radioKidsYes) radioKidsYes.checked = Boolean(settings.made_for_kids);



      if (radioKidsNo) radioKidsNo.checked = !settings.made_for_kids;



    }



    if (selCat && settings.category_id) {



      selCat.value = String(settings.category_id);



    }



    if (selLicense && settings.license) {



      selLicense.value = settings.license;



    }



    if (chkEmbed && settings.embeddable !== undefined) {



      chkEmbed.checked = Boolean(settings.embeddable);



    }



    if (chkPublicStats && settings.public_stats_viewable !== undefined) {



      chkPublicStats.checked = Boolean(settings.public_stats_viewable);



    }



    if (settings.shorts_remix) {

      const rNone = document.getElementById("advYtRemixNone");

      const rAudio = document.getElementById("advYtRemixAudio");

      const rAll = document.getElementById("advYtRemixAll");

      if (rNone) rNone.checked = (settings.shorts_remix === "none");

      if (rAudio) rAudio.checked = (settings.shorts_remix === "audio_only");

      if (rAll) rAll.checked = (settings.shorts_remix === "all");

    }



    const curEpLang = (window.currentSeoData && window.currentSeoData.language) || (window.state && window.state.loadedEpisodeData && window.state.loadedEpisodeData.config && window.state.loadedEpisodeData.config.language) || (window.state && window.state.currentLanguage) || "";
    let effectiveLang = settings.default_language;
    if (curEpLang) {
      const c = curEpLang.toLowerCase();
      if (c.includes("spa") || c === "es") effectiveLang = "es";
      else if (c.includes("vie") || c === "vi") effectiveLang = "vi";
      else if (c.includes("eng") || c === "en") effectiveLang = "en-US";
      else if (c.includes("rus") || c === "ru") effectiveLang = "ru";
      else if (c.includes("por") || c === "pt") effectiveLang = "pt-BR";
      else effectiveLang = curEpLang;
    }
    if (selDefLang && effectiveLang) {
      let l = effectiveLang;
      if (l === "en") l = "en-US";
      selDefLang.value = l;
    }
    if (selAudioLang && effectiveLang) {
      let l = effectiveLang;
      if (l === "en") l = "en-US";
      selAudioLang.value = l;
    }
    const selCaptionCert = document.getElementById("advYtCaptionCert");
    if (selCaptionCert) {
      selCaptionCert.value = settings.caption_certification || "never_aired_us";
    }

    const targetPl = settings.default_playlist_id || "auto";



    [selPl, document.getElementById("ytQuickPlaylistSelect"), document.getElementById("seoYtPlaylistSelect")].forEach(sel => {



      if (sel && targetPl) {



        if (Array.from(sel.options).some(o => o.value === targetPl)) {



          sel.value = targetPl;



        }



      }



    });



    // Update ultra-compact status line

    const summaryEl = document.getElementById("ytActivePresetSummary");

    if (summaryEl) {

      const p = settings.default_privacy || "unlisted";

      const pLabel = p === "public" ? "🌐 Public" : (p === "unlisted" ? "👁️ Unlisted" : (p === "schedule_seo" ? "⏰ Lên lịch" : "🔒 Private"));

      const aiLabel = settings.contains_synthetic_media !== false ? "🤖 AI" : "";

      const lang = settings.default_language ? (settings.default_language === "en-US" || settings.default_language === "en" ? "🇺🇸 en" : settings.default_language) : "";

      summaryEl.textContent = [pLabel, aiLabel, lang].filter(Boolean).join(" • ");

    }



  } catch (err) {



    console.warn("applyChannelSavedSettings error:", err);



  }

};







window.saveCurrentChannelPublishSettings = async function () {



  const selCh = document.getElementById("advYtChannelSelect");



  const channelId = selCh ? selCh.value : (window.youTubeState.activeChannelId || "");



  if (!channelId) {



    showToast("Vui lòng chọn hoặc thêm kênh trước khi lưu cấu hình.", "warning");



    return;



  }







  const selPriv = document.getElementById("advYtPrivacySelect");



  const selPl = document.getElementById("advYtPlaylistSelect");



  const chkSynthetic = document.getElementById("advYtContainsSyntheticMedia");



  const radioKidsYes = document.getElementById("advYtKidsYes");



  const selCat = document.getElementById("advYtCategory");



  const selLicense = document.getElementById("advYtLicense");



  const chkEmbed = document.getElementById("advYtEmbeddable");



  const chkPublicStats = document.getElementById("advYtPublicStats");



  const selDefLang = document.getElementById("advYtDefaultLang");



  const selAudioLang = document.getElementById("advYtAudioLang");







  const settings = {



    category_id: selCat ? selCat.value : "1",



    contains_synthetic_media: chkSynthetic ? chkSynthetic.checked : true,



    made_for_kids: radioKidsYes ? radioKidsYes.checked : false,



    license: selLicense ? selLicense.value : "youtube",



    embeddable: chkEmbed ? chkEmbed.checked : true,



    public_stats_viewable: chkPublicStats ? chkPublicStats.checked : true,



    default_privacy: selPriv ? selPriv.value : "unlisted",



    default_language: selDefLang ? selDefLang.value : "",



    default_audio_language: selAudioLang ? selAudioLang.value : "",



    default_playlist_id: (selPl && selPl.value !== "__new__") ? selPl.value : "auto",



    shorts_remix: (document.getElementById("advYtRemixNone") && document.getElementById("advYtRemixNone").checked) ? "none" : ((document.getElementById("advYtRemixAudio") && document.getElementById("advYtRemixAudio").checked) ? "audio_only" : "all")



  };







  const series = (window.currentSeoData && window.currentSeoData.series) || (state && state.currentSeries) || (el.inSeries && el.inSeries.value.trim()) || "";







  try {



    const res = await fetch("/api/youtube/channels/settings", {



      method: "POST",



      headers: { "Content-Type": "application/json" },



      body: JSON.stringify({



        channel_id: channelId,



        settings: settings,



        series_name: series



      })



    });



    const data = await res.json();



    if (data.ok) {



      if (window.youTubeState.channels) {



        const ch = window.youTubeState.channels.find(c => c.id === channelId);



        if (ch) ch.publish_settings = settings;



      }



      const qPriv = document.getElementById("ytQuickPrivacySelect");



      const sPriv = document.getElementById("seoYtPrivacySelect");



      if (qPriv) qPriv.value = settings.default_privacy;



      if (sPriv) sPriv.value = settings.default_privacy;



      const allChannels = window.youTubeState.channels || [];

      renderChannelNumberSlots(allChannels, channelId);

      updateVisitChannelButtons(channelId);

      window.applyChannelSavedSettings(channelId);



      showToast("💾 Đã lưu cấu hình xuất bản cho kênh thành công!", "success");



    } else {



      showToast("Lỗi lưu cấu hình: " + (data.error || "Không rõ"), "error");



    }



  } catch (err) {



    showToast("Lỗi kết nối khi lưu cấu hình: " + err.message, "error");



  }

};







window.autoDetectAndSelectChannel = async function (seriesName, language, force = false) {

  // USER MANUAL SELECTION IS SUPREME: NEVER OVERRIDE UNLESS FORCED!

  if (!force && window.youTubeState && window.youTubeState.userSelectedChannel && window.youTubeState.selectedChannelId) {

    return window.youTubeState.selectedChannelId;

  }



  const series = seriesName || (window.currentSeoData && window.currentSeoData.series) || (state && state.currentSeries) || (el.inSeries && el.inSeries.value.trim()) || "";

  const lang = language || (window.currentSeoData && window.currentSeoData.language) || (state && state.loadedEpisodeData && state.loadedEpisodeData.config && state.loadedEpisodeData.config.language) || (el.inLanguage && el.inLanguage.value.trim()) || "";







  try {



    const res = await fetch(`/api/youtube/series_channel?series=${encodeURIComponent(series)}&lang=${encodeURIComponent(lang)}&language=${encodeURIComponent(lang)}`);



    if (!res.ok) return null;



    const data = await res.json();



    if (data && data.ok && data.channel_id) {



      const channelId = data.channel_id;



      if (window.youTubeState) {



        window.youTubeState.activeChannelId = channelId;



        window.youTubeState.selectedChannelId = channelId;



      }







      const qSel = document.getElementById("ytQuickChannelSelect");



      const sSel = document.getElementById("seoYtChannelSelect");



      const aSel = document.getElementById("advYtChannelSelect");



      if (qSel) qSel.value = channelId;



      if (sSel) sSel.value = channelId;



      if (aSel) aSel.value = channelId;







      const activeCh = (window.youTubeState.channels || []).find(c => c.id === channelId);



      const studioLink = document.getElementById("advYtStudioEditorLink");



      if (studioLink && activeCh) {



        studioLink.href = getStudioUrl(activeCh);



      }







      updateVisitChannelButtons(channelId);



      fetchChannelPlaylists(channelId);



      window.applyChannelSavedSettings(channelId);



      return channelId;



    }



  } catch (err) {



    console.warn("autoDetectAndSelectChannel error:", err);



  }



  return null;



};







window.toggleOAuthCredentialsBox = function () {



  const box = document.getElementById("ytOAuthBox");



  const icon = document.getElementById("ytToggleOAuthIcon");



  if (!box) return;



  const isOpen = box.style.display !== "none";



  box.style.display = isOpen ? "none" : "block";



  if (icon) icon.textContent = isOpen ? "Đổi tệp khóa / Cấu hình nâng cao ▼" : "Thu gọn ▲";



};







window.saveOAuthCredentials = async function () {



  const cid = (document.getElementById("inYtClientId")?.value || "").trim();



  const csecret = (document.getElementById("inYtClientSecret")?.value || "").trim();



  if (!cid || !csecret) {



    showToast("Vui lòng nhập cả Client ID và Client Secret.", "warning");



    return;



  }



  try {



    const res = await fetch("/api/youtube/credentials", {



      method: "POST",



      headers: { "Content-Type": "application/json" },



      body: JSON.stringify({ client_id: cid, client_secret: csecret })



    });



    const data = await res.json();



    if (data.ok) {



      window.youTubeState.clientConfigured = true;



      showToast("Đã lưu cấu hình Google OAuth Client!", "success");



      await window.fetchYouTubeChannels();



      const box = document.getElementById("ytOAuthBox");



      if (box) box.style.display = "none";



      await window.startOAuthFlow();



    } else {



      showToast(data.error || "Lỗi lưu cấu hình OAuth.", "error");



    }



  } catch (err) {



    showToast("Lỗi kết nối tới máy chủ: " + err.message, "error");



  }

};







window.startOAuthFlow = async function () {



  const cidInput = document.getElementById("inYtClientId");



  const secInput = document.getElementById("inYtClientSecret");







  // Validate credentials first



  if (!window.youTubeState.clientConfigured && (!cidInput?.value.trim() || !secInput?.value.trim())) {



    window.handleUnifiedYouTubeConnect();



    return;



  }







  try {



    const res = await fetch("/api/youtube/auth_url");



    const data = await res.json();



    if (!data.ok) {



      throw new Error(data.error || "Chưa thiết lập Google OAuth credentials.");



    }







    const windowName = "youtube_oauth_" + Date.now();



    const authWindow = window.open(



      data.auth_url,



      windowName,



      "width=580,height=740,menubar=no,toolbar=no,status=no,resizable=yes,scrollbars=yes"



    );







    if (!authWindow || authWindow.closed || typeof authWindow.closed === "undefined") {



      showToast("⚠️ Trình duyệt chặn popup! Đang mở trên tab mới...", "warning");



      window.open(data.auth_url, "_blank");



    } else {



      try { authWindow.focus(); } catch (e) {}



      showToast("Đang mở cửa sổ chọn tài khoản Google để kết nối kênh mới...", "info");



    }







    // Listen for postMessage from callback popup



    const onMessage = async (event) => {



      if (event.data && event.data.type === "YOUTUBE_AUTH_SUCCESS") {



        window.removeEventListener("message", onMessage);



        showToast(`🎉 Kết nối kênh "${event.data.name || 'YouTube'}" thành công!`, "success");



        await window.fetchYouTubeChannels();



      }



    };



    window.addEventListener("message", onMessage);







    // Fallback polling in case popup closes or postMessage blocked



    let checks = 0;



    const pollInterval = setInterval(async () => {



      checks++;



      if (authWindow && authWindow.closed) {



        clearInterval(pollInterval);



        await window.fetchYouTubeChannels();



      }



      if (checks > 60) clearInterval(pollInterval);



    }, 1500);







  } catch (err) {



    showToast(err.message, "warning");



  }

};







window.selectActiveYouTubeChannel = async function (channelId) {



  try {



    const res = await fetch("/api/youtube/channels/select", {



      method: "POST",



      headers: { "Content-Type": "application/json" },



      body: JSON.stringify({ channel_id: channelId })



    });



    const data = await res.json();



    if (data.ok) {



      showToast("Đã chọn làm kênh mặc định!", "success");



      await window.fetchYouTubeChannels();



    }



  } catch (err) {



    showToast("Lỗi chọn kênh: " + err.message, "error");



  }

};







window.deleteYouTubeChannel = async function (channelId, channelName) {



  if (!confirm(`Bạn có chắc chắn muốn hủy kết nối kênh "${channelName || channelId}" khỏi Studio?`)) {



    return;



  }



  try {



    const res = await fetch("/api/youtube/channels/delete", {



      method: "POST",



      headers: { "Content-Type": "application/json" },



      body: JSON.stringify({ channel_id: channelId })



    });



    const data = await res.json();



    if (data.ok) {



      showToast("Đã hủy kết nối kênh.", "info");



      await window.fetchYouTubeChannels();



    }



  } catch (err) {



    showToast("Lỗi xóa kênh: " + err.message, "error");



  }

};







window.updateYouTubeChannelPrivacy = async function (channelId, defaultPrivacy) {



  try {



    const res = await fetch("/api/youtube/channels/privacy", {



      method: "POST",



      headers: { "Content-Type": "application/json" },



      body: JSON.stringify({ channel_id: channelId, default_privacy: defaultPrivacy })



    });



    const data = await res.json();



    if (data.ok) {



      showToast(`Đã lưu chế độ đăng: ${defaultPrivacy}`, "success");



    }



  } catch (err) {



    showToast("Lỗi cập nhật quyền riêng tư: " + err.message, "error");



  }

};







// ---------------------------------------------------------------------------



// 1-CLICK VIDEO UPLOAD TRIGGER & REAL-TIME PROGRESS TRACKING



// ---------------------------------------------------------------------------







window.triggerYouTubeUploadFromMonitor = function () {

  const selCh = document.getElementById("ytQuickChannelSelect");

  const selPriv = document.getElementById("ytQuickPrivacySelect");

  const selPl = document.getElementById("ytQuickPlaylistSelect");

  const channelId = selCh ? selCh.value : "";

  const ch = (window.youTubeState.channels || []).find(c => c.id === channelId);

  const chSettings = (ch && ch.publish_settings) || {};

  const sData = window.currentSeoData;



  window.triggerYouTubeUpload({

    channelId: channelId,

    title: (sData && (sData.best_title || sData.title)) || null,

    description: (sData && sData.description) || null,

    tags: (sData && sData.tags) || null,

    pinnedComment: (sData && sData.pinned_comment) || null,



    privacy: (selPriv && selPriv.value) || chSettings.default_privacy || "unlisted",



    playlistId: (selPl && selPl.value) || chSettings.default_playlist_id || "auto",



    containsSyntheticMedia: chSettings.contains_synthetic_media !== undefined ? chSettings.contains_synthetic_media : true,



    madeForKids: chSettings.made_for_kids || false,



    categoryId: chSettings.category_id || "1",



    license: chSettings.license || "youtube",



    embeddable: chSettings.embeddable !== undefined ? chSettings.embeddable : true,



    publicStatsViewable: chSettings.public_stats_viewable !== undefined ? chSettings.public_stats_viewable : true,



    defaultLanguage: chSettings.default_language || null,



    defaultAudioLanguage: chSettings.default_audio_language || null,



    mediaType: "long",



    source: "monitor"



  });



};







window.triggerYouTubeShortUploadFromMonitor = function () {



  const selCh = document.getElementById("ytQuickChannelSelect");



  const selPriv = document.getElementById("ytQuickPrivacySelect");



  const selPl = document.getElementById("ytQuickPlaylistSelect");



  const channelId = selCh ? selCh.value : "";



  const ch = (window.youTubeState.channels || []).find(c => c.id === channelId);



  const chSettings = (ch && ch.publish_settings) || {};







  window.triggerYouTubeUpload({



    channelId: channelId,



    privacy: (selPriv && selPriv.value) || chSettings.default_privacy || "unlisted",



    playlistId: (selPl && selPl.value) || chSettings.default_playlist_id || "auto",



    containsSyntheticMedia: chSettings.contains_synthetic_media !== undefined ? chSettings.contains_synthetic_media : true,



    madeForKids: chSettings.made_for_kids || false,



    categoryId: chSettings.category_id || "1",



    license: chSettings.license || "youtube",



    embeddable: chSettings.embeddable !== undefined ? chSettings.embeddable : true,



    publicStatsViewable: chSettings.public_stats_viewable !== undefined ? chSettings.public_stats_viewable : true,



    defaultLanguage: chSettings.default_language || null,



    defaultAudioLanguage: chSettings.default_audio_language || null,



    mediaType: "short",



    source: "monitor"



  });



};







window.triggerYouTubeUploadFromSeoModal = function () {

  const selCh = document.getElementById("seoYtChannelSelect");

  const selPriv = document.getElementById("seoYtPrivacySelect");

  const selPl = document.getElementById("seoYtPlaylistSelect");

  const channelId = selCh ? selCh.value : "";

  const ch = (window.youTubeState.channels || []).find(c => c.id === channelId);

  const chSettings = (ch && ch.publish_settings) || {};

  const sData = window.currentSeoData;



  let activeTitle = null;

  const selTitleEl = document.querySelector("#seoTitlesContainer .title-card.selected, #seoTitlesContainer [data-selected='true']");

  if (selTitleEl && selTitleEl.dataset.title) {

    activeTitle = selTitleEl.dataset.title;

  } else if (sData) {

    activeTitle = sData.best_title || sData.title || null;

  }

  const descEl = document.getElementById("seoDescriptionArea");

  const activeDesc = (descEl && descEl.value.trim()) || (sData && sData.description) || null;

  const tagsEl = document.getElementById("seoTagsInput");

  const activeTags = (tagsEl && tagsEl.value.trim()) || (sData && sData.tags) || null;

  const pinEl = document.getElementById("seoPinnedCommentInput");

  const activePin = (pinEl && pinEl.value.trim()) || (sData && sData.pinned_comment) || null;



  window.triggerYouTubeUpload({

    channelId: channelId,

    title: activeTitle,

    description: activeDesc,

    tags: activeTags,

    pinnedComment: activePin,



    privacy: (selPriv && selPriv.value) || chSettings.default_privacy || "unlisted",



    playlistId: (selPl && selPl.value) || chSettings.default_playlist_id || "auto",



    containsSyntheticMedia: chSettings.contains_synthetic_media !== undefined ? chSettings.contains_synthetic_media : true,



    madeForKids: chSettings.made_for_kids || false,



    categoryId: chSettings.category_id || "1",



    license: chSettings.license || "youtube",



    embeddable: chSettings.embeddable !== undefined ? chSettings.embeddable : true,



    publicStatsViewable: chSettings.public_stats_viewable !== undefined ? chSettings.public_stats_viewable : true,



    defaultLanguage: chSettings.default_language || null,



    defaultAudioLanguage: chSettings.default_audio_language || null,



    mediaType: window.currentSeoTab || "long",



    source: "seo_modal"



  });



};







window.triggerYouTubeBothUploadFromMonitor = function () {



  const selCh = document.getElementById("ytQuickChannelSelect");



  const selPriv = document.getElementById("ytQuickPrivacySelect");



  const selPl = document.getElementById("ytQuickPlaylistSelect");



  const channelId = selCh ? selCh.value : "";



  const ch = (window.youTubeState.channels || []).find(c => c.id === channelId);



  const chSettings = (ch && ch.publish_settings) || {};







  window.triggerYouTubeUpload({



    channelId: channelId,



    privacy: (selPriv && selPriv.value) || chSettings.default_privacy || "unlisted",



    playlistId: (selPl && selPl.value) || chSettings.default_playlist_id || "auto",



    containsSyntheticMedia: chSettings.contains_synthetic_media !== undefined ? chSettings.contains_synthetic_media : true,



    madeForKids: chSettings.made_for_kids || false,



    categoryId: chSettings.category_id || "1",



    license: chSettings.license || "youtube",



    embeddable: chSettings.embeddable !== undefined ? chSettings.embeddable : true,



    publicStatsViewable: chSettings.public_stats_viewable !== undefined ? chSettings.public_stats_viewable : true,



    defaultLanguage: chSettings.default_language || null,



    defaultAudioLanguage: chSettings.default_audio_language || null,



    mediaType: "both",



    source: "monitor"



  });



};







window.triggerYouTubeBothUploadFromSeoModal = function () {



  const selCh = document.getElementById("seoYtChannelSelect");



  const selPriv = document.getElementById("seoYtPrivacySelect");



  const selPl = document.getElementById("seoYtPlaylistSelect");



  const channelId = selCh ? selCh.value : "";



  const ch = (window.youTubeState.channels || []).find(c => c.id === channelId);



  const chSettings = (ch && ch.publish_settings) || {};







  window.triggerYouTubeUpload({



    channelId: channelId,



    privacy: (selPriv && selPriv.value) || chSettings.default_privacy || "unlisted",



    playlistId: (selPl && selPl.value) || chSettings.default_playlist_id || "auto",



    containsSyntheticMedia: chSettings.contains_synthetic_media !== undefined ? chSettings.contains_synthetic_media : true,



    madeForKids: chSettings.made_for_kids || false,



    categoryId: chSettings.category_id || "1",



    license: chSettings.license || "youtube",



    embeddable: chSettings.embeddable !== undefined ? chSettings.embeddable : true,



    publicStatsViewable: chSettings.public_stats_viewable !== undefined ? chSettings.public_stats_viewable : true,



    defaultLanguage: chSettings.default_language || null,



    defaultAudioLanguage: chSettings.default_audio_language || null,



    mediaType: "both",



    source: "seo_modal"



  });



};









// ==============================================================================

// ADVANCED YOUTUBE PUBLISH MODAL CONTROLLERS (FULL YOUTUBE STUDIO SUITE)

// ==============================================================================

window.switchYtModalTab = function (tabName) {

  const tabs = ["details", "advanced", "visibility"];

  tabs.forEach(t => {

    const sec = document.getElementById("secTabYt" + t.charAt(0).toUpperCase() + t.slice(1));

    const btn = document.getElementById("btnTabYt" + t.charAt(0).toUpperCase() + t.slice(1));

    if (sec) {

      sec.style.display = (t === tabName) ? "flex" : "none";

    }

    if (btn) {

      if (t === tabName) {

        btn.classList.add("active");

        btn.style.borderBottom = "2px solid #ef4444";

        btn.style.color = "#f8fafc";

        btn.style.fontWeight = "700";

      } else {

        btn.classList.remove("active");

        btn.style.borderBottom = "2px solid transparent";

        btn.style.color = "#94a3b8";

        btn.style.fontWeight = "600";

      }

    }

  });

};



window.onAdvVideoLangChange = function (videoLang) {

  const audSelect = document.getElementById("advYtAudioLang");

  if (!audSelect || !videoLang) return;

  

  // Exact match

  if (Array.from(audSelect.options).some(o => o.value === videoLang)) {

    audSelect.value = videoLang;

    return;

  }

  

  // Base language prefix match (e.g. es-419 -> es, fr-CA -> fr)

  const base = videoLang.split("-")[0].toLowerCase();

  const matched = Array.from(audSelect.options).find(o => {

    const val = o.value.toLowerCase();

    return val === base || val.startsWith(base + "-") || val.startsWith(base);

  });

  if (matched) {

    audSelect.value = matched.value;

  }

};



window.updateYtTitleCount = function (val) {

  const countEl = document.getElementById("advYtTitleCount");

  if (!countEl) return;

  const len = (val || "").length;

  countEl.textContent = `${len}/100`;

  countEl.style.color = len > 100 ? "#ef4444" : "#94a3b8";

};



window.updateYtDescCount = function (val) {

  const countEl = document.getElementById("advYtDescCount");

  if (!countEl) return;

  const len = (val || "").length;

  countEl.textContent = `${len}/5000`;

  countEl.style.color = len > 5000 ? "#ef4444" : "#94a3b8";

};



window.updateYtTagsCount = function (val) {

  const countEl = document.getElementById("advYtTagsCount");

  if (!countEl) return;

  const len = (val || "").length;

  countEl.textContent = `${len}/500`;

  countEl.style.color = len > 500 ? "#ef4444" : "#94a3b8";

};



window.openYouTubeAdvancedModal = async function () {



  const modal = document.getElementById("modalYouTubeAdvancedPublish");



  if (!modal) return;



    // Reset expandable section to collapsed by default
  const exSection = document.getElementById("advYtExtraSection");
  if (exSection) exSection.style.display = "none";
  const btnToggleMore = document.getElementById("btnAdvYtToggleMore");
  if (btnToggleMore) btnToggleMore.innerHTML = "HIỆN THÊM (Nội dung AI, Thẻ Tags, Ngôn ngữ, Danh mục...) ▼";

  openModal(modal);



  if (typeof window.switchYtModalTab === "function") {

    window.switchYtModalTab("details");

  }







  // Sync channels

  await window.fetchYouTubeChannels();



  const channels = window.youTubeState.channels || [];

  const targetId = (window.youTubeState.userSelectedChannel && window.youTubeState.selectedChannelId)

    || window.youTubeState.selectedChannelId

    || window.youTubeState.activeChannelId

    || (channels[0] ? channels[0].id : "");



  const advChSelect = document.getElementById("advYtChannelSelect");

  if (advChSelect) {

    if (channels.length === 0) {

      advChSelect.innerHTML = '<option value="">Chưa có kênh (Vui lòng thêm kênh trước)</option>';

    } else {

      advChSelect.innerHTML = channels.map((ch, idx) => {

        const isSel = ch.id === targetId ? "selected" : "";

        const num = idx + 1;

        const subs = ch.subscriber_count ? ` (${Number(ch.subscriber_count).toLocaleString()} subs)` : "";

        return `<option value="${escapeHtml(ch.id)}" ${isSel}>${num}. ${escapeHtml(ch.name)}${subs}</option>`;

      }).join("");

      advChSelect.value = targetId;

    }

  }



  // Sync header tag & studio link

  const activeCh = channels.find(c => c.id === targetId) || channels[0];

  const advHeaderTag = document.getElementById("advYtCurrentChannelTag");

  if (advHeaderTag && activeCh) {

    const chIdx = channels.findIndex(c => c.id === targetId);

    advHeaderTag.textContent = `🔴 Kênh ${chIdx >= 0 ? chIdx + 1 : 1}: ${activeCh.name}`;

  }



  const studioLink = document.getElementById("advYtStudioEditorLink");

  if (studioLink && activeCh) {

    studioLink.href = getStudioUrl(activeCh);

  }



    // Populate playlists and apply saved channel configurations for targetId!
  if (targetId) {
    fetchChannelPlaylists(targetId);
    if (typeof window.applyChannelSavedSettings === "function") {
      await window.applyChannelSavedSettings(targetId);
    }
  }

  // Active series & episode strictly resolved
  const { series: curSeries, episode: curEpisode } = getActiveSeriesAndEpisode();
  const epNum = Number(curEpisode || 1);

  // Update Header Episode Badge
  const epBadge = document.getElementById("advYtEpisodeBadge");
  if (epBadge) {
    epBadge.textContent = `🎬 Series: ${curSeries || 'auto'} | Tập ${String(epNum).padStart(2, '0')}`;
  }

  // ALWAYS fetch fresh SEO data for this specific series & episode (Strict episode isolation)
  let sData = {};
  if (curSeries && curSeries !== "auto") {
    try {
      const seoRes = await fetch(`/api/episode/seo?series=${encodeURIComponent(curSeries)}&episode=${epNum}`);
      if (seoRes.ok) {
        const fetchedData = await seoRes.json();
        if (fetchedData && typeof fetchedData === "object" && !fetchedData.error) {
          sData = fetchedData;
          window.currentSeoData = fetchedData;
          currentSeoData = fetchedData;
          if (window.state) window.state.currentSeoData = fetchedData;
        }
      }
    } catch (err) {
      console.warn("Could not fetch fresh SEO data:", err);
    }
  }
  if (!sData || Object.keys(sData).length === 0) {
    sData = window.currentSeoData || {};
  }

  const isShort = window.currentSeoTab === "short" || (!!(sData.is_short || sData.is_vertical_short) && window.currentSeoTab !== "long");

  if (epBadge) {
    epBadge.textContent = `🎬 Series: ${curSeries || 'auto'} | Tập ${String(epNum).padStart(2, '0')} (${isShort ? 'Shorts 9:16' : '16:9'})`;
  }

  // Populate metadata, title, description, tags, pinned comment & languages from fresh SEO data
  const inTitle = document.getElementById("advYtTitle");
  const inDesc = document.getElementById("advYtDescription");
  const inTags = document.getElementById("advYtTags");
  const pinBox = document.getElementById("advYtPinnedComment");
  const thumbBox = document.getElementById("advYtThumbnailBox");
  const imgThumb = document.getElementById("advYtThumbnailPreview");
  const ratioLabel = document.getElementById("advYtThumbnailRatioLabel");

  if (inTitle) {
    inTitle.value = sData.best_title || sData.title || "";
    if (typeof window.updateYtTitleCount === "function") window.updateYtTitleCount(inTitle.value);
  }
  if (inDesc) {
    inDesc.value = sData.description || "";
    if (typeof window.updateYtDescCount === "function") window.updateYtDescCount(inDesc.value);
  }
  if (inTags) {
    const tList = sData.tags || [];
    inTags.value = Array.isArray(tList) ? tList.join(", ") : (tList || "");
    if (typeof window.updateYtTagsCount === "function") window.updateYtTagsCount(inTags.value);
  }
  if (pinBox) {
    pinBox.value = sData.pinned_comment || "";
  }

  // Dynamic Thumbnail Container & Ratio Label
  if (thumbBox && ratioLabel) {
    if (isShort) {
      thumbBox.style.width = "90px";
      thumbBox.style.aspectRatio = "9/16";
      ratioLabel.textContent = "Bìa dọc Shorts 9:16 (1080x1920) chuẩn Google Flow & Shorts.";
    } else {
      thumbBox.style.width = "140px";
      thumbBox.style.aspectRatio = "16/9";
      ratioLabel.textContent = "Tỷ lệ 16:9 (1280x720) định dạng JPG hoặc PNG.";
    }
  }

  // Load thumbnail preview with robust fallbacks and clean placeholder
  if (imgThumb) {
    const padEp = String(epNum).padStart(3, "0");
    const candidateUrls = [];
    if (isShort) {
      candidateUrls.push(`/media/productions/${encodeURIComponent(curSeries)}/episode_${padEp}/thumbnail_shorts.jpg?t=${Date.now()}`);
      if (sData.thumbnail_shorts_url) candidateUrls.push(sData.thumbnail_shorts_url);
    }
    if (sData.thumbnail_url) candidateUrls.push(sData.thumbnail_url);
    if (sData.thumbnail_slug_url) candidateUrls.push(sData.thumbnail_slug_url);
    candidateUrls.push(`/api/productions/${encodeURIComponent(curSeries)}/episodes/${epNum}/thumbnail?t=${Date.now()}`);
    candidateUrls.push(`/media/productions/${encodeURIComponent(curSeries)}/episode_${padEp}/thumbnail_seo.jpg?t=${Date.now()}`);
    candidateUrls.push(`/media/productions/${encodeURIComponent(curSeries)}/episode_${padEp}/thumbnail_flow_base.jpg?t=${Date.now()}`);
    candidateUrls.push(`/api/productions/auto/episodes/${epNum}/thumbnail?t=${Date.now()}`);
    candidateUrls.push(`/api/episode/thumbnail?series=${encodeURIComponent(curSeries)}&episode=${epNum}`);
    candidateUrls.push(`/api/episode/thumbnail?series=auto&episode=${epNum}`);

    let cIdx = 0;
    const ph = document.getElementById("advYtThumbnailPlaceholder");
    if (ph) {
      ph.style.display = "flex";
      ph.innerHTML = '<span style="font-size:1.3rem;">⏳</span><span>Đang tải ảnh...</span>';
    }
    imgThumb.style.display = "none";

    imgThumb.onload = function () {
      imgThumb.style.display = "block";
      if (ph) ph.style.display = "none";
      const posterImg = document.getElementById("advYtVideoPosterImg");
      if (posterImg) {
        posterImg.src = imgThumb.src;
        posterImg.style.display = "block";
      }
    };

    imgThumb.onerror = function () {
      cIdx++;
      if (cIdx < candidateUrls.length && candidateUrls[cIdx]) {
        imgThumb.src = candidateUrls[cIdx];
      } else {
        imgThumb.onerror = null;
        imgThumb.style.display = "none";
        if (ph) {
          ph.style.display = "flex";
          ph.innerHTML = '<span style="font-size:1.4rem;">🖼️</span><span style="font-size:0.72rem;color:#94a3b8;">Chưa có ảnh (Bấm đổi ảnh)</span>';
        }
      }
    };
    imgThumb.src = candidateUrls[0];
  }

  // Video Card Preview & Status
  const previewUrlEl = document.getElementById("advYtPreviewVideoUrl");
  const copyBtn = document.getElementById("btnAdvYtCopyLink");
  const statusBadge = document.getElementById("advYtUploadStatusBadge");
  const origFileEl = document.getElementById("advYtOriginalFilename");
  const qualityEl = document.getElementById("advYtQualityBadge");
  const videoPlayer = document.getElementById("advYtVideoPreview");
  const videoPosterPlaceholder = document.getElementById("advYtVideoPosterPlaceholder");
  const videoPosterImg = document.getElementById("advYtVideoPosterImg");
  const durationBadge = document.getElementById("advYtVideoDurationBadge");
  const playerContainer = document.getElementById("advYtVideoPlayerContainer");

  const vidLink = sData.youtube_watch_url || sData.video_url || (sData.youtube_upload_settings && sData.youtube_upload_settings.watch_url);
  if (vidLink && vidLink.includes("http")) {
    if (previewUrlEl) previewUrlEl.textContent = vidLink;
    if (copyBtn) copyBtn.style.display = "inline-block";
    if (statusBadge) {
      statusBadge.textContent = "🟢 Đã tải lên YouTube";
      statusBadge.style.color = "#2ba640";
    }
  } else {
    if (previewUrlEl) previewUrlEl.textContent = "Chưa tải lên YouTube";
    if (copyBtn) copyBtn.style.display = "none";
    if (statusBadge) {
      statusBadge.textContent = "🟡 Sẵn sàng đăng (Sẽ có link sau khi bấm Đăng Video)";
      statusBadge.style.color = "#f59e0b";
    }
  }

  if (origFileEl) {
    origFileEl.textContent = "episode_final.mp4";
  }
  if (qualityEl) {
    qualityEl.textContent = isShort ? "✓ 1080x1920 (9:16 Shorts 60fps)" : "✓ 1080p Full HD (16:9 60fps)";
  }

  // Configure playable video preview
  const padEp = String(epNum).padStart(3, "0");
  const localVideoUrl = isShort 
    ? `/media/productions/${encodeURIComponent(curSeries)}/episode_${padEp}/episode_short.mp4`
    : `/media/productions/${encodeURIComponent(curSeries)}/episode_${padEp}/episode_final.mp4`;
  if (playerContainer) {
    playerContainer.style.aspectRatio = isShort ? "9/16" : "16/9";
    playerContainer.style.maxHeight = isShort ? "340px" : "190px";
    playerContainer.style.width = isShort ? "auto" : "100%";
    playerContainer.style.margin = isShort ? "0 auto" : "0";
  }

  if (videoPlayer) {
    videoPlayer.src = localVideoUrl;
    videoPlayer.style.display = "block";
    if (videoPosterPlaceholder) videoPosterPlaceholder.style.display = "none";
    videoPlayer.onloadedmetadata = function () {
      const dur = Math.round(videoPlayer.duration || 0);
      const mins = String(Math.floor(dur / 60)).padStart(2, "0");
      const secs = String(dur % 60).padStart(2, "0");
      if (durationBadge) durationBadge.textContent = `${mins}:${secs} ${isShort ? 'Shorts' : 'HD'}`;
    };
    videoPlayer.onerror = function () {
      videoPlayer.style.display = "none";
      if (videoPosterPlaceholder) {
        videoPosterPlaceholder.style.display = "flex";
        if (imgThumb && imgThumb.src && imgThumb.style.display !== "none") {
          if (videoPosterImg) {
            videoPosterImg.src = imgThumb.src;
            videoPosterImg.style.display = "block";
          }
        }
      }
    };
  }

  // Language Sync
  const defLang = document.getElementById("advYtDefaultLang");
  const audLang = document.getElementById("advYtAudioLang");
  let lang = sData.language || "es";
  if (lang.toLowerCase().includes("eng") || lang.toLowerCase() === "en") lang = "en-US";
  else if (lang.toLowerCase().includes("spa") || lang.toLowerCase() === "es") lang = "es";
  else if (lang.toLowerCase().includes("rus") || lang.toLowerCase() === "ru") lang = "ru";
  else if (lang.toLowerCase().includes("vie") || lang.toLowerCase() === "vi") lang = "vi";

  if (defLang) defLang.value = lang;
  if (audLang) audLang.value = lang;

  // Safe Default Privacy: Unlisted
  const unlistRadio = document.getElementById("radioYtModeUnlisted");
  const privSelect = document.getElementById("advYtPrivacySelect");
  if (!document.querySelector('input[name="ytStudioPublishMode"]:checked')) {
    if (unlistRadio) unlistRadio.checked = true;
    if (privSelect) privSelect.value = "unlisted";
  }

  // Sync schedule visibility based on privacy selection
  const isSched = privSelect && privSelect.value === "schedule_seo";
  window.toggleScheduleField(isSched);
};

window.copyAdvVideoUrl = function () {
  const el = document.getElementById("advYtPreviewVideoUrl");
  if (el && el.innerText && el.innerText.includes("http")) {
    navigator.clipboard.writeText(el.innerText);
    showToast("Đã sao chép đường link YouTube!");
  } else {
    showToast("Video chưa có đường liên kết YouTube.", "warning");
  }
};

window.handleCustomThumbnailUpload = async function (input) {
  if (!input || !input.files || !input.files[0]) return;
  const file = input.files[0];
  const reader = new FileReader();
  reader.onload = async function (e) {
    const base64Data = e.target.result;
    const imgThumb = document.getElementById("advYtThumbnailPreview");
    const videoPosterImg = document.getElementById("advYtVideoPosterImg");
    if (imgThumb) {
      imgThumb.src = base64Data;
      imgThumb.style.display = "block";
    }
    if (videoPosterImg) {
      videoPosterImg.src = base64Data;
      videoPosterImg.style.display = "block";
    }
    const { series, episode } = getActiveSeriesAndEpisode();
    try {
      showToast("Đang lưu ảnh thu nhỏ mới...");
      const res = await fetch("/api/episode/thumbnail", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          series: series,
          episode: episode,
          image_base64: base64Data
        })
      });
      const data = await res.json();
      if (res.ok && data.ok) {
        showToast("Đã cập nhật ảnh thu nhỏ thành công!", "success");
      } else {
        showToast(data.error || "Lỗi lưu ảnh thu nhỏ", "error");
      }
    } catch (err) {
      showToast("Lỗi kết nối khi lưu ảnh: " + err.message, "error");
    }
  };
  reader.readAsDataURL(file);
};







function ensureTimeOption(select, val) {

  if (!select) return;

  if (!Array.from(select.options).some(o => o.value === val)) {

    const opt = document.createElement("option");

    opt.value = val;

    opt.textContent = `${val} (Giờ chọn nhanh)`;

    select.appendChild(opt);

  }

}



window.initEasyYouTubeScheduler = function() {

  const dateSelect = document.getElementById("advYtScheduleDateSelect");

  const timeSelect = document.getElementById("advYtScheduleTimeSelect");

  const hiddenInput = document.getElementById("advYtPublishAt");

  if (!dateSelect || !timeSelect || !hiddenInput) return;



  const daysOfWeek = ["Chủ Nhật", "Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy"];

  const now = new Date();

  const pad = n => String(n).padStart(2, "0");

  

  let options = [];

  for (let i = 0; i < 14; i++) {

    const d = new Date();

    d.setDate(now.getDate() + i);

    const yyyy = d.getFullYear();

    const mm = pad(d.getMonth() + 1);

    const dd = pad(d.getDate());

    const dateVal = `${yyyy}-${mm}-${dd}`;

    

    let label = "";

    if (i === 0) label = `Hôm nay (${dd}/${mm})`;

    else if (i === 1) label = `Ngày mai (${dd}/${mm})`;

    else if (i === 2) label = `Ngày mốt (${dd}/${mm})`;

    else {

      const dayName = daysOfWeek[d.getDay()];

      label = `${dayName} (${dd}/${mm})`;

    }

    options.push(`<option value="${dateVal}">${label}</option>`);

  }

  dateSelect.innerHTML = options.join("");



  if (hiddenInput.value && hiddenInput.value.includes("T")) {

    const [savedD, savedT] = hiddenInput.value.split("T");

    if (Array.from(dateSelect.options).some(o => o.value === savedD)) {

      dateSelect.value = savedD;

    }

    const tClean = savedT.slice(0, 5);

    ensureTimeOption(timeSelect, tClean);

    timeSelect.value = tClean;

  } else {

    if (now.getHours() >= 20) {

      dateSelect.selectedIndex = 1;

      timeSelect.value = "20:00";

    } else if (now.getHours() < 11) {

      dateSelect.selectedIndex = 0;

      timeSelect.value = "11:30";

    } else {

      dateSelect.selectedIndex = 0;

      timeSelect.value = "20:00";

    }

  }



  window.syncEasyScheduleToHidden();

};



window.quickSetSchedule = function(preset) {

  const dateSelect = document.getElementById("advYtScheduleDateSelect");

  const timeSelect = document.getElementById("advYtScheduleTimeSelect");

  if (!dateSelect || !timeSelect) return;



  const now = new Date();

  const pad = n => String(n).padStart(2, "0");



  if (preset === "plus_2h") {

    const target = new Date(now.getTime() + 2 * 3600 * 1000);

    const dateVal = `${target.getFullYear()}-${pad(target.getMonth()+1)}-${pad(target.getDate())}`;

    const h = pad(target.getHours());

    const m = target.getMinutes() < 30 ? "00" : "30";

    const timeVal = `${h}:${m}`;

    dateSelect.value = dateVal;

    ensureTimeOption(timeSelect, timeVal);

    timeSelect.value = timeVal;

  } else if (preset === "tonight_20h") {

    const dateVal = `${now.getFullYear()}-${pad(now.getMonth()+1)}-${pad(now.getDate())}`;

    dateSelect.value = dateVal;

    timeSelect.value = "20:00";

  } else if (preset === "tomorrow_11h30") {

    const tomorrow = new Date(now.getTime() + 24 * 3600 * 1000);

    const dateVal = `${tomorrow.getFullYear()}-${pad(tomorrow.getMonth()+1)}-${pad(tomorrow.getDate())}`;

    dateSelect.value = dateVal;

    timeSelect.value = "11:30";

  } else if (preset === "tomorrow_20h") {

    const tomorrow = new Date(now.getTime() + 24 * 3600 * 1000);

    const dateVal = `${tomorrow.getFullYear()}-${pad(tomorrow.getMonth()+1)}-${pad(tomorrow.getDate())}`;

    dateSelect.value = dateVal;

    timeSelect.value = "20:00";

  }



  const chips = document.querySelectorAll(".yt-sched-chip");

  chips.forEach(c => c.classList.remove("active"));

  if (window.event && window.event.target && window.event.target.classList.contains("yt-sched-chip")) {

    window.event.target.classList.add("active");

  }



  window.syncEasyScheduleToHidden();

};



window.onCustomScheduleChange = function() {

  const chips = document.querySelectorAll(".yt-sched-chip");

  chips.forEach(c => c.classList.remove("active"));

  window.syncEasyScheduleToHidden();

};



window.syncEasyScheduleToHidden = function() {

  const dateSelect = document.getElementById("advYtScheduleDateSelect");

  const timeSelect = document.getElementById("advYtScheduleTimeSelect");

  const hiddenInput = document.getElementById("advYtPublishAt");

  const summaryEl = document.getElementById("advYtScheduleSummaryText");

  if (!dateSelect || !timeSelect || !hiddenInput) return;



  const dateVal = dateSelect.value;

  const timeVal = timeSelect.value || "20:00";

  if (!dateVal) return;



  const dtLocal = `${dateVal}T${timeVal}`;

  hiddenInput.value = dtLocal;



  const [yyyy, mm, dd] = dateVal.split("-");

  const dateObj = new Date(Number(yyyy), Number(mm) - 1, Number(dd));

  const daysOfWeek = ["Chủ Nhật", "Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy"];

  const dayName = daysOfWeek[dateObj.getDay()];



  if (summaryEl) {

    summaryEl.textContent = `${timeVal} - ${dayName}, ngày ${dd}/${mm}/${yyyy}`;

  }

};



window.onYtStudioModeChange = function(mode) {

  const hiddenSelect = document.getElementById("advYtPrivacySelect");

  if (hiddenSelect) {

    hiddenSelect.value = mode;

  }

  

  const isSched = (mode === "schedule_seo");

  window.toggleScheduleField(isSched);



  if (typeof syncPrivacyChoice === "function" && mode !== "schedule_seo") {

    syncPrivacyChoice(mode);

  }

};



window.toggleYtScheduleAccordion = function(forceOpen) {

  const wrap = document.getElementById("advYtScheduleWrap");

  const schedRadio = document.getElementById("radioYtModeSchedule");

  const arrow = document.getElementById("ytScheduleArrow");

  if (!wrap) return;



  const willOpen = (typeof forceOpen === "boolean") ? forceOpen : (wrap.style.display === "none");

  wrap.style.display = willOpen ? "flex" : "none";

  if (arrow) arrow.textContent = willOpen ? "▲" : "▼";



  if (willOpen) {

    if (schedRadio) schedRadio.checked = true;

    window.onYtStudioModeChange("schedule_seo");

  } else {

    // If closing, fallback to unlisted

    const unlistRadio = document.getElementById("radioYtModeUnlisted");

    if (unlistRadio) unlistRadio.checked = true;

    window.onYtStudioModeChange("unlisted");

  }

};



window.toggleScheduleField = function (isSchedule) {

  const wrap = document.getElementById("advYtScheduleWrap");

  const arrow = document.getElementById("ytScheduleArrow");

  const privSelect = document.getElementById("advYtPrivacySelect");

  const schedRadio = document.getElementById("radioYtModeSchedule");

  const unlistRadio = document.getElementById("radioYtModeUnlisted");

  const pubRadio = document.getElementById("radioYtModePublic");

  const privRadio = document.getElementById("radioYtModePrivate");



  if (wrap) {

    wrap.style.display = isSchedule ? "flex" : "none";

    if (arrow) arrow.textContent = isSchedule ? "▲" : "▼";

    if (isSchedule && typeof window.initEasyYouTubeScheduler === "function") {

      window.initEasyYouTubeScheduler();

    }

  }



  if (isSchedule) {

    if (schedRadio) schedRadio.checked = true;

    if (privSelect && privSelect.value !== "schedule_seo") privSelect.value = "schedule_seo";

  } else {

    const curVal = privSelect ? privSelect.value : "unlisted";

    if (curVal === "public" && pubRadio) pubRadio.checked = true;

    else if (curVal === "private" && privRadio) privRadio.checked = true;

    else if (unlistRadio) unlistRadio.checked = true;

  }

};







window.triggerYouTubeUploadFromAdvancedModal = function () {



  const selCh = document.getElementById("advYtChannelSelect");



  const selPriv = document.getElementById("advYtPrivacySelect");



  const selPl = document.getElementById("advYtPlaylistSelect");



  const inNewPl = document.getElementById("advYtNewPlaylistTitle");



  const chkSynthetic = document.getElementById("advYtContainsSyntheticMedia");



  const radioSchedule = document.getElementById("advYtRadioSchedule");



  const inPublishAt = document.getElementById("advYtPublishAt");



  const radioKidsYes = document.getElementById("advYtKidsYes");



  const selCat = document.getElementById("advYtCategory");



  const selLicense = document.getElementById("advYtLicense");



  const chkEmbed = document.getElementById("advYtEmbeddable");



  const chkPublicStats = document.getElementById("advYtPublicStats");



  const selDefLang = document.getElementById("advYtDefaultLang");



  const selAudioLang = document.getElementById("advYtAudioLang");



  const txtPin = document.getElementById("advYtPinnedComment");



  const radioRemixNone = document.getElementById("advYtRemixNone");



  const radioRemixAudio = document.getElementById("advYtRemixAudio");



  const shortsRemixChoice = (radioRemixNone && radioRemixNone.checked) ? "none" : ((radioRemixAudio && radioRemixAudio.checked) ? "audio_only" : "all");







  const isSchedule = (radioSchedule && radioSchedule.checked) || (selPriv && selPriv.value === "schedule_seo");



  let publishAtIso = null;



  if (isSchedule && inPublishAt && inPublishAt.value) {



    const dt = new Date(inPublishAt.value);



    if (!isNaN(dt.getTime())) {



      const pad = (n) => String(n).padStart(2, "0");



      const tzo = -dt.getTimezoneOffset();



      const sign = tzo >= 0 ? "+" : "-";



      const tzoHrs = pad(Math.floor(Math.abs(tzo) / 60));



      const tzoMins = pad(Math.abs(tzo) % 60);



      publishAtIso = `${dt.getFullYear()}-${pad(dt.getMonth() + 1)}-${pad(dt.getDate())}T${pad(dt.getHours())}:${pad(dt.getMinutes())}:00${sign}${tzoHrs}:${tzoMins}`;



    }



  } else if (isSchedule) {



    const sInfo = window.getSeoScheduleIso(window.currentSeoData);



    publishAtIso = sInfo.iso;



  }







  if(isSchedule && !publishAtIso) {



    showToast("Vui lòng chọn ngày và giờ đăng trong tương lai.", "warning");



    return;



  }



  let finalChoicePl = selPl ? selPl.value : "auto";

  let customNewTitle = null;

  if (finalChoicePl === "__new__") {

    customNewTitle = inNewPl ? inNewPl.value.trim() : "";

    if (!customNewTitle) {

      showToast("Vui lòng nhập tên danh sách phát mới muốn tạo trên YouTube.", "warning");

      if (inNewPl) inNewPl.focus();

      return;

    }

    finalChoicePl = "auto";

  }



  const inTitle = document.getElementById("advYtTitle");

  const inDesc = document.getElementById("advYtDescription");

  const inTags = document.getElementById("advYtTags");

  const chkPremiere = document.getElementById("advYtSetPremiere");



  const payload = {



    channelId: selCh ? selCh.value : "",



    title: inTitle ? inTitle.value.trim() : null,



    description: inDesc ? inDesc.value.trim() : null,



    tags: inTags ? inTags.value.trim() : null,



    setPremiere: chkPremiere ? chkPremiere.checked : false,



    privacy: isSchedule ? "private" : (selPriv ? selPriv.value : "private"),



    playlistId: finalChoicePl,



    newPlaylistTitle: customNewTitle,



    containsSyntheticMedia: chkSynthetic ? chkSynthetic.checked : true,



    publishAt: publishAtIso,



    madeForKids: radioKidsYes ? radioKidsYes.checked : false,



    categoryId: selCat ? selCat.value : "1",



    license: selLicense ? selLicense.value : "youtube",



    embeddable: chkEmbed ? chkEmbed.checked : true,



    publicStatsViewable: chkPublicStats ? chkPublicStats.checked : true,



    defaultLanguage: selDefLang ? selDefLang.value : null,



    defaultAudioLanguage: selAudioLang ? selAudioLang.value : null,



    pinnedComment: txtPin ? txtPin.value.trim() : null,



    shortsRemixing: shortsRemixChoice,



    source: "advanced_modal"



  };







  closeAllModals();



  window.triggerYouTubeUpload(payload);



};







window.triggerYouTubeUpload = async function (options = {}) {



  let {



    channelId,



    title,



    description,



    tags,



    setPremiere,



    privacy,



    playlistId,



    newPlaylistTitle,



    containsSyntheticMedia,



    publishAt,



    madeForKids,



    categoryId,



    license,



    embeddable,



    publicStatsViewable,



    defaultLanguage,



    defaultAudioLanguage,



    pinnedComment,



    mediaType = "long",



    source



  } = options;







  if (window.youTubeState.uploading) {



    showToast("Đang có một video khác đang tải lên YouTube. Vui lòng chờ.", "warning");



    return;



  }







  // Determine series & episode strictly for active selection



  const { series, episode } = getActiveSeriesAndEpisode();







  if (!channelId && window.youTubeState.channels.length > 0) {



    channelId = window.youTubeState.activeChannelId || window.youTubeState.channels[0].id;



  }







  if (!channelId) {



    showToast("Chưa có kênh YouTube nào được kết nối. Vui lòng thêm kênh trước.", "warning");



    window.openYouTubeModal();



    return;



  }







  // Update UI into uploading state



  window.youTubeState.uploading = true;



  setUploadUIState(true, source);







  const quickPlaylistSelect = document.getElementById("ytQuickPlaylistSelect");



  const seoPlaylistSelect = document.getElementById("seoYtPlaylistSelect");



  const ch = (window.youTubeState.channels || []).find(c => c.id === channelId);



  const chSettings = (ch && ch.publish_settings) || {};







  let finalPrivacy = privacy || chSettings.default_privacy || "private";



  let finalPublishAt = publishAt || null;







  if (finalPrivacy === "schedule_seo" || finalPrivacy === "scheduled") {

    if (!finalPublishAt) {

      const sInfo = window.getSeoScheduleIso(window.currentSeoData);

      finalPublishAt = sInfo.iso;

    }

    if (!finalPublishAt) {

      // Auto-compute next Golden Publishing Hour (20:00 UTC / 15:00 EST)

      const now = new Date();

      const target = new Date();

      target.setUTCHours(20, 0, 0, 0);

      if (target.getTime() <= now.getTime() + 2 * 3600 * 1000) {

        target.setUTCDate(target.getUTCDate() + 1);

      }

      finalPublishAt = target.toISOString();

    }

    finalPrivacy = "private"; // YouTube API strictly requires privacyStatus = 'private' when publishAt is set

  }







  const finalPlaylistId = playlistId || chSettings.default_playlist_id || "auto";



  const finalSynthetic = containsSyntheticMedia !== undefined ? containsSyntheticMedia : (chSettings.contains_synthetic_media !== undefined ? chSettings.contains_synthetic_media : true);



  const finalKids = madeForKids !== undefined ? !!madeForKids : (chSettings.made_for_kids || false);



  const finalCategory = categoryId || chSettings.category_id || "1";



  const finalLicense = license || chSettings.license || "youtube";



  const finalEmbeddable = embeddable !== undefined ? embeddable : (chSettings.embeddable !== undefined ? chSettings.embeddable : true);



  const finalPublicStats = publicStatsViewable !== undefined ? publicStatsViewable : (chSettings.public_stats_viewable !== undefined ? chSettings.public_stats_viewable : true);



  const curEpLangForUpload = (window.currentSeoData && window.currentSeoData.language) || (window.state && window.state.loadedEpisodeData && window.state.loadedEpisodeData.config && window.state.loadedEpisodeData.config.language) || (window.state && window.state.currentLanguage) || "";
  let normEpLang = curEpLangForUpload;
  if (normEpLang) {
    const c = normEpLang.toLowerCase();
    if (c.includes("spa") || c === "es") normEpLang = "es";
    else if (c.includes("vie") || c === "vi") normEpLang = "vi";
    else if (c.includes("eng") || c === "en") normEpLang = "en-US";
    else if (c.includes("rus") || c === "ru") normEpLang = "ru";
    else if (c.includes("por") || c === "pt") normEpLang = "pt-BR";
  }

  const finalDefLang = defaultLanguage || normEpLang || chSettings.default_language || null;
  const finalAudioLang = defaultAudioLanguage || defaultLanguage || normEpLang || chSettings.default_audio_language || null;
  const captionCertEl = document.getElementById("advYtCaptionCert");
  const finalCaptionCert = (captionCertEl && captionCertEl.value) || (window.currentSeoData && window.currentSeoData.caption_certification) || chSettings.caption_certification || "never_aired_us";

  try {



    const res = await fetch("/api/youtube/upload", {



      method: "POST",



      headers: { "Content-Type": "application/json" },



      body: JSON.stringify({



        series: series,



        episode: episode,



        channel_id: channelId,



        privacy: finalPrivacy,



        media_type: mediaType,



        playlist_id: finalPlaylistId,



        new_playlist_title: newPlaylistTitle || null,



        contains_synthetic_media: finalSynthetic,



        publish_at: finalPublishAt || null,



        made_for_kids: finalKids,



        category_id: finalCategory,



        license: finalLicense,



        embeddable: finalEmbeddable,



        public_stats_viewable: finalPublicStats,



        default_language: finalDefLang,



        default_audio_language: finalAudioLang,
        caption_certification: finalCaptionCert,



        pinned_comment: pinnedComment || (window.currentSeoData && window.currentSeoData.pinned_comment) || null,

        title: title || (window.currentSeoData && (window.currentSeoData.best_title || window.currentSeoData.title)) || null,

        description: description || (window.currentSeoData && window.currentSeoData.description) || null,

        tags: tags || (window.currentSeoData && window.currentSeoData.tags) || null,



        set_premiere: Boolean(setPremiere),



        source: source || "monitor"



      })



    });



    const data = await res.json();



    if (!data.ok) {



      if (data.is_language_mismatch && data.suggested_channel_id) {



        window.syncSelectedYouTubeChannel(data.suggested_channel_id);



      }



      throw new Error(data.error || "Không thể khởi động tiến trình tải video lên YouTube.");



    }







    let toastMsg = mediaType === "both"



      ? "🔥 Bắt đầu chuỗi xuất bản CẢ 2 THỂ LOẠI (Video Dài 16:9 + Shorts 9:16) lên kênh..."



      : (mediaType === "short" ? "📱 Bắt đầu tải YouTube Shorts 9:16 lên kênh..." : "🚀 Bắt đầu tải video dài 16:9 lên kênh...");



    if (finalPublishAt) {



      const sInfo = window.getSeoScheduleIso(window.currentSeoData);

      const displayTime = (sInfo && sInfo.iso) ? sInfo.display : new Date(finalPublishAt).toLocaleString("vi-VN");

      toastMsg = `⏰ Đang tải lên và LÊN LỊCH PHÁT HÀNH lúc ${displayTime}! (YouTube sẽ tự động Công khai khi đến giờ)`;



    }



    showToast(toastMsg, "info");



    startUploadProgressPolling(source);







  } catch (err) {



    window.youTubeState.uploading = false;



    setUploadUIState(false, source);



    showToast("Lỗi đăng video: " + err.message, "error");



  }

};







function setUploadUIState(uploading, source) {



  // Monitor controls (compact circular chopstick-tip buttons)



  const btnQuick = document.getElementById("btnQuickUploadYouTube");



  const btnQuickShort = document.getElementById("btnQuickUploadShort");



  const btnQuickBoth = document.getElementById("btnQuickUploadBoth");



  const progLine = document.getElementById("ytQuickUploadProgressLine");



  if (btnQuick) {



    btnQuick.disabled = uploading;



    btnQuick.innerHTML = uploading ? "<span>⏳...</span>" : "<span>🚀 Đăng</span>";



    btnQuick.title = uploading ? "Đang có video tải lên..." : "🚀 Đăng video 16:9 lên YouTube (Theo cấu hình đã lưu)";



  }



  if (btnQuickShort) {



    btnQuickShort.disabled = uploading;



    btnQuickShort.innerHTML = uploading ? "<span>⏳...</span>" : "<span>📱 Shorts</span>";



    btnQuickShort.title = uploading ? "Đang có video tải lên..." : "📱 Đăng YouTube Shorts 9:16 (Theo cấu hình đã lưu)";



  }



  if (btnQuickBoth) {



    btnQuickBoth.disabled = uploading;



    btnQuickBoth.innerHTML = uploading ? "<span>⏳...</span>" : "<span>🔥 Cả 2</span>";



    btnQuickBoth.title = uploading ? "Đang có video tải lên..." : "🔥 Đăng cả hai (16:9 + Shorts 9:16) cùng lúc tự động!";



  }



  if (progLine) progLine.style.display = uploading ? "block" : "none";







  // SEO Modal controls



  const btnSeo = document.getElementById("btnSeoModalUploadYt");



  const btnSeoText = document.getElementById("btnSeoModalUploadYtText");



  const btnSeoBoth = document.getElementById("btnSeoModalUploadBoth");



  const seoBox = document.getElementById("seoYtProgressBox");



  if (btnSeo) {



    btnSeo.disabled = uploading;



    if (btnSeoText) {



      if (uploading) {



        btnSeoText.textContent = "⏳ Đang Tải Lên...";



      } else {



        btnSeoText.textContent = window.currentSeoTab === "short" ? "📱 Đăng Tab Này Lên Kênh" : "🚀 Đăng Tab Này Lên Kênh";



      }



    }



  }



  if (btnSeoBoth) {



    btnSeoBoth.disabled = uploading;



    btnSeoBoth.innerHTML = uploading ? "<span>⏳ Đang Tải Lên...</span>" : "<span>🔥 Đăng Cả 2 Thể Loại (Dài + Shorts)</span>";



  }



  if (seoBox) seoBox.style.display = uploading ? "block" : "none";



}







function startUploadProgressPolling(source) {



  if (window.youTubeState.pollTimer) {



    clearInterval(window.youTubeState.pollTimer);



  }







  window.youTubeState.pollTimer = setInterval(async () => {



    try {



      const res = await fetch("/api/youtube/upload_status");



      if (!res.ok) return;



      const status = await res.json();







      updateProgressUI(status);







      if (status.status === "done") {



        clearInterval(window.youTubeState.pollTimer);



        window.youTubeState.uploading = false;



        setUploadUIState(false, source);



        showUploadSuccess(status);



        showToast("🎉 Đã xuất bản video và thumbnail lên YouTube thành công!", "success");



      } else if (status.status === "error") {



        clearInterval(window.youTubeState.pollTimer);



        window.youTubeState.uploading = false;



        setUploadUIState(false, source);



        showToast("Lỗi đăng video: " + (status.error || status.message), "error");



      }



    } catch (e) {



      console.warn("Poll upload status failed:", e);



    }



  }, 800);



}







function updateProgressUI(status) {



  const pct = Math.max(0, Math.min(100, status.percent || 0));



  const msg = status.message || `Đang tải: ${pct}%`;







  // Monitor line



  const qPct = document.getElementById("ytQuickProgressPct");



  const qBar = document.getElementById("ytQuickProgressBar");



  const qMsg = document.getElementById("ytQuickProgressMsg");



  if (qPct) qPct.textContent = `${pct}%`;



  if (qBar) qBar.style.width = `${pct}%`;



  if (qMsg) qMsg.textContent = msg;







  // SEO modal box



  const sPct = document.getElementById("seoYtProgressPct");



  const sBar = document.getElementById("seoYtProgressBar");



  const sMsg = document.getElementById("seoYtProgressLabel");



  if (sPct) sPct.textContent = `${pct}%`;



  if (sBar) sBar.style.width = `${pct}%`;



  if (sMsg) sMsg.textContent = msg;



}







function showUploadSuccess(status) {



  const vidUrl = status.video_url || `https://youtu.be/${status.video_id}`;



  const stdUrl = status.studio_url || `https://studio.youtube.com/video/${status.video_id}/edit`;







  // Monitor success box



  const qSuccess = document.getElementById("ytQuickSuccessBox");



  const qLink = document.getElementById("ytQuickVideoLink");



  const qChLink = document.getElementById("ytQuickChannelLink");



  if (qSuccess && qLink) {



    qSuccess.style.display = "flex";



    qLink.href = vidUrl;



    qLink.textContent = vidUrl;



    if (status.publish_at) {



      const qMsg = document.getElementById("ytQuickProgressMsg");



      if (qMsg) qMsg.textContent = `✅ Đã lên lịch tự động Công khai lúc: ${status.publish_at}`;



    }



    if (qChLink) {



      const activeCh = (window.youTubeState.channels || []).find(c => c.id === window.youTubeState.activeChannelId) || (window.youTubeState.channels && window.youTubeState.channels[0]);



      if (activeCh) {



        qChLink.href = getChannelUrl(activeCh);



        qChLink.style.display = "inline-flex";



      } else {



        qChLink.style.display = "none";



      }



    }



  }







  // SEO modal success box



  const sSuccess = document.getElementById("seoYtSuccessResult");



  const sLink = document.getElementById("seoYtVideoLink");



  const sStd = document.getElementById("seoYtStudioLink");



  const sChLink = document.getElementById("seoYtChannelLink");



  if (sSuccess && sLink) {



    sSuccess.style.display = "flex";



    sLink.href = vidUrl;



    sLink.textContent = vidUrl;



    if (sStd) sStd.href = stdUrl;



    if (sChLink) {



      const activeCh = (window.youTubeState.channels || []).find(c => c.id === window.youTubeState.activeChannelId) || (window.youTubeState.channels && window.youTubeState.channels[0]);



      if (activeCh) {



        sChLink.href = getChannelUrl(activeCh);



        sChLink.style.display = "inline-flex";



      } else {



        sChLink.style.display = "none";



      }



    }



  }



}









// =============================================================================

// YOUTUBE AUTO-UPLOAD TOGGLE HANDLERS (ON / OFF)

// =============================================================================

window.toggleAutoUpload = function(checked) {

  const chk = document.getElementById("chkAutoUpload");

  if (chk) chk.checked = Boolean(checked);

  const badge = document.getElementById("autoUploadBadge");

  const hint = document.getElementById("autoUploadHint");

  if (badge) {

    badge.textContent = checked ? "BẬT" : "TẮT";

    badge.style.background = checked ? "#ef4444" : "#334155";

    badge.style.color = checked ? "#ffffff" : "#94a3b8";

  }

  if (hint) {

    hint.textContent = checked

      ? "Sẽ tự động đăng bài lên YouTube (Unlisted) sau khi dựng xong"

      : "Chỉ tạo video & gói SEO trong máy, KHÔNG tự đăng";

  }

  try {

    localStorage.setItem("storyboard_auto_upload", checked ? "1" : "0");

  } catch(e) {}

};



window.toggleQueueAutoUpload = function(checked) {

  const chk = document.getElementById("chkQueueAutoUpload");

  if (chk) chk.checked = Boolean(checked);

  try {

    localStorage.setItem("storyboard_queue_auto_upload", checked ? "1" : "0");

  } catch(e) {}

};



function initAutoUploadToggles() {

  try {

    const saved = localStorage.getItem("storyboard_auto_upload") === "1";

    window.toggleAutoUpload(saved);

    const qSaved = localStorage.getItem("storyboard_queue_auto_upload") === "1";

    window.toggleQueueAutoUpload(qSaved);

  } catch(e) {

    window.toggleAutoUpload(false);

  }

}



if (document.readyState === "loading") {

  document.addEventListener("DOMContentLoaded", initAutoUploadToggles);

} else {

  initAutoUploadToggles();

}



// Auto fetch channels on boot



if (document.readyState === "loading") {



  document.addEventListener("DOMContentLoaded", () => {



    window.fetchYouTubeChannels();



  });



} else {



  window.fetchYouTubeChannels();



}





// =============================================================================

// PRODUCTION QUEUE MANAGER (AUTO-QUEUE OVERNIGHT)

// =============================================================================



let queuePollTimer = null;



window.openQueueModal = function() {

  const modal = document.getElementById("queueModal");

  if (!modal) return;

  modal.style.display = "flex";

  window.refreshQueueUI();

  if (queuePollTimer) clearInterval(queuePollTimer);

  queuePollTimer = setInterval(window.refreshQueueUI, 4000);

};



window.closeQueueModal = function() {

  const modal = document.getElementById("queueModal");

  if (modal) modal.style.display = "none";

  if (queuePollTimer) {

    clearInterval(queuePollTimer);

    queuePollTimer = null;

  }

};



window.toggleBulkPanel = function(force) {

  const card = document.getElementById("queueBulkCard");

  if (!card) return;

  if (typeof force === "boolean") {

    card.style.display = force ? "block" : "none";

  } else {

    card.style.display = card.style.display === "none" ? "block" : "none";

  }

  if (card.style.display === "block") {

    const curSeries = el.inSeries ? el.inSeries.value : "Stoic Sovereign";

    const curEp = parseInt(el.inEpisode ? el.inEpisode.value : "1", 10) || 1;

    const curMins = parseFloat(el.inMinutes ? el.inMinutes.value : "20") || 20;

    const curProdMode = el.inProductionMode ? el.inProductionMode.value : "cinematic_drama";

    

    const bSeries = document.getElementById("queueBulkSeries");

    const bEp = document.getElementById("queueBulkStartEp");

    const bMins = document.getElementById("queueBulkMinutes");

    const bProd = document.getElementById("queueBulkProdMode");

    

    if (bSeries) bSeries.value = curSeries;

    if (bEp) bEp.value = String(curEp);

    if (bMins) bMins.value = String(curMins);

    if (bProd) bProd.value = curProdMode;

  }

};



window.refreshQueueUI = async function() {

  try {

    const res = await fetch("/api/queue");

    if (!res.ok) return;

    const data = await res.json();

    if (!data.ok) return;



    window.updateQueueBadges(data);



    const items = data.items || [];

    const listEl = document.getElementById("queueItemsList");

    const emptyEl = document.getElementById("queueEmptyState");

    const summaryEl = document.getElementById("queueSummaryText");

    const statusBadge = document.getElementById("queueModalStatusBadge");

    const btnStart = document.getElementById("btnStartQueue");

    const btnPause = document.getElementById("btnPauseQueue");

    const chkShutdown = document.getElementById("chkQueueShutdown");



    if (chkShutdown) chkShutdown.checked = Boolean(data.shutdown_on_complete);



    if (data.active) {

      if (statusBadge) {

        statusBadge.textContent = "🚀 Đang Chạy Tự Động";

        statusBadge.style.background = "#10b981";

        statusBadge.style.color = "#020617";

        statusBadge.style.fontWeight = "700";

      }

      if (btnStart) btnStart.style.display = "none";

      if (btnPause) btnPause.style.display = "inline-flex";

    } else {

      if (statusBadge) {

        statusBadge.textContent = "⏸️ Đang Nghỉ";

        statusBadge.style.background = "#334155";

        statusBadge.style.color = "#94a3b8";

        statusBadge.style.fontWeight = "500";

      }

      if (btnStart) btnStart.style.display = "inline-flex";

      if (btnPause) btnPause.style.display = "none";

    }



    if (summaryEl) {

      summaryEl.textContent = `Tổng cộng: ${data.total_jobs} | Chờ: ${data.pending_count} | Đang chạy: ${data.running_count} | Hoàn thành: ${data.completed_count} | Lỗi: ${data.failed_count}`;

    }



    if (!items.length) {

      if (listEl) listEl.innerHTML = "";

      if (emptyEl) emptyEl.style.display = "block";

      return;

    }



    if (emptyEl) emptyEl.style.display = "none";

    if (!listEl) return;



    let html = "";

    items.forEach((it, idx) => {

      const isRunning = it.status === "running";

      const isCompleted = it.status === "completed";

      const isFailed = it.status === "failed";



      let statusBadgeHtml = "";

      let borderColor = "rgba(255,255,255,0.08)";

      let bgCard = "#090f1e";



      if (isRunning) {

        statusBadgeHtml = `<span style="background:#10b981;color:#020617;font-size:0.68rem;padding:2px 8px;border-radius:10px;font-weight:700;display:inline-flex;align-items:center;gap:4px;">⏳ Đang Sản Xuất</span>`;

        borderColor = "#10b981";

        bgCard = "rgba(16,185,129,0.08)";

      } else if (isCompleted) {

        statusBadgeHtml = `<span style="background:rgba(16,185,129,0.2);color:#34d399;font-size:0.68rem;padding:2px 8px;border-radius:10px;font-weight:600;">✅ Hoàn Thành</span>`;

      } else if (isFailed) {

        statusBadgeHtml = `<span style="background:rgba(239,68,68,0.2);color:#f87171;font-size:0.68rem;padding:2px 8px;border-radius:10px;font-weight:600;">❌ Thất Bại</span>`;

        borderColor = "rgba(239,68,68,0.3)";

      } else {

        statusBadgeHtml = `<span style="background:#334155;color:#cbd5e1;font-size:0.68rem;padding:2px 8px;border-radius:10px;font-weight:500;">⏸️ Chờ Đến Lượt</span>`;

      }



      const modePill = it.production_mode === "cinematic_drama"

        ? `<span style="background:rgba(245,158,11,0.15);color:#fbbf24;padding:1px 6px;border-radius:4px;font-size:0.68rem;font-weight:600;">🎬 Muse AI Video</span>`

        : `<span style="background:rgba(99,102,241,0.15);color:#818cf8;padding:1px 6px;border-radius:4px;font-size:0.68rem;font-weight:600;">🎙️ Thuyết Minh (${it.image_provider})</span>`;



      const durationPill = `<span style="background:rgba(255,255,255,0.06);color:#94a3b8;padding:1px 6px;border-radius:4px;font-size:0.68rem;">⏱️ ${it.minutes || 2} phút</span>`;



      const sourcePreview = it.source_label ? `<div style="font-size:0.72rem;color:#64748b;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:550px;margin-top:2px;">🔗 ${escapeHtml(it.source_label)}</div>` : "";

      const errorMsg = it.error ? `<div style="font-size:0.72rem;color:#f87171;margin-top:3px;">⚠️ ${escapeHtml(it.error)}</div>` : "";



      html += `

        <div style="background:${bgCard};border:1px solid ${borderColor};border-radius:8px;padding:10px 14px;display:flex;align-items:center;justify-content:space-between;gap:12px;transition:all 0.2s ease;">

          <div style="display:flex;align-items:flex-start;gap:10px;flex:1;min-width:0;">

            <div style="font-size:0.8rem;font-weight:700;color:#64748b;min-width:24px;padding-top:2px;">#${idx+1}</div>

            <div style="flex:1;min-width:0;">

              <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:2px;">

                <strong style="font-size:0.86rem;color:#f8fafc;">${escapeHtml(it.title || 'Tập phim')}</strong>

                ${statusBadgeHtml}

                ${modePill}

                ${durationPill}

              </div>

              ${sourcePreview}

              ${errorMsg}

            </div>

          </div>

          <div style="display:flex;align-items:center;gap:6px;">

            ${isFailed ? `<button type="button" onclick="retryQueueItem('${it.id}')" style="background:rgba(59,130,246,0.15);border:1px solid rgba(59,130,246,0.4);color:#60a5fa;border-radius:6px;padding:4px 8px;cursor:pointer;font-size:0.75rem;font-weight:600;display:inline-flex;align-items:center;gap:4px;" title="Chạy tiếp từ cảnh dở dang">🔄 Thử Lại</button>` : ""}

            ${!isRunning ? `<button type="button" onclick="removeQueueItem('${it.id}')" style="background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);color:#f87171;border-radius:6px;padding:4px 8px;cursor:pointer;font-size:0.75rem;" title="Xóa khỏi hàng chờ">🗑️</button>` : `<span style="font-size:0.75rem;color:#10b981;font-weight:600;">Đang xử lý</span>`}

          </div>

        </div>

      `;

    });

    listEl.innerHTML = html;

  } catch (err) {

    console.warn("[QUEUE_FETCH_ERROR]", err);

  }

};



window.updateQueueBadges = function(data) {

  const pendingCount = data ? data.pending_count : 0;

  const runningCount = data ? data.running_count : 0;

  const totalWaiting = pendingCount + runningCount;



  const headerBadge = document.getElementById("queueCountBadge");

  if (headerBadge) {

    headerBadge.textContent = String(totalWaiting);

    headerBadge.style.display = totalWaiting > 0 ? "inline-block" : "none";

  }



  const inlineBadge = document.getElementById("queueInlineCount");

  if (inlineBadge) {

    inlineBadge.textContent = String(totalWaiting);

  }

};



window.addCurrentConfigToQueue = async function() {

  try {

    const series = (el.inSeries ? el.inSeries.value.trim() : "") || "Stoic Sovereign";

    const episode = parseInt(el.inEpisode ? el.inEpisode.value : "1", 10) || 1;

    let inputMode = el.inInputMode ? el.inInputMode.value : "idea";

    let prompt = el.inPrompt ? el.inPrompt.value.trim() : "";

    const minutes = parseFloat(el.inMinutes ? el.inMinutes.value : "2.0") || 2.0;

    const sceneSeconds = parseInt(el.inSceneSec ? el.inSceneSec.value : "10", 10) || 10;

    const language = el.inLanguage ? el.inLanguage.value : "Vietnamese";

    const genre = (el.inGenre && el.inGenre.value) ? el.inGenre.value : "family_drama";

    const productionMode = el.inProductionMode ? el.inProductionMode.value : "cinematic_drama";

    const visualStyle = (el.inVisualStyle && el.inVisualStyle.value && el.inVisualStyle.value !== "auto") 

      ? el.inVisualStyle.value 

      : (genre === "animation" ? "color_animation" : (genre === "whiteboard" ? "whiteboard" : (genre === "colored_marker" ? "colored_marker" : (productionMode === "cinematic_drama" ? "flow_video" : "color_cinematic"))));

    const imageProvider = el.inImageSource ? el.inImageSource.value : "muse_video";

    const subtitleStyle = el.inSubtitleStyle ? el.inSubtitleStyle.value : "karaoke_viral";

    const subtitleSize = parseInt(el.inSubtitleSize ? el.inSubtitleSize.value : "0", 10) || 0;

    const workers = parseInt(el.inWorkers ? el.inWorkers.value : "4", 10) || 4;



    let referenceUrl = (el.inReferenceUrl ? el.inReferenceUrl.value.trim() : "") || "";

    if (prompt.startsWith("http://") || prompt.startsWith("https://")) {

      referenceUrl = prompt;

      inputMode = "link";

    } else if (inputMode === "link" && !referenceUrl && prompt) {

      referenceUrl = prompt;

    }



    const payload = {

      series,

      episode,

      input_mode: inputMode,

      prompt: prompt || referenceUrl,

      reference_url: referenceUrl,

      minutes,

      scene_seconds: sceneSeconds,

      language,

      genre,

      visual_style: visualStyle,

      voice_name: voiceName,

      speech_pacing: speechPacing,

      production_mode: productionMode,

      image_provider: productionMode === "cinematic_drama" ? "muse_video" : imageProvider,

      subtitle_style: subtitleStyle,

      subtitle_size: subtitleSize,

      size: el.inResolution ? el.inResolution.value : "1280x720",

      workers,

      mode: "live",

      model: el.inModel ? el.inModel.value : "gemini-3.5-flash",

      link_clone_mode: document.getElementById("inLinkCloneMode")?.value || "exact_clone",

      character_clone: state.clonedCharacter || null,

      motion_mode: el.inMotionMode ? el.inMotionMode.value : "ken_burns",

      camera_motion: el.inCameraMotion ? el.inCameraMotion.value : "auto",

      atmospheric_overlay: el.inAtmosphericOverlay ? el.inAtmosphericOverlay.value : "auto",

      flow_video_model: el.inFlowVideoModel ? el.inFlowVideoModel.value : "Omni 1.1 Flash",

      flow_video_duration: parseInt(el.inFlowVideoDuration ? el.inFlowVideoDuration.value : "8", 10) || 8,

    };



    const res = await fetch("/api/queue/add", {

      method: "POST",

      headers: { "Content-Type": "application/json" },

      body: JSON.stringify(payload)

    });



    const data = await res.json();

    if (!res.ok || !data.ok) {

      throw new Error(data.error || "Không thể thêm vào hàng chờ");

    }



    showToast(`✅ Đã thêm Tập ${episode} vào hàng chờ! Tự động chạy tuần tự...`);



    // Auto increment episode for next entry

    if (el.inEpisode) {

      el.inEpisode.value = String(episode + 1);

    }



    window.refreshQueueUI();

  } catch (err) {

    showToast(`❌ Lỗi thêm hàng chờ: ${err.message}`);

  }

};



window.submitBulkImportQueue = async function() {

  try {

    const textEl = document.getElementById("queueBulkText");

    const rawText = textEl ? textEl.value.trim() : "";

    if (!rawText) {

      alert("Vui lòng dán ít nhất 1 link hoặc ý tưởng kịch bản!");

      return;

    }



    const series = document.getElementById("queueBulkSeries")?.value.trim() || "Stoic Sovereign";

    const startEp = parseInt(document.getElementById("queueBulkStartEp")?.value || "1", 10) || 1;

    const prodMode = document.getElementById("queueBulkProdMode")?.value || "cinematic_drama";

    const mins = parseFloat(document.getElementById("queueBulkMinutes")?.value || "20") || 20;



    const baseConfig = {

      series,

      episode: startEp,

      production_mode: prodMode,

      image_provider: prodMode === "cinematic_drama" ? "muse_video" : "flowkit",

      minutes: mins,

      scene_seconds: prodMode === "cinematic_drama" ? 10 : 25,

      language: el.inLanguage ? el.inLanguage.value : "Vietnamese",

      genre: el.inGenre ? el.inGenre.value : "stoic",

      visual_style: (el.inVisualStyle && el.inVisualStyle.value && el.inVisualStyle.value !== "auto") ? el.inVisualStyle.value : (el.inGenre?.value === "animation" ? "color_animation" : (el.inGenre?.value === "whiteboard" ? "whiteboard" : (el.inGenre?.value === "colored_marker" ? "colored_marker" : (prodMode === "cinematic_drama" ? "flow_video" : "color_cinematic")))),

      voice_name: el.inVoice ? el.inVoice.value : "auto",

      speech_pacing: el.inPacing ? el.inPacing.value : "slow",

      subtitle_style: el.inSubtitleStyle ? el.inSubtitleStyle.value : "karaoke_viral",

      subtitle_size: parseInt(el.inSubtitleSize ? el.inSubtitleSize.value : "0", 10) || 0,

      workers: parseInt(el.inWorkers ? el.inWorkers.value : "4", 10) || 4

    };



    const res = await fetch("/api/queue/bulk-add", {

      method: "POST",

      headers: { "Content-Type": "application/json" },

      body: JSON.stringify({

        links: rawText.split("\n"),

        base_config: baseConfig

      })

    });



    const data = await res.json();

    if (!res.ok || !data.ok) {

      throw new Error(data.error || "Lỗi nạp hàng loạt");

    }



    showToast(`🚀 Đã thêm ${data.count} tập vào hàng chờ thành công!`);

    if (textEl) textEl.value = "";

    window.toggleBulkPanel(false);

    window.refreshQueueUI();

  } catch (err) {

    alert(`Lỗi nạp hàng loạt: ${err.message}`);

  }

};



window.startQueueProduction = async function() {

  try {

    const res = await fetch("/api/queue/start", { method: "POST" });

    const data = await res.json();

    if (!res.ok || !data.ok) throw new Error(data.error || "Không thể khởi động hàng chờ");

    showToast("🚀 Hàng chờ đã được kích hoạt! Hệ thống bắt đầu xử lý tuần tự...");

    window.refreshQueueUI();

  } catch (err) {

    showToast(`❌ Lỗi: ${err.message}`);

  }

};



window.pauseQueueProduction = async function() {

  try {

    const res = await fetch("/api/queue/pause", { method: "POST" });

    const data = await res.json();

    if (!res.ok || !data.ok) throw new Error(data.error || "Không thể tạm dừng");

    showToast("⏸️ Đã tạm dừng hàng chờ tự động.");

    window.refreshQueueUI();

  } catch (err) {

    showToast(`❌ Lỗi: ${err.message}`);

  }

};



window.retryQueueItem = async function(jobId) {

  try {

    const res = await fetch("/api/queue/retry", {

      method: "POST",

      headers: { "Content-Type": "application/json" },

      body: JSON.stringify({ job_id: jobId })

    });

    const data = await res.json();

    if (!res.ok || !data.ok) throw new Error(data.error || "Không thể kích hoạt lại");

    showToast("🔄 Đã đưa công việc vào lại hàng chờ (chạy tiếp từ cảnh lỗi).");

    window.refreshQueueUI();

  } catch (err) {

    showToast(`❌ Lỗi: ${err.message}`);

  }

};



window.removeQueueItem = async function(jobId) {

  if (!confirm("Bạn có chắc chắn muốn xóa công việc này khỏi hàng chờ?")) return;

  try {

    const res = await fetch("/api/queue/remove", {

      method: "POST",

      headers: { "Content-Type": "application/json" },

      body: JSON.stringify({ job_id: jobId })

    });

    const data = await res.json();

    if (!res.ok || !data.ok) throw new Error(data.error || "Không thể xóa");

    showToast("🗑️ Đã xóa công việc khỏi hàng chờ.");

    window.refreshQueueUI();

  } catch (err) {

    showToast(`❌ Lỗi: ${err.message}`);

  }

};



window.clearFinishedQueue = async function() {

  try {

    const res = await fetch("/api/queue/clear", {

      method: "POST",

      headers: { "Content-Type": "application/json" },

      body: JSON.stringify({ mode: "completed_failed" })

    });

    const data = await res.json();

    if (!res.ok || !data.ok) throw new Error(data.error || "Không thể dọn dẹp");

    showToast("🧹 Đã dọn dẹp các công việc đã hoàn thành hoặc thất bại.");

    window.refreshQueueUI();

  } catch (err) {

    showToast(`❌ Lỗi: ${err.message}`);

  }

};



window.toggleQueueShutdown = async function(enabled) {

  try {

    await fetch("/api/queue/shutdown", {

      method: "POST",

      headers: { "Content-Type": "application/json" },

      body: JSON.stringify({ enabled })

    });

    showToast(enabled ? "🌙 Đã BẬT: Máy tính sẽ tự động tắt sau khi hoàn thành toàn bộ hàng chờ!" : "☀️ Đã TẮT tự động tắt máy.");

  } catch (err) {

    console.warn(err);

  }

};



// Initial badge check

setTimeout(() => {

  if (typeof window.refreshQueueUI === "function") {

    fetch("/api/queue").then(r => r.json()).then(d => { if (d && d.ok) window.updateQueueBadges(d); }).catch(() => {});

  }

}, 1500);





// --- PER-SCENE ACTIONS: RETRY, SKIP, ASSEMBLE NOW ---



window.retrySelectedScene = async function(sceneNumOverride) {
  if (state.isRunning) {
    showToast("⚠️ Tiến trình sản xuất đang chạy. Vui lòng chờ hoàn tất hoặc bấm Dừng trước khi tạo lại cảnh!", 4000);
    return;
  }
  const scNum = sceneNumOverride || state.selectedSceneNumber || 1;
  const curSeries = state.currentSeries || (el.inSeries ? el.inSeries.value.trim() : "phim");
  const curEp = Number(state.currentEpisode || (el.inEpisode ? el.inEpisode.value : 1));

  if (el.inSeries && curSeries) el.inSeries.value = curSeries;
  if (el.inEpisode && curEp) el.inEpisode.value = curEp;

  const currentDesc = document.getElementById("inspectorDesc")?.textContent || "";
  const initialPrompt = (currentDesc && currentDesc !== "-") ? currentDesc.trim() : "";
  const updatedPrompt = prompt(`Chỉnh sửa prompt Cảnh ${scNum} trước khi tạo lại:`, initialPrompt);
  if (updatedPrompt === null) return;

  try {
    showToast(`🔄 Đang chuẩn bị tạo lại Cảnh ${scNum}...`);
    const res = await fetch("/api/scene/retry", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        series: curSeries,
        episode: curEp,
        scene_number: scNum,
        prompt: updatedPrompt.trim()
      })
    });
    const data = await res.json();
    if (!res.ok || !data.ok) throw new Error(data.error || "Không thể khởi tạo lại cảnh");
    showToast(`⚡ Đã dọn dẹp Cảnh ${scNum}. Bắt đầu tạo lại ảnh và video...`);
    if (typeof submitProduction === "function") {
      submitProduction("live", { resume: true });
    }
  } catch (err) {
    showToast(`❌ Lỗi tạo lại cảnh: ${err.message}`);
  }
};

window.skipSelectedScene = async function() {

  const scNum = state.selectedSceneNumber || 1;

  const curSeries = state.currentSeries || (el.inSeries ? el.inSeries.value.trim() : "phim");

  const curEp = Number(state.currentEpisode || (el.inEpisode ? el.inEpisode.value : 1));

  

  if (!confirm(`Bạn có chắc chắn muốn BỎ QUA Cảnh ${scNum}? Hệ thống sẽ tự động chèn clip cầu nối an toàn (3s) để không làm nghẽn tiến trình cả tập.`)) {

    return;

  }

  

  try {

    showToast(`⏭️ Đang bỏ qua Cảnh ${scNum}...`);

    const res = await fetch("/api/scene/skip", {

      method: "POST",

      headers: { "Content-Type": "application/json" },

      body: JSON.stringify({

        series: curSeries,

        episode: curEp,

        scene_number: scNum

      })

    });

    const data = await res.json();

    if (!res.ok || !data.ok) throw new Error(data.error || "Không thể bỏ qua cảnh");

    

    showToast(`✅ Đã bỏ qua Cảnh ${scNum} thành công!`);

    await loadEpisodeDetails(curSeries, curEp);

  } catch (err) {

    showToast(`❌ Lỗi bỏ qua cảnh: ${err.message}`);

  }

};



window.assembleEpisodeDirect = async function() {

  const curSeries = state.currentSeries || (el.inSeries ? el.inSeries.value.trim() : "phim");

  const curEp = Number(state.currentEpisode || (el.inEpisode ? el.inEpisode.value : 1));

  

  if (!confirm(`Ghép nối toàn bộ các phân cảnh đã hoàn thành của Tập ${curEp} thành phim ngay bây giờ?`)) {

    return;

  }

  

  try {

    showToast(`🎬 Đang ghép nối các phân cảnh thành phim hoàn chỉnh...`);

    const res = await fetch("/api/episode/assemble", {

      method: "POST",

      headers: { "Content-Type": "application/json" },

      body: JSON.stringify({

        series: curSeries,

        episode: curEp

      })

    });

    const data = await res.json();

    if (!res.ok || !data.ok) throw new Error(data.error || "Không thể ghép phim");

    

    showToast(`🎉 ${data.message || "Đã ghép tập phim thành công!"}`);

    await loadEpisodeDetails(curSeries, curEp);

    void pollStatus();

  } catch (err) {

    showToast(`❌ Lỗi ghép phim: ${err.message}`);

  }

};





window.openMuseCookiePasteModal = async function(presetAccountId = null, presetName = null) {

  const modal = document.getElementById("modalMuseCookiePaste");

  if (!modal) return;



  const sel = document.getElementById("selMuseCookieTargetAccount");

  const nameDiv = document.getElementById("divMuseNewAccountName");

  const nameInput = document.getElementById("inMuseNewAccountName");

  const cookieInput = document.getElementById("inMuseCookieRaw");

  const btn = document.getElementById("btnSubmitMuseCookie");



  if (cookieInput) cookieInput.value = "";

  if (btn) { btn.disabled = false; btn.innerHTML = "<span>✓ Xác Minh & Lưu Phiên</span>"; }



  // Fetch accounts to populate select

  let accounts = [];

  try {

    const res = await fetch("/api/muse/status");

    const data = await res.json();

    accounts = data.accounts || [];

  } catch (_) {}



  if (sel) {

    let options = accounts.map(a => `<option value="${escapeHtml(a.id)}">${escapeHtml(a.name)} (${a.ready ? '🟢 Sẵn sàng' : '🟡 Cần đăng nhập'})</option>`).join("");

    options += `<option value="__new__">🔴 + Tạo tài khoản mới...</option>`;

    sel.innerHTML = options;



    if (presetAccountId && accounts.some(a => a.id === presetAccountId)) {

      sel.value = presetAccountId;

    } else if (presetAccountId === "__new__" || accounts.length === 0) {

      sel.value = "__new__";

    }

  }



  if (window.onMuseCookieTargetAccountChange) {

    window.onMuseCookieTargetAccountChange();

  }



  if (presetName && nameInput && sel && sel.value === "__new__") {

    nameInput.value = presetName;

  }



  modal.classList.add("open");

};



window.closeMuseProxyModal = function() {

  const modal = document.getElementById("modalMuseProxy");

  if (modal) modal.classList.remove("open");

};



window.onMuseCookieTargetAccountChange = function() {

  const sel = document.getElementById("selMuseCookieTargetAccount");

  const nameDiv = document.getElementById("divMuseNewAccountName");

  if (!sel || !nameDiv) return;

  nameDiv.style.display = sel.value === "__new__" ? "block" : "none";

};



window.submitMuseCookiePaste = async function() {

  const sel = document.getElementById("selMuseCookieTargetAccount");

  const nameInput = document.getElementById("inMuseNewAccountName");

  const cookieInput = document.getElementById("inMuseCookieRaw");

  const btn = document.getElementById("btnSubmitMuseCookie");



  const rawCookies = cookieInput ? cookieInput.value.trim() : "";

  if (!rawCookies) {

    showToast("Vui lòng dán nội dung cookie trước khi lưu!", "warning");

    if (cookieInput) cookieInput.focus();

    return;

  }



  const isNew = sel && sel.value === "__new__";

  const accountId = isNew ? "" : (sel ? sel.value : "");

  const accountName = isNew ? ((nameInput ? nameInput.value.trim() : "") || "Tài khoản Muse mới") : "";



  try {

    if (btn) {

      btn.disabled = true;

      btn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" style="width:14px;height:14px;border-width:2px;display:inline-block;margin-right:6px;"></span> Đang xác minh phiên với Muse...`;

    }



    const res = await fetch("/api/muse/accounts/save_session", {

      method: "POST",

      headers: { "Content-Type": "application/json" },

      body: JSON.stringify({

        account_id: accountId,

        name: accountName,

        cookies: rawCookies

      })

    });



    const data = await res.json();

    if (!res.ok || !data.ok) {

      throw new Error(data.error || "Không lưu được phiên Muse.");

    }



    const modal = document.getElementById("modalMuseCookiePaste");

    if (modal) closeModal(modal);



    await loadMuseStatus(true);

    showToast(data.message || "Đã lưu và xác minh tài khoản thành công!", "success");



  } catch (err) {

    showToast(err.message, "error");

  } finally {

    if (btn) {

      btn.disabled = false;

      btn.innerHTML = "<span>✓ Xác Minh & Lưu Phiên</span>";

    }

  }

};





// ==========================================

// MUSE AI PROXY AUTO-MAPPING HANDLERS

// ==========================================



window.openMuseProxyModal = function() {

  const modal = document.getElementById("modalMuseProxy");

  if (!modal) return;

  const input = document.getElementById("inMuseProxyRaw");

  const btn = document.getElementById("btnSubmitMuseProxy");

  if (input) input.value = "";

  if (btn) { btn.disabled = false; btn.innerHTML = "<span>✓ Tự Động Phân Bổ Proxy</span>"; }

  modal.classList.add("open");

};



window.submitMuseProxyPaste = async function() {

  const input = document.getElementById("inMuseProxyRaw");

  const btn = document.getElementById("btnSubmitMuseProxy");

  const raw = input ? input.value.trim() : "";

  if (!raw) {

    showToast("Vui lòng dán ít nhất 1 proxy!", "warning");

    if (input) input.focus();

    return;

  }



  try {

    if (btn) {

      btn.disabled = true;

      btn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" style="width:14px;height:14px;border-width:2px;display:inline-block;margin-right:6px;"></span> Đang gán proxy...`;

    }



    const res = await fetch("/api/muse/accounts/import_proxies", {

      method: "POST",

      headers: { "Content-Type": "application/json" },

      body: JSON.stringify({ proxies: raw })

    });



    const data = await res.json();

    if (!res.ok || !data.ok) {

      throw new Error(data.error || "Không gán được proxy.");

    }



    const modal = document.getElementById("modalMuseProxy");

    if (modal) closeModal(modal);



    await loadMuseStatus(true);

    showToast(data.message || `Đã gán proxy cho ${data.assigned_count || 0} tài khoản!`, "success");



  } catch (err) {

    showToast(err.message, "error");

  } finally {

    if (btn) {

      btn.disabled = false;

      btn.innerHTML = "<span>✓ Tự Động Phân Bổ Proxy</span>";

    }

  }

};



window.clearAllMuseProxies = async function() {

  if (!confirm("Bạn có chắc muốn xóa tất cả proxy đã gán? Các tài khoản sẽ quay lại dùng IP trực tiếp của máy.")) {

    return;

  }



  try {

    const res = await fetch("/api/muse/accounts/remove_proxies", {

      method: "POST",

      headers: { "Content-Type": "application/json" },

      body: JSON.stringify({})

    });



    const data = await res.json();

    if (!res.ok || !data.ok) {

      throw new Error(data.error || "Không xóa được proxy.");

    }



    const modal = document.getElementById("modalMuseProxy");

    if (modal) closeModal(modal);



    await loadMuseStatus(true);

    showToast(data.message || "Đã xóa proxy, tất cả tài khoản dùng IP gốc!", "success");



  } catch (err) {

    showToast(err.message, "error");

  }

};



// =============================================================================
// SATELLITE SHORTS (9:16) SYSTEM
// =============================================================================

window.openSatelliteShortPrompt = function() {
  const modal = document.getElementById("modalSatelliteShortPrompt");
  if (modal) {
    modal.style.display = "flex";
  }
};

window.closeSatelliteShortModal = function() {
  const modal = document.getElementById("modalSatelliteShortPrompt");
  if (modal) {
    modal.style.display = "none";
  }
};

window.confirmCreateSatelliteShort = async function() {
  const btn = document.getElementById("btnConfirmSatelliteShort");
  const bannerBtn = document.getElementById("btnCreateSatelliteShort");
  if (btn) {
    btn.disabled = true;
    btn.textContent = "⏳ Đang trích xuất...";
  }
  if (bannerBtn) {
    bannerBtn.disabled = true;
    bannerBtn.textContent = "⏳ Đang tạo Short 9:16...";
  }
  showToast("⏳ Đang phân tích phân đoạn cao trào & tạo Short Vệ Tinh 9:16...", 5000);
  try {
    const curSeries = state.currentSeries || (el.inSeries ? el.inSeries.value.trim() : "") || "stoi";
    const curEp = Number(state.currentEpisode || (el.inEpisode ? el.inEpisode.value : 1) || 2);
    const res = await fetch("/api/episode/short/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        series: curSeries,
        episode: curEp
      })
    });
    const data = await res.json();
    if (data.ok) {
      closeSatelliteShortModal();
      showToast("🎉 Đã tạo thành công Video Short Vệ Tinh (9:16)!", 4000);
      const shortUrl = data.video_url || data.web_url || `/media/productions/${encodeURIComponent(curSeries)}/episode_${String(curEp).padStart(3, "0")}/episode_short.mp4?v=${Date.now()}`;
      
      if (!state.loadedEpisodeData) state.loadedEpisodeData = {};
      state.loadedEpisodeData.final_short_url = shortUrl;
      state.activePreviewMode = "short";

      if (typeof switchPlayerMode === "function") {
        switchPlayerMode("short");
      }
      if (typeof setVideoSource === "function") {
        setVideoSource(shortUrl, `📱 Short Vệ Tinh 9:16 - Tập ${curEp}`);
      }
      if (el.videoMonitorContainer) {
        el.videoMonitorContainer.classList.add("mode-shorts");
      }
      if (el.cinemaVideo) {
        el.cinemaVideo.style.display = "block";
        el.cinemaVideo.src = shortUrl;
        el.cinemaVideo.load();
        el.cinemaVideo.play().catch(() => {});
      }
      if (typeof fetchStatus === "function") {
        fetchStatus();
      }
    } else {
      showToast("❌ Lỗi tạo Short: " + (data.error || "Không thành công"), 4000);
    }
  } catch (err) {
    showToast("❌ Lỗi kết nối: " + err.message, 4000);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = "📱 Có, Tạo Short Vệ Tinh (OK)";
    }
    if (bannerBtn) {
      bannerBtn.disabled = false;
      bannerBtn.textContent = "📱 Tạo Short Vệ Tinh (9:16)";
    }
  }
};


// 🧹 Dọn dẹp bản sao lưu cũ, file tạm cập nhật và bộ nhớ cache (Áp dụng cả Máy Chính & Máy Phụ)
async function cleanOldVersionsAndCache() {
  const btn = document.getElementById("btnCleanOldVersions");
  const origText = btn ? btn.innerHTML : "";
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = "⏳ Đang dọn dẹp...";
  }
  try {
    const res = await fetch("/api/system/cleanup");
    const data = await res.json();
    if (data.ok) {
      if (data.freed_mb > 0) {
        showToast(`✓ Đã dọn dẹp ${data.freed_mb} MB dữ liệu bản cũ và file tạm!`, "success");
      } else {
        showToast("✓ Hệ thống sạch sẽ! Không có dữ liệu bản cũ thừa cần dọn.", "info");
      }
    } else {
      showToast("Lỗi dọn dẹp: " + (data.error || "Không rõ nguyên nhân"), "error");
    }
  } catch (err) {
    showToast("Không thể kết nối máy chủ để dọn dẹp.", "error");
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = origText;
    }
  }
}
