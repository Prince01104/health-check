/* Health Check: single-page app (no build step). Talks to the FastAPI backend in /api. */
(() => {
"use strict";

// ------------------------------------------------------------------ helpers
const store = {
  get(k) { try { return localStorage.getItem(k); } catch { return null; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch { /* private mode */ } },
  del(k) { try { localStorage.removeItem(k); } catch { /* ignore */ } },
};
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const $ = (sel, el = document) => el.querySelector(sel);
const $$ = (sel, el = document) => [...el.querySelectorAll(sel)];

const state = {
  lang: store.get("hc_lang") === "hi" ? "hi" : "en",
  checks: [], me: null, current: null, picked: null, pickedUrl: null, histFilter: "all", resultView: "photo", busy: false,
};

// -------------------------------------------------------------------- icons
const ICONS = {
  logo: '<path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/><path d="M3.22 12H9.5l.5-1 2 4.5 2-7 1.5 3.5h5.27"/>',
  oral: '<path d="M7.5 3.5C5 3.5 3.200 5.400 3.200 8c0 2.400 1.200 3.700 1.800 6 .6 2.300.6 5.200 1.600 7 .4.800 1.400.9 1.900 0 .9-1.700 1-3.900 1.700-4.700.3-.4 1-.4 1.300 0 .7.800.8 3 1.700 4.700.5.900 1.500.8 1.900 0 1-1.800 1-4.700 1.600-7 .6-2.300 1.800-3.600 1.800-6 0-2.600-1.800-4.500-4.300-4.500-1.900 0-2.700.9-4.500.9S9.400 3.500 7.500 3.500Z"/>',
  skin: '<circle cx="12" cy="12" r="9"/><path d="M8 14.500c.9 1.300 2.300 2 4 2s3.100-.7 4-2"/><path d="M9 9.500h.01M15 9.500h.01" stroke-width="2.600"/>',
  infection: '<circle cx="12" cy="12" r="4"/><path d="M12 2.500v2.500M12 19v2.500M4.500 4.500l1.800 1.800M17.700 17.700l1.800 1.800M2.500 12H5M19 12h2.500M4.500 19.500l1.800-1.800M17.700 6.300l1.800-1.800"/>',
  nail: '<path d="M6.500 21V10.500a5.500 5.500 0 0 1 11 0V21"/><path d="M10 21v-9.500a2 2 0 0 1 4 0V21"/>',
  home: '<path d="M3 11l9-8 9 8"/><path d="M5 9.500V20h5v-6h4v6h5V9.500"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  user: '<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 3.500-6 8-6s8 2 8 6"/>',
  logout: '<path d="M9 4H5.500A1.500 1.500 0 0 0 4 5.500v13A1.500 1.500 0 0 0 5.500 20H9"/><path d="M15.500 7.500 20 12l-4.500 4.500M20 12H9"/>',
  camera: '<path d="M4 8h3l2-3h6l2 3h3a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1z"/><circle cx="12" cy="13" r="3.500"/>',
  image: '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="1.500"/><path d="m21 16-5-5-8 8"/>',
  back: '<path d="M15 5 8 12l7 7"/>',
  download: '<path d="M12 4v11M7 11l5 5 5-5M5 20h14"/>',
  map: '<path d="M12 21s7-6.500 7-12a7 7 0 0 0-14 0c0 5.500 7 12 7 12z"/><circle cx="12" cy="9" r="2.500"/>',
  alert: '<path d="M12 3 22 20H2L12 3z"/><path d="M12 10v4.500M12 17.500h.01"/>',
  flame: '<path d="M12 3c1 3.500 5.500 5.500 5.500 10.500a5.500 5.500 0 0 1-11 0c0-2.200 1-3.500 2.200-4.500.1 2 1 3 2.200 3-.2-3.200-1.200-6.200 1.100-9z"/>',
  bulb: '<path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-3.500 10.900c.7.600 1 1.300 1 2.100h5c0-.8.300-1.500 1-2.100A6 6 0 0 0 12 3z"/>',
  trash: '<path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3"/>',
  bell: '<path d="M6 16V11a6 6 0 0 1 12 0v5l2 2H4l2-2zM10 21h4"/>',
};
const icon = (n) => `<svg class="i" viewBox="0 0 24 24" aria-hidden="true">${ICONS[n] || ""}</svg>`;

// --------------------------------------------------------------------- text
const T = {
  en: {
    tagline: "Oral, skin, infection and nail screening in one app",
    email: "Email", emailPh: "you@example.com", password: "Password", passwordPh: "Enter your password",
    forgot: "Forgot password?", forgotMsg: "Password reset is not available in this demo. Please create a new account.",
    login: "Login", newHere: "New here?", createAccount: "Create account", haveAcc: "Already have an account?",
    name: "Your name", namePh: "Full name", confirm: "Confirm password", pwMismatch: "Passwords do not match.", pwHint: "At least 6 characters",
    disc: "AI screening only. It does not replace a doctor's diagnosis.",
    disc2: "AI screening only. See a doctor for a real diagnosis.",
    welcome: "Welcome back", quickTitle: "Start a quick check", quickText: "Pick a check below, add a clear photo and get an instant AI result.",
    choose: "Choose a check", soon: "Coming soon", demo: "Demo model", tipDay: "Tip of the day",
    dayStreak: (n) => `${n} day streak`, reminderDue: "You have not done a check today.",
    home: "Home", history: "History", profile: "Profile", logout: "Logout",
    photoTips: "How to take a good photo", takePhoto: "Take photo", choosePhoto: "Choose from gallery", noPhoto: "Your photo will appear here",
    analyse: "Analyse photo", analysing: "Analysing...", demoWarn: "Demo model: the results are random and not meaningful. Copy your real model into the models folder.",
    soonText: "This check is coming soon. Its model has not been installed yet.",
    photo: "Photo", heat: "Heatmap", heatNote: "Warm colours show where the AI looked. It is only a hint, not proof.",
    possible: "Possible", confidence: "confidence", notSure: "Not sure", bestGuess: "Best guess",
    notSureText: "The model is not confident about this photo. Retake it in good light, closer to the problem area, and try again.",
    invalidTitle: "This photo does not look right", invalidText: "Please take a clear photo of the correct area. See the tips below.",
    q_low_res: "The photo is small. Move closer or use a higher quality photo.", q_blurry: "The photo looks blurry. Hold the phone steady.",
    q_dark: "The photo is too dark. Use more light.", q_bright: "The photo is too bright. Avoid flash and glare.",
    about: "About this result", doThis: "What you can do", others: "Other possibilities",
    d_soon: (d) => `Please book a visit with a ${d} soon.`, d_if_persists: "If it does not settle in 1 to 2 weeks or gets worse, please see a doctor.",
    d_no: "Nothing worrying was seen, but regular check-ups are still a good idea.", d_unsure: "If you are worried, please see a doctor.",
    findDoc: (d) => `Find a ${d} near me`, report: "Download PDF report", again: "Check again",
    historyEmpty: "No checks yet. Do your first check from Home.", all: "All", clearAll: "Clear all history",
    confirmClear: "Delete all your saved results and photos?", deleteOne: "Delete this result", confirmDelOne: "Delete this result and its photos?",
    checksDone: "Checks done", streak: "Day streak", language: "Language", reminder: "Daily reminder", reminderTime: "Reminder time",
    reminderHelp: "Shown on Home while the app is open.",
    privacy: "Your photos are saved only in this app's own storage on this computer. You can delete everything at any time.",
    deleteAcc: "Delete my account and data", confirmDelAcc: "This permanently deletes your account, results and photos. Continue?",
    logoutTitle: "Log out?", logoutText: "You will need to log in again to run a new check or see your history.",
    yesLogout: "Yes, log out", cancel: "Cancel", loading: "Loading...",
    errGeneric: "Something went wrong. Please try again.", errNetwork: "Cannot reach the server. Is it running?",
    doctor: { dentist: "dentist", dermatologist: "skin doctor", doctor: "doctor" },
    photoTipsBy: {
      oral: ["Open your mouth wide and face the camera straight.", "Use bright light. Avoid flash glare.", "Show the teeth, gums or sore area up close.", "Keep the phone steady."],
      skin: ["Use daylight, with no filter or beauty mode.", "Hold the phone 15 to 30 cm away.", "Keep the problem area in the centre.", "Move hair or glasses away from the area."],
      infection: ["Show the wound or spot clearly in bright light.", "Include a little normal skin around it.", "Do not use a filter.", "Keep the phone steady."],
      nail: ["Place your hand flat in good light.", "Remove nail polish if you can.", "Take a close-up of one or two nails.", "Keep the nail in the centre."],
    },
    checkTitle: { oral: "Oral Check", skin: "Skin Check", infection: "Infection Check", nail: "Nail Check" },
    checkSub: { oral: "Teeth and gums", skin: "Face, acne and rashes", infection: "Wounds and spots", nail: "Colour and shape" },
    statusOk: "Result", noProblem: "No clear problem",
  },
  hi: {
    tagline: "मुंह, त्वचा, संक्रमण और नाखून की जांच, एक ही ऐप में",
    email: "ईमेल", emailPh: "you@example.com", password: "पासवर्ड", passwordPh: "अपना पासवर्ड लिखें",
    forgot: "पासवर्ड भूल गए?", forgotMsg: "इस डेमो में पासवर्ड रीसेट उपलब्ध नहीं है। कृपया नया खाता बनाएं।",
    login: "लॉगिन", newHere: "नए हैं?", createAccount: "खाता बनाएं", haveAcc: "पहले से खाता है?",
    name: "आपका नाम", namePh: "पूरा नाम", confirm: "पासवर्ड दोबारा लिखें", pwMismatch: "पासवर्ड मेल नहीं खाते।", pwHint: "कम से कम 6 अक्षर",
    disc: "यह सिर्फ AI स्क्रीनिंग है। यह डॉक्टर की जांच का विकल्प नहीं है।",
    disc2: "यह सिर्फ AI स्क्रीनिंग है। असली जांच के लिए डॉक्टर को दिखाएं।",
    welcome: "वापसी पर स्वागत है", quickTitle: "जल्दी जांच शुरू करें", quickText: "नीचे से जांच चुनें, साफ फोटो डालें और तुरंत AI नतीजा पाएं।",
    choose: "जांच चुनें", soon: "जल्द आ रहा है", demo: "डेमो मॉडल", tipDay: "आज की सलाह",
    dayStreak: (n) => `${n} दिन लगातार`, reminderDue: "आज आपने कोई जांच नहीं की है।",
    home: "होम", history: "इतिहास", profile: "प्रोफ़ाइल", logout: "लॉगआउट",
    photoTips: "अच्छी फोटो कैसे लें", takePhoto: "फोटो लें", choosePhoto: "गैलरी से चुनें", noPhoto: "आपकी फोटो यहां दिखेगी",
    analyse: "फोटो जांचें", analysing: "जांच हो रही है...", demoWarn: "डेमो मॉडल: नतीजे बेतरतीब हैं और किसी काम के नहीं। अपना असली मॉडल models फ़ोल्डर में रखें।",
    soonText: "यह जांच जल्द आएगी। इसका मॉडल अभी नहीं लगा है।",
    photo: "फोटो", heat: "हीटमैप", heatNote: "गर्म रंग दिखाते हैं कि AI ने कहां देखा। यह सिर्फ एक संकेत है, सबूत नहीं।",
    possible: "संभावित", confidence: "भरोसा", notSure: "पक्का नहीं", bestGuess: "सबसे संभावित",
    notSureText: "मॉडल को इस फोटो पर भरोसा नहीं है। अच्छी रोशनी में, समस्या वाली जगह के पास से दोबारा फोटो लें।",
    invalidTitle: "यह फोटो सही नहीं लग रही", invalidText: "कृपया सही जगह की साफ फोटो लें। नीचे दी गई सलाह देखें।",
    q_low_res: "फोटो छोटी है। पास जाएं या बेहतर क्वालिटी की फोटो लें।", q_blurry: "फोटो धुंधली लग रही है। फोन को स्थिर पकड़ें।",
    q_dark: "फोटो बहुत अंधेरी है। ज़्यादा रोशनी में लें।", q_bright: "फोटो बहुत तेज़ रोशनी वाली है। फ्लैश और चमक से बचें।",
    about: "इस नतीजे के बारे में", doThis: "आप क्या कर सकते हैं", others: "दूसरी संभावनाएं",
    d_soon: (d) => `कृपया जल्द ${d} से मिलें।`, d_if_persists: "अगर 1-2 हफ्ते में ठीक न हो या बढ़े, तो डॉक्टर को दिखाएं।",
    d_no: "कुछ चिंताजनक नहीं दिखा, फिर भी नियमित जांच अच्छी रहती है।", d_unsure: "अगर चिंता हो तो डॉक्टर को दिखाएं।",
    findDoc: (d) => `पास के ${d} खोजें`, report: "PDF रिपोर्ट डाउनलोड करें", again: "दोबारा जांचें",
    historyEmpty: "अभी कोई जांच नहीं हुई। होम से पहली जांच करें।", all: "सभी", clearAll: "पूरा इतिहास मिटाएं",
    confirmClear: "आपके सभी सेव नतीजे और फोटो मिटा दें?", deleteOne: "यह नतीजा मिटाएं", confirmDelOne: "यह नतीजा और इसकी फोटो मिटा दें?",
    checksDone: "जांचें", streak: "लगातार दिन", language: "भाषा", reminder: "रोज़ का रिमाइंडर", reminderTime: "रिमाइंडर का समय",
    reminderHelp: "ऐप खुला होने पर होम पर दिखेगा।",
    privacy: "आपकी फोटो सिर्फ इस कंप्यूटर पर इस ऐप के अपने स्टोरेज में रहती हैं। आप कभी भी सब कुछ मिटा सकते हैं।",
    deleteAcc: "मेरा खाता और डेटा मिटाएं", confirmDelAcc: "इससे आपका खाता, नतीजे और फोटो हमेशा के लिए मिट जाएंगे। आगे बढ़ें?",
    logoutTitle: "लॉगआउट करें?", logoutText: "नई जांच करने या इतिहास देखने के लिए आपको दोबारा लॉगिन करना होगा।",
    yesLogout: "हां, लॉगआउट करें", cancel: "रद्द करें", loading: "लोड हो रहा है...",
    errGeneric: "कुछ गड़बड़ हो गई। कृपया दोबारा कोशिश करें।", errNetwork: "सर्वर से जुड़ नहीं पा रहे। क्या वह चालू है?",
    doctor: { dentist: "डेंटिस्ट", dermatologist: "त्वचा रोग विशेषज्ञ", doctor: "डॉक्टर" },
    photoTipsBy: {
      oral: ["मुंह पूरा खोलें और कैमरे की तरफ सीधे देखें।", "तेज़ रोशनी लें। फ्लैश की चमक से बचें।", "दांत, मसूड़े या घाव की पास से फोटो लें।", "फोन को स्थिर रखें।"],
      skin: ["दिन की रोशनी में लें, फिल्टर या ब्यूटी मोड न लगाएं।", "फोन को 15 से 30 सेमी दूर रखें।", "समस्या वाली जगह को बीच में रखें।", "बाल या चश्मा उस जगह से हटा लें।"],
      infection: ["घाव या दाग को तेज़ रोशनी में साफ दिखाएं।", "आसपास की थोड़ी सामान्य त्वचा भी लें।", "फिल्टर का उपयोग न करें।", "फोन को स्थिर रखें।"],
      nail: ["हाथ को अच्छी रोशनी में सीधा रखें।", "हो सके तो नेल पॉलिश हटा लें।", "एक या दो नाखूनों की पास से फोटो लें।", "नाखून को बीच में रखें।"],
    },
    checkTitle: { oral: "मुंह की जांच", skin: "त्वचा की जांच", infection: "संक्रमण जांच", nail: "नाखून की जांच" },
    checkSub: { oral: "दांत और मसूड़े", skin: "चेहरा, मुंहासे और चकत्ते", infection: "घाव और दाग", nail: "रंग और आकार" },
    statusOk: "नतीजा", noProblem: "कोई साफ समस्या नहीं",
  },
};
const LABEL_HI = {
  calculus: "टार्टर (कैलकुलस)", gingivitis: "मसूड़ों की सूजन", hypodontia: "दांतों की कमी", mouth_ulcer: "मुंह का छाला",
  caries: "कैविटी (दांत की सड़न)", discoloration: "दांतों का रंग बदलना", acne: "मुंहासे", rosacea: "रोज़ेसिया",
  eczema: "एक्ज़ीमा", tinea: "दाद (टिनिया)", psoriasis: "सोरायसिस", vitiligo: "सफेद दाग (विटिलिगो)",
};
const t = (k, ...a) => { const v = T[state.lang][k] ?? T.en[k] ?? k; return typeof v === "function" ? v(...a) : v; };
const labelName = (label, display) => {
  const low = String(label).toLowerCase();
  if (low.startsWith("not_")) return state.lang === "hi" ? "फोटो सही नहीं" : "Photo not suitable";
  if (low.includes("normal")) return t("noProblem");
  return state.lang === "hi" && LABEL_HI[low] ? LABEL_HI[low] : display;
};
const fmtDate = (ts) => new Date(ts * 1000).toLocaleString(state.lang === "hi" ? "hi-IN" : "en-IN",
  { day: "numeric", month: "short", year: "numeric", hour: "numeric", minute: "2-digit" });
const checkTitle = (id) => t("checkTitle")[id] || id;

// ---------------------------------------------------------------------- api
async function api(path, opts = {}) {
  const headers = { ...(opts.headers || {}) };
  const tok = store.get("hc_token");
  if (tok) headers.Authorization = "Bearer " + tok;
  let body = opts.body;
  if (body && !(body instanceof FormData)) { headers["Content-Type"] = "application/json"; body = JSON.stringify(body); }
  let res;
  try { res = await fetch(path, { method: opts.method || "GET", headers, body }); }
  catch { throw new Error(t("errNetwork")); }
  if (res.status === 401 && !opts.noRedirect) { clearSession(); location.hash = "#/login"; throw new Error("auth"); }
  if (!res.ok) {
    let msg = t("errGeneric");
    try { const j = await res.json(); if (typeof j.detail === "string") msg = j.detail; } catch { /* ignore */ }
    throw new Error(msg);
  }
  return opts.raw ? res : res.json();
}
function clearSession() {
  store.del("hc_token"); state.me = null; state.current = null;
  for (const u of imgCache.values()) URL.revokeObjectURL(u);
  imgCache.clear();
}
const imgCache = new Map();
async function imgUrl(id, kind) {
  const key = id + ":" + kind;
  if (!imgCache.has(key)) {
    const res = await api(`/api/history/${id}/image?kind=${kind}`, { raw: true });
    imgCache.set(key, URL.createObjectURL(await res.blob()));
  }
  return imgCache.get(key);
}
function hydrateImages() {
  $$("img[data-img]").forEach(async (el) => {
    const [id, kind] = el.dataset.img.split(":");
    try { el.src = await imgUrl(id, kind); } catch { el.alt = ""; }
  });
}
async function shrink(file, max = 1280) {
  try {
    const bmp = await createImageBitmap(file, { imageOrientation: "from-image" });
    const s = Math.min(1, max / Math.max(bmp.width, bmp.height));
    const c = document.createElement("canvas");
    c.width = Math.round(bmp.width * s); c.height = Math.round(bmp.height * s);
    c.getContext("2d").drawImage(bmp, 0, 0, c.width, c.height);
    const blob = await new Promise((r) => c.toBlob(r, "image/jpeg", 0.9));
    return blob || file;
  } catch { return file; }
}
let toastTimer;
function toast(msg) {
  const el = $("#toast"); el.textContent = msg; el.classList.add("show");
  clearTimeout(toastTimer); toastTimer = setTimeout(() => el.classList.remove("show"), 3200);
}

// --------------------------------------------------------------------- views
const view = $("#view"), nav = $("#nav");
const disclaimer = (k = "disc2") => `<p class="disc">${esc(t(k))}</p>`;

function setNav(active) {
  if (!active) { nav.hidden = true; return; }
  nav.hidden = false;
  const items = [["home", "home", t("home")], ["history", "clock", t("history")], ["profile", "user", t("profile")], ["logout", "logout", t("logout")]];
  nav.innerHTML = items.map(([id, ic, label]) =>
    `<button data-go="${id}" ${id === active ? 'aria-current="page"' : ""}>${icon(ic)}<span>${esc(label)}</span></button>`).join("");
}
function render(html, navActive) {
  view.innerHTML = html; setNav(navActive); hydrateImages(); window.scrollTo(0, 0);
}
const loading = () => render(`<p class="center muted" style="padding:60px 0">${esc(t("loading"))}</p>`, null);

function authScreen(mode) {
  const signup = mode === "signup";
  render(`
  <section class="auth">
    <div class="logo">${icon("logo")}</div>
    <h1>Health Check</h1>
    <p class="tag">${esc(t("tagline"))}</p>
    <form id="authForm" class="stack" novalidate>
      ${signup ? `<div><label class="f" for="name">${esc(t("name"))}</label><input id="name" type="text" autocomplete="name" placeholder="${esc(t("namePh"))}" required></div>` : ""}
      <div><label class="f" for="email">${esc(t("email"))}</label><input id="email" type="email" autocomplete="email" inputmode="email" placeholder="${esc(t("emailPh"))}" required></div>
      <div><label class="f" for="pw">${esc(t("password"))}</label><input id="pw" type="password" autocomplete="${signup ? "new-password" : "current-password"}" placeholder="${esc(signup ? t("pwHint") : t("passwordPh"))}" required></div>
      ${signup ? `<div><label class="f" for="pw2">${esc(t("confirm"))}</label><input id="pw2" type="password" autocomplete="new-password" required></div>` : ""}
      <div id="authErr" class="err" role="alert" hidden></div>
      ${signup ? "" : `<div style="text-align:right"><button type="button" class="link" data-action="forgot">${esc(t("forgot"))}</button></div>`}
      <button class="btn" type="submit">${esc(signup ? t("createAccount") : t("login"))}</button>
    </form>
    <p class="center" style="margin-top:18px"><span class="muted">${esc(signup ? t("haveAcc") : t("newHere"))}</span>
      <a class="link" href="#/${signup ? "login" : "signup"}">${esc(signup ? t("login") : t("createAccount"))}</a></p>
    <p class="foot-note">${esc(t("disc"))}</p>
    <p class="center" style="margin-top:14px">${langSwitch()}</p>
  </section>`, null);
}
const langSwitch = () => `<span class="seg" role="group" aria-label="Language">
  <button data-lang="en" aria-pressed="${state.lang === "en"}">English</button>
  <button data-lang="hi" aria-pressed="${state.lang === "hi"}">हिन्दी</button></span>`;

function reminderDue() {
  let r; try { r = JSON.parse(store.get("hc_rem") || "null"); } catch { r = null; }
  if (!r || !r.on || !state.me || state.me.stats.today_done) return false;
  const [h, m] = (r.time || "20:00").split(":").map(Number);
  const now = new Date();
  return now.getHours() * 60 + now.getMinutes() >= h * 60 + m;
}

async function homeScreen() {
  loading();
  const [checks, me, tip] = await Promise.all([api("/api/checks"), api("/api/me?tz=" + -new Date().getTimezoneOffset()), api("/api/tip")]);
  state.checks = checks; state.me = me;
  const cards = checks.map((c) => `
    <button class="card check" data-check="${c.id}" ${c.ready ? "" : 'aria-disabled="true"'} aria-label="${esc(checkTitle(c.id))}">
      <span class="tile ${c.id}">${icon(c.id)}</span>
      ${!c.ready ? `<span class="pill warn badge">${esc(t("soon"))}</span>` : c.demo ? `<span class="pill warn badge">${esc(t("demo"))}</span>` : ""}
      <h3>${esc(checkTitle(c.id))}</h3><span class="muted small">${esc(t("checkSub")[c.id] || c.subtitle)}</span>
    </button>`).join("");
  const streak = me.stats.streak > 0 ? `<span class="pill on-dark">${icon("flame")} ${esc(t("dayStreak", me.stats.streak))}</span>` : "";
  render(`
  <div class="top">
    <div><p class="muted">${esc(t("welcome"))}, ${esc(me.name.split(" ")[0])}</p><h1>Health Check</h1></div>
    <button class="avatar" data-go="profile" aria-label="${esc(t("profile"))}">${icon("user")}</button>
  </div>
  ${reminderDue() ? `<div class="reminder">${icon("bell")} ${esc(t("reminderDue"))}</div>` : ""}
  <section class="banner"><h3>${esc(t("quickTitle"))}</h3><p>${esc(t("quickText"))}</p>${streak ? `<div class="chip-row">${streak}</div>` : ""}</section>
  <h2 class="sec">${esc(t("choose"))}</h2>
  <div class="grid2">${cards}</div>
  <div class="card tip" style="margin-top:14px"><span class="tile">${icon("bulb")}</span>
    <div><b class="small">${esc(t("tipDay"))}</b><p class="small" style="margin-top:2px">${esc(tip[state.lang] || tip.en)}</p></div></div>
  ${disclaimer()}`, "home");
}

function checkScreen(id) {
  const c = state.checks.find((x) => x.id === id);
  if (!c) { location.hash = "#/home"; return; }
  if (state.pickedFor !== id) { state.picked = null; if (state.pickedUrl) URL.revokeObjectURL(state.pickedUrl); state.pickedUrl = null; state.pickedFor = id; }
  const tips = (t("photoTipsBy")[id] || []).map((x) => `<li>${esc(x)}</li>`).join("");
  render(`
  <div class="head"><button class="back" data-go="home" aria-label="${esc(t("home"))}">${icon("back")}</button><h2>${esc(checkTitle(id))}</h2></div>
  <div class="stack">
    ${!c.ready ? `<div class="note">${esc(t("soonText"))}</div>` : c.demo ? `<div class="note">${esc(t("demoWarn"))}</div>` : ""}
    <div class="card"><h3>${esc(t("photoTips"))}</h3><ul class="tips small">${tips}</ul></div>
    <div class="drop" id="drop">${state.pickedUrl ? `<img src="${state.pickedUrl}" alt="">` : `<span>${icon("image")}<br>${esc(t("noPhoto"))}</span>`}</div>
    <input type="file" id="cam" accept="image/*" capture="environment" hidden>
    <input type="file" id="gal" accept="image/*" hidden>
    <div class="btns2">
      <button class="btn outline" data-action="cam" ${c.ready ? "" : "disabled"}>${icon("camera")} ${esc(t("takePhoto"))}</button>
      <button class="btn outline" data-action="gal" ${c.ready ? "" : "disabled"}>${icon("image")} ${esc(t("choosePhoto"))}</button>
    </div>
    <div id="chkErr" class="err" role="alert" hidden></div>
    <button class="btn" id="go" data-action="analyse" data-check="${id}" ${state.picked && c.ready ? "" : "disabled"}>${esc(t("analyse"))}</button>
  </div>
  ${disclaimer()}`, "home");
  const onPick = async (ev) => {
    const f = ev.target.files && ev.target.files[0];
    if (!f) return;
    if (state.pickedUrl) URL.revokeObjectURL(state.pickedUrl);
    state.picked = f; state.pickedUrl = URL.createObjectURL(f);
    $("#drop").innerHTML = `<img src="${state.pickedUrl}" alt="">`;
    $("#go").disabled = false;
  };
  $("#cam").addEventListener("change", onPick); $("#gal").addEventListener("change", onPick);
}

async function analyse(id) {
  if (state.busy || !state.picked) return;
  state.busy = true;
  const btn = $("#go"), err = $("#chkErr");
  err.hidden = true; btn.disabled = true; btn.innerHTML = `<span class="spin"></span> ${esc(t("analysing"))}`;
  try {
    const blob = await shrink(state.picked);
    const fd = new FormData(); fd.append("file", blob, "photo.jpg");
    state.current = await api("/api/predict/" + id, { method: "POST", body: fd });
    state.resultView = "photo"; state.me = null;
    location.hash = "#/result";
  } catch (e) {
    if (e.message !== "auth") { err.textContent = e.message; err.hidden = false; }
    btn.disabled = false; btn.textContent = t("analyse");
  } finally { state.busy = false; }
}

function resultScreen(r, fromHistory) {
  const info = r.content[state.lang] || r.content.en;
  const doc = t("doctor")[r.doctor] || r.doctor;
  const pct = Math.round(r.confidence * 100);
  const name = labelName(r.label, r.display);
  let head, body = "";
  if (r.status === "ok") {
    head = `<div class="res ok"><span class="muted small">${esc(t("possible"))}</span><h2>${esc(name)}</h2>
      <div class="bar" role="img" aria-label="${pct}%"><i style="width:${pct}%"></i></div><p class="small muted" style="margin-top:6px">${pct}% ${esc(t("confidence"))}</p></div>`;
    const dd = r.see_doctor === "soon" ? t("d_soon", doc) : r.see_doctor === "no" ? t("d_no") : t("d_if_persists");
    body = `<div class="card"><h3>${esc(t("about"))}</h3><p style="margin-top:6px">${esc(info.about)}</p></div>
      <div class="card"><h3>${esc(t("doThis"))}</h3><ul class="tips">${info.tips.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>
        <p style="margin-top:10px"><b>${esc(dd)}</b></p></div>`;
  } else if (r.status === "uncertain") {
    head = `<div class="res warn"><h2>${esc(t("notSure"))}</h2><p>${esc(t("notSureText"))}</p>
      <p class="small" style="margin-top:8px">${esc(t("bestGuess"))}: <b>${esc(name)}</b> (${pct}%)</p></div>`;
    body = `<div class="card"><h3>${esc(t("photoTips"))}</h3><ul class="tips small">${(t("photoTipsBy")[r.check] || []).map((x) => `<li>${esc(x)}</li>`).join("")}</ul>
      <p style="margin-top:10px"><b>${esc(t("d_unsure"))}</b></p></div>`;
  } else {
    head = `<div class="res bad"><h2>${esc(t("invalidTitle"))}</h2><p>${esc(t("invalidText"))}</p></div>`;
    body = `<div class="card"><h3>${esc(t("photoTips"))}</h3><ul class="tips small">${(t("photoTipsBy")[r.check] || []).map((x) => `<li>${esc(x)}</li>`).join("")}</ul></div>`;
  }
  const qual = (r.quality.warnings || []).map((w) => `<div class="note">${esc(t("q_" + w))}</div>`).join("");
  const probs = r.probs.slice(0, 4).map((p) => `<div class="prob"><span>${esc(labelName(p.label, p.display))}</span><b>${Math.round(p.p * 100)}%</b>
      <div class="bar"><i style="width:${Math.round(p.p * 100)}%"></i></div></div>`).join("");
  const q = encodeURIComponent({ dentist: "dentist", dermatologist: "dermatologist", doctor: "doctor" }[r.doctor] + " near me");
  render(`
  <div class="head"><button class="back" data-go="${fromHistory ? "history" : "home"}" aria-label="${esc(t("back"))}">${icon("back")}</button>
    <div class="grow"><h2>${esc(checkTitle(r.check))}</h2><p class="muted small">${esc(fmtDate(r.created))}</p></div></div>
  <div class="stack">
    ${r.demo ? `<div class="note">${esc(t("demoWarn"))}</div>` : ""}
    <div class="imgbox"><img data-img="${r.id}:img" alt="" ${state.resultView === "heat" && r.has_heatmap ? "hidden" : ""} id="imgPhoto">
      ${r.has_heatmap ? `<img data-img="${r.id}:heat" alt="" id="imgHeat" ${state.resultView === "heat" ? "" : "hidden"}>` : ""}</div>
    ${r.has_heatmap ? `<div class="row between"><span class="seg" role="group">
        <button data-view="photo" aria-pressed="${state.resultView === "photo"}">${esc(t("photo"))}</button>
        <button data-view="heat" aria-pressed="${state.resultView === "heat"}">${esc(t("heat"))}</button></span></div>
      <p class="muted tiny" id="heatNote" ${state.resultView === "heat" ? "" : "hidden"}>${esc(t("heatNote"))}</p>` : ""}
    ${head}${qual}${body}
    <div class="card"><h3>${esc(t("others"))}</h3>${probs}</div>
    <a class="btn outline" href="https://www.google.com/maps/search/${q}" target="_blank" rel="noopener">${icon("map")} ${esc(t("findDoc", doc))}</a>
    <button class="btn outline" data-action="pdf" data-id="${r.id}">${icon("download")} ${esc(t("report"))}</button>
    <button class="btn" data-go="check/${r.check}">${esc(t("again"))}</button>
    ${fromHistory ? `<button class="btn danger sm" data-action="delone" data-id="${r.id}">${icon("trash")} ${esc(t("deleteOne"))}</button>` : ""}
  </div>
  ${disclaimer()}`, fromHistory ? "history" : "home");
}
T.en.back = "Back"; T.hi.back = "वापस";

async function historyScreen() {
  loading();
  const f = state.histFilter;
  const list = await api("/api/history" + (f === "all" ? "" : "?check=" + f));
  const chips = ["all", "oral", "skin", "infection", "nail"].map((c) =>
    `<button data-filter="${c}" aria-pressed="${f === c}">${esc(c === "all" ? t("all") : checkTitle(c))}</button>`).join("");
  const items = list.map((h) => {
    const pill = h.status === "ok" ? `<span class="pill ok">${Math.round(h.confidence * 100)}%</span>`
      : h.status === "uncertain" ? `<span class="pill warn">${esc(t("notSure"))}</span>` : `<span class="pill bad">${esc(t("invalidTitle"))}</span>`;
    return `<button class="card item" data-open="${h.id}"><img data-img="${h.id}:img" alt="">
      <div class="grow"><b>${esc(h.status === "ok" ? labelName(h.label, h.display) : checkTitle(h.check))}</b>
      <p class="muted small">${esc(checkTitle(h.check))} · ${esc(fmtDate(h.created))}</p></div>${pill}</button>`;
  }).join("");
  render(`<h1 style="margin-bottom:14px">${esc(t("history"))}</h1><div class="chips">${chips}</div>
    ${items || `<div class="empty">${esc(t("historyEmpty"))}</div>`}
    ${list.length ? `<button class="btn danger sm" data-action="clearall" style="margin-top:8px">${icon("trash")} ${esc(t("clearAll"))}</button>` : ""}
    ${disclaimer()}`, "history");
}

async function profileScreen() {
  loading();
  const me = await api("/api/me?tz=" + -new Date().getTimezoneOffset());
  state.me = me;
  let r; try { r = JSON.parse(store.get("hc_rem") || "null"); } catch { r = null; }
  r = r || { on: false, time: "20:00" };
  render(`
  <div class="top"><h1>${esc(t("profile"))}</h1></div>
  <div class="card row"><span class="avatar" style="cursor:default">${icon("user")}</span>
    <div><b>${esc(me.name)}</b><p class="muted small">${esc(me.email)}</p></div></div>
  <div class="grid2" style="margin-top:12px">
    <div class="card stat"><b>${me.stats.total}</b><span class="muted small">${esc(t("checksDone"))}</span></div>
    <div class="card stat"><b>${me.stats.streak}</b><span class="muted small">${esc(t("streak"))}</span></div></div>
  <div class="card" style="margin-top:12px">
    <div class="setting"><span>${esc(t("language"))}</span>${langSwitch()}</div>
    <div class="setting"><div><b>${esc(t("reminder"))}</b><p class="muted tiny">${esc(t("reminderHelp"))}</p></div>
      <label class="switch"><input type="checkbox" id="remOn" ${r.on ? "checked" : ""} aria-label="${esc(t("reminder"))}"><span></span></label></div>
    <div class="setting"><label for="remTime">${esc(t("reminderTime"))}</label><input type="time" id="remTime" value="${esc(r.time)}" style="width:160px"></div>
  </div>
  <p class="muted small" style="margin:14px 2px">${esc(t("privacy"))}</p>
  <div class="stack"><button class="btn outline" data-go="logout">${icon("logout")} ${esc(t("logout"))}</button>
    <button class="btn danger sm" data-action="delacc">${icon("trash")} ${esc(t("deleteAcc"))}</button></div>
  ${disclaimer()}`, "profile");
  const save = () => {
    const on = $("#remOn").checked;
    store.set("hc_rem", JSON.stringify({ on, time: $("#remTime").value || "20:00" }));
    if (on && "Notification" in window && Notification.permission === "default") Notification.requestPermission();
  };
  $("#remOn").addEventListener("change", save); $("#remTime").addEventListener("change", save);
}

function logoutScreen() {
  render(`<section class="confirm"><span class="tile">${icon("logout")}</span><h2>${esc(t("logoutTitle"))}</h2>
    <p>${esc(t("logoutText"))}</p>
    <button class="btn" data-action="dologout">${esc(t("yesLogout"))}</button>
    <button class="btn outline" data-go="home">${esc(t("cancel"))}</button></section>`, null);
}

// ------------------------------------------------------------------- router
async function route() {
  const parts = (location.hash.replace(/^#\/?/, "") || "").split("/");
  const page = parts[0] || "", arg = parts[1];
  const authed = !!store.get("hc_token");
  document.documentElement.lang = state.lang;
  try {
    if (!authed && page !== "signup") { if (page !== "login") { location.hash = "#/login"; return; } return authScreen("login"); }
    if (!authed) return authScreen("signup");
    if (!page || page === "login" || page === "signup") { location.hash = "#/home"; return; }
    if (!state.checks.length) state.checks = await api("/api/checks");
    switch (page) {
      case "home": return await homeScreen();
      case "check": return checkScreen(arg);
      case "result": if (!state.current) { location.hash = "#/home"; return; } return resultScreen(state.current, false);
      case "history":
        if (arg) { loading(); state.current = await api("/api/history/" + encodeURIComponent(arg)); return resultScreen(state.current, true); }
        return await historyScreen();
      case "profile": return await profileScreen();
      case "logout": return logoutScreen();
      default: location.hash = "#/home";
    }
  } catch (e) {
    if (e.message === "auth") return;
    render(`<div class="err" role="alert" style="margin-top:30px">${esc(e.message)}</div><p class="center" style="margin-top:14px"><button class="btn outline" onclick="location.reload()">OK</button></p>`, authed ? "home" : null);
  }
}

// ------------------------------------------------------------------- events
document.addEventListener("click", async (ev) => {
  const el = ev.target.closest("[data-go],[data-check],[data-action],[data-lang],[data-view],[data-filter],[data-open]");
  if (!el) return;
  const d = el.dataset;
  if (d.go) { location.hash = "#/" + d.go; return; }
  if (d.open) { location.hash = "#/history/" + d.open; return; }
  if (d.lang) { state.lang = d.lang; store.set("hc_lang", d.lang); route(); return; }
  if (d.filter) { state.histFilter = d.filter; route(); return; }
  if (d.view) {
    state.resultView = d.view;
    $("#imgPhoto").hidden = d.view === "heat"; const h = $("#imgHeat"); if (h) h.hidden = d.view !== "heat";
    $("#heatNote").hidden = d.view !== "heat";
    $$("[data-view]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.view === d.view)));
    return;
  }
  if (d.check && !d.action) {
    const c = state.checks.find((x) => x.id === d.check);
    if (c && !c.ready) { toast(t("soonText")); return; }
    location.hash = "#/check/" + d.check; return;
  }
  switch (d.action) {
    case "forgot": toast(t("forgotMsg")); break;
    case "cam": $("#cam").click(); break;
    case "gal": $("#gal").click(); break;
    case "analyse": analyse(d.check); break;
    case "pdf": {
      try {
        const res = await api(`/api/history/${d.id}/report`, { raw: true });
        const url = URL.createObjectURL(await res.blob());
        const a = document.createElement("a"); a.href = url; a.download = `health-check-${d.id}.pdf`; a.click();
        setTimeout(() => URL.revokeObjectURL(url), 5000);
      } catch (e) { if (e.message !== "auth") toast(e.message); }
      break;
    }
    case "delone":
      if (confirm(t("confirmDelOne"))) { try { await api("/api/history/" + d.id, { method: "DELETE" }); location.hash = "#/history"; } catch (e) { toast(e.message); } }
      break;
    case "clearall":
      if (confirm(t("confirmClear"))) { try { await api("/api/history", { method: "DELETE" }); route(); } catch (e) { toast(e.message); } }
      break;
    case "delacc":
      if (confirm(t("confirmDelAcc"))) { try { await api("/api/me", { method: "DELETE" }); clearSession(); location.hash = "#/login"; } catch (e) { toast(e.message); } }
      break;
    case "dologout":
      try { await api("/api/logout", { method: "POST", noRedirect: true }); } catch { /* token may already be gone */ }
      clearSession(); location.hash = "#/login"; break;
  }
});

document.addEventListener("submit", async (ev) => {
  if (ev.target.id !== "authForm") return;
  ev.preventDefault();
  const signup = !!$("#name"), err = $("#authErr"), btn = $("button[type=submit]", ev.target);
  err.hidden = true;
  const email = $("#email").value.trim(), pw = $("#pw").value;
  if (signup && pw !== $("#pw2").value) { err.textContent = t("pwMismatch"); err.hidden = false; return; }
  btn.disabled = true;
  try {
    const body = signup ? { name: $("#name").value, email, password: pw } : { email, password: pw };
    const res = await api(signup ? "/api/signup" : "/api/login", { method: "POST", body, noRedirect: true });
    store.set("hc_token", res.token); location.hash = "#/home"; route();
  } catch (e) { err.textContent = e.message; err.hidden = false; btn.disabled = false; }
});

// reminder: show a browser notification once a day while the app is open
setInterval(() => {
  if (!store.get("hc_token") || !("Notification" in window) || Notification.permission !== "granted") return;
  api("/api/me?tz=" + -new Date().getTimezoneOffset(), { noRedirect: true }).then((me) => {
    state.me = me;
    const today = new Date().toDateString();
    if (reminderDue() && store.get("hc_rem_last") !== today) {
      store.set("hc_rem_last", today);
      new Notification("Health Check", { body: t("reminderDue") });
    }
  }).catch(() => {});
}, 60000);

window.addEventListener("hashchange", route);
route();
})();
