/* Indian Law Assistant: mobile-first chat client for the FastAPI backend.
 * Talks to POST /chat/stream (NDJSON events: sources | token | final | error) and GET /pdf/{doc_id}.
 * Chat history lives in this device's localStorage; the backend only keeps a conversation_id for follow-ups. */
"use strict";

/* ------------------------------------------------------------------ i18n */
const T = {
  en: {
    title: "Law Assistant", sub: "Indian law · हिंदी / English", history: "Chats", new: "New chat", about: "About & settings",
    welcomeH: "Indian law, made understandable.", welcomeP: "Explore Indian legislation, understand your rights and get answers grounded in legal documents.",
    eyebrow: "Indian legal research", tryAsking: "Try asking", topics: "Popular topics", recent: "Recently explored", explore: "Explore legislation", qlabel: "Your question",
    viewSources: "View sources", panelTitle: "Sources", panelHint: "Retrieved from the original documents", collapse: "Collapse sidebar", expand: "Expand sidebar", openMenu: "Open menu", closePanel: "Close sources",
    overviewOf: "Give me an overview of",
    placeholder: "Ask your question…", foot: "Legal information, not legal advice.", details: "Details",
    searching: "Searching the law", writing: "Writing the answer", copy: "Copy", copied: "Copied", retry: "Try again",
    sources: "Sources", open: "Open original PDF page", page: "Page", ocr: "OCR", exact: "Exact section match",
    verified: "Number matches English text", unverified: "Number not found in English text",
    inferred: "Section number reconstructed from OCR",
    hindi: "Hindi", english: "English", error: "Something went wrong", stopped: "Stopped.", offline: "You are offline. Reconnect to ask questions.",
    delete: "Delete chat", confirmDelete: "Delete this chat from this device?", close: "Close", install: "Install app",
    openHistory: "Open chat history", ocrConf: "OCR confidence", newChat: "New chat", untitled: "New chat",
    aboutTitle: "About & disclaimer",
    aboutBody: [
      ["Legal information, not legal advice", ["This assistant explains what the available legal documents say. It can be incomplete, out of date, or wrong. It is not a lawyer and does not create an advocate–client relationship. For your own situation, consult a qualified advocate."]],
      ["What it reads", ["The Constitution of India, Bharatiya Nyaya Sanhita 2023, Bharatiya Nagarik Suraksha Sanhita 2023, Bharatiya Sakshya Adhiniyam 2023, the Information Technology Act 2000 and the Consumer Protection Act 2019, in English and Hindi."]],
      ["Hindi text and accuracy", ["Several Hindi PDFs are scans, so their text is read by OCR and can contain errors. Cards show the OCR confidence. If a provision cannot be read reliably, the assistant says so instead of guessing. Always check the original page using the link on each source."]],
      ["Your data", ["Questions go to the server running this app, which uses local models (no paid cloud AI). Chat history is stored only on this device."]],
      ["Install", ["Android Chrome: menu → Install app. iPhone Safari: Share → Add to Home Screen."]],
    ],
  },
  hi: {
    title: "विधि सहायक", sub: "भारतीय कानून · हिंदी / English", history: "चैट", new: "नई चैट", about: "परिचय व सेटिंग",
    welcomeH: "भारतीय कानून, सरल भाषा में।", welcomeP: "भारतीय कानूनों को जानें, अपने अधिकार समझें और कानूनी दस्तावेज़ों पर आधारित उत्तर पाएँ।",
    eyebrow: "भारतीय विधि शोध", tryAsking: "ये पूछ कर देखें", topics: "लोकप्रिय विषय", recent: "हाल की चैट", explore: "कानून देखें", qlabel: "आपका प्रश्न",
    viewSources: "स्रोत देखें", panelTitle: "स्रोत", panelHint: "मूल दस्तावेज़ों से प्राप्त", collapse: "साइडबार छोटा करें", expand: "साइडबार खोलें", openMenu: "मेनू खोलें", closePanel: "स्रोत बंद करें",
    overviewOf: "मुझे संक्षेप में बताइए:",
    placeholder: "अपना प्रश्न लिखें…", foot: "कानूनी जानकारी, कानूनी सलाह नहीं।", details: "विवरण",
    searching: "कानून खोजा जा रहा है", writing: "उत्तर लिखा जा रहा है", copy: "कॉपी", copied: "कॉपी हो गया", retry: "फिर कोशिश करें",
    sources: "स्रोत", open: "मूल PDF पृष्ठ खोलें", page: "पृष्ठ", ocr: "OCR", exact: "सटीक धारा मिलान",
    verified: "संख्या अंग्रेज़ी पाठ से मेल खाती है", unverified: "संख्या अंग्रेज़ी पाठ में नहीं मिली",
    inferred: "धारा संख्या OCR से पुनर्निर्मित",
    hindi: "हिंदी", english: "अंग्रेज़ी", error: "कुछ गड़बड़ हुई", stopped: "रोका गया।", offline: "आप ऑफ़लाइन हैं। प्रश्न पूछने के लिए कनेक्ट करें।",
    delete: "चैट हटाएँ", confirmDelete: "इस चैट को इस डिवाइस से हटाएँ?", close: "बंद करें", install: "ऐप इंस्टॉल करें",
    openHistory: "चैट इतिहास खोलें", ocrConf: "OCR विश्वसनीयता", newChat: "नई चैट", untitled: "नई चैट",
    aboutTitle: "परिचय व अस्वीकरण",
    aboutBody: [
      ["कानूनी जानकारी, कानूनी सलाह नहीं", ["यह सहायक बताता है कि उपलब्ध कानूनी दस्तावेज़ क्या कहते हैं। यह अधूरा, पुराना या गलत हो सकता है। यह वकील नहीं है। अपनी स्थिति के लिए किसी योग्य अधिवक्ता से परामर्श करें।"]],
      ["यह क्या पढ़ता है", ["भारत का संविधान, भारतीय न्याय संहिता 2023, भारतीय नागरिक सुरक्षा संहिता 2023, भारतीय साक्ष्य अधिनियम 2023, सूचना प्रौद्योगिकी अधिनियम 2000 और उपभोक्ता संरक्षण अधिनियम 2019, हिंदी और अंग्रेज़ी में।"]],
      ["हिंदी पाठ और सटीकता", ["कई हिंदी PDF स्कैन हैं, इसलिए उनका पाठ OCR से पढ़ा गया है और उसमें त्रुटियाँ हो सकती हैं। कार्ड पर OCR विश्वसनीयता दिखती है। यदि कोई प्रावधान भरोसेमंद रूप से नहीं पढ़ा जा सके, तो सहायक अनुमान लगाने के बजाय यह बता देता है। हर स्रोत के लिंक से मूल पृष्ठ अवश्य जाँचें।"]],
      ["आपका डेटा", ["प्रश्न इस ऐप चलाने वाले सर्वर पर जाते हैं, जो स्थानीय मॉडल इस्तेमाल करता है (कोई सशुल्क क्लाउड AI नहीं)। चैट इतिहास केवल इसी डिवाइस पर रहता है।"]],
      ["इंस्टॉल", ["Android Chrome: मेनू → ऐप इंस्टॉल करें। iPhone Safari: शेयर → होम स्क्रीन में जोड़ें।"]],
    ],
  },
};
const EXAMPLES = {
  en: ["What are my fundamental rights under the Constitution?", "Explain Section 103 of BNS.", "What is the difference between BNS and IPC?", "What are my rights if I am arrested?"],
  hi: ["संविधान के तहत मेरे मौलिक अधिकार क्या हैं?", "BNS की धारा 103 समझाइए।", "BNS और IPC में क्या अंतर है?", "गिरफ्तार होने पर मेरे क्या अधिकार हैं?"],
};
/* Topic chips are plain prompts that run the normal RAG query; they are not data or statistics. */
const TOPICS = {
  en: [["Fundamental rights", "What are the fundamental rights in the Constitution of India?"], ["Arrest and bail", "What are the rules on arrest and bail?"], ["Consumer complaints", "How do I file a consumer complaint for a defective product?"],
       ["Cyber offences", "What offences does the IT Act 2000 cover?"], ["Theft and robbery", "What is the punishment for theft?"], ["Evidence", "What counts as evidence under the Bharatiya Sakshya Adhiniyam?"]],
  hi: [["मौलिक अधिकार", "भारत के संविधान में मौलिक अधिकार क्या हैं?"], ["गिरफ्तारी और जमानत", "गिरफ्तारी और जमानत के नियम क्या हैं?"], ["उपभोक्ता शिकायत", "दोषपूर्ण वस्तु के लिए उपभोक्ता शिकायत कैसे दर्ज करें?"],
       ["साइबर अपराध", "आईटी अधिनियम 2000 में कौन से अपराध आते हैं?"], ["चोरी", "चोरी की सजा क्या है?"], ["साक्ष्य", "भारतीय साक्ष्य अधिनियम के तहत क्या साक्ष्य माना जाता है?"]],
};
const ACTS = [["Constitution of India", "COI", "the Constitution of India"], ["Bharatiya Nyaya Sanhita, 2023", "BNS", "the Bharatiya Nyaya Sanhita, 2023"], ["Bharatiya Nagarik Suraksha Sanhita, 2023", "BNSS", "the Bharatiya Nagarik Suraksha Sanhita, 2023"],
              ["Bharatiya Sakshya Adhiniyam, 2023", "BSA", "the Bharatiya Sakshya Adhiniyam, 2023"], ["Information Technology Act, 2000", "IT", "the Information Technology Act, 2000"], ["Consumer Protection Act, 2019", "CPA", "the Consumer Protection Act, 2019"]];

/* ------------------------------------------------------------------ state */
const $ = id => document.getElementById(id);
const STORE_KEY = "ila.v1", MAX_CHATS = 30;
let state = { chats: [], activeId: null, lang: "auto" };
let busy = false, abortCtl = null, deferredInstall = null;
let HINDI = false;   // set from /health: Hindi support is paused until the server says otherwise

/* About-sheet sections; while Hindi is paused the Hindi/OCR section is replaced by a plain language notice */
function aboutSections(l) {
  const sections = T[l].aboutBody;
  if (HINDI) return sections;
  const englishOnly = sections.map((sec, i) => i === 1
    ? ["What it reads", ["The Constitution of India, Bharatiya Nyaya Sanhita 2023, Bharatiya Nagarik Suraksha Sanhita 2023, Bharatiya Sakshya Adhiniyam 2023, the Information Technology Act 2000 and the Consumer Protection Act 2019 (English texts)."]]
    : i === 2
    ? ["Language", ["Currently English only. Hindi support is paused while the Hindi source documents are being verified."]] : sec);
  englishOnly.splice(2, 0, ["Known limitations", [
    "Answers come from a small local model and can be wrong, incomplete or too general, especially on questions that compare several provisions (for example bailable versus non-bailable offences). Always read the cited source text.",
    "Long provisions (such as the definitions sections) may be shown only in part. A yellow or red note under an answer means the checker found something to verify; “Incomplete answer” means the reply was cut off.",
    "Replies are generated on this computer and typically take one to two minutes."]]);
  return englishOnly;
}

function load() {
  try {
    const raw = JSON.parse(localStorage.getItem(STORE_KEY) || "null");
    if (raw && Array.isArray(raw.chats)) state = { ...state, ...raw };
  } catch (e) { /* private mode or corrupt data: start fresh */ }
  state.chats.forEach(c => { c.messages = c.messages.filter(m => !m.pending); });
}
function save() {
  state.chats = state.chats.sort((a, b) => b.updated - a.updated).slice(0, MAX_CHATS);
  try { localStorage.setItem(STORE_KEY, JSON.stringify(state)); } catch (e) { /* storage full or blocked */ }
}
const activeChat = () => state.chats.find(c => c.id === state.activeId) || null;

function uiLang() {
  if (!HINDI) return "en";
  if (state.lang === "en" || state.lang === "hi") return state.lang;
  const chat = activeChat();
  const lastBot = chat && [...chat.messages].reverse().find(m => m.role === "assistant" && m.language);
  if (lastBot) return lastBot.language;
  return (navigator.language || "en").toLowerCase().startsWith("hi") ? "hi" : "en";
}
const t = key => T[uiLang()][key];

/* ------------------------------------------------------------------ small helpers */
function el(tag, cls, text) {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text != null) n.textContent = text;
  return n;
}
function toast(msg) {
  const n = $("toast"); n.textContent = msg; n.hidden = false;
  clearTimeout(toast.timer); toast.timer = setTimeout(() => { n.hidden = true; }, 1800);
}
function nearBottom() { const m = $("messages"); return m.scrollHeight - m.scrollTop - m.clientHeight < 90; }
function scrollBottom(force) { const m = $("messages"); if (force || nearBottom()) m.scrollTop = m.scrollHeight; }
function chev() { const s = document.createElementNS("http://www.w3.org/2000/svg", "svg"); s.setAttribute("viewBox", "0 0 24 24"); s.setAttribute("class", "chev"); s.setAttribute("aria-hidden", "true"); const p = document.createElementNS("http://www.w3.org/2000/svg", "path"); p.setAttribute("d", "M6 9l6 6 6-6"); s.appendChild(p); return s; }

/* ------------------------------------------------------------------ i18n application */
function applyI18n() {
  const l = uiLang(), s = T[l];
  document.documentElement.lang = l;
  $("t-title").textContent = s.title; $("t-sub").textContent = HINDI ? s.sub : "Indian law · English";
  $("t-explore").textContent = s.explore; $("t-eyebrow").textContent = s.eyebrow; $("t-try").textContent = s.tryAsking; $("t-topics").textContent = s.topics; $("t-recent").textContent = s.recent;
  $("t-qlabel").textContent = s.qlabel; $("panel-title").textContent = s.panelTitle; $("panel-hint").textContent = s.panelHint; $("close-panel").setAttribute("aria-label", s.closePanel);
  syncCollapseLabels();
  $("lang").hidden = !HINDI;
  $("t-history").textContent = s.history; $("t-new").textContent = s.new; $("t-about").textContent = s.about;
  $("t-welcome-h").textContent = s.welcomeH; $("t-welcome-p").textContent = s.welcomeP;
  $("t-foot").textContent = s.foot; $("t-details").textContent = s.details;
  $("q").placeholder = s.placeholder; $("offline").textContent = s.offline;
  $("new-chat").setAttribute("aria-label", s.newChat); $("open-about").setAttribute("aria-label", s.about);
  $("close-drawer").setAttribute("aria-label", s.close);
  $("about-title").textContent = s.aboutTitle; $("close-about").textContent = s.close; $("install").textContent = s.install;
  $("send").setAttribute("aria-label", l === "hi" ? "भेजें" : "Send"); $("stop").setAttribute("aria-label", l === "hi" ? "रोकें" : "Stop");
  const body = $("about-body"); body.textContent = "";
  aboutSections(l).forEach(([h, ps]) => { body.appendChild(el("h3", null, h)); ps.forEach(p => body.appendChild(el("p", null, p))); });
  const tp = $("topics"); tp.textContent = "";
  TOPICS[l].forEach(([label, q]) => { const b = el("button", "topic", label); b.type = "button"; b.onclick = () => ask(q); tp.appendChild(b); });
  const acts = $("acts"); acts.textContent = "";
  ACTS.forEach(([name, abbr, phrase]) => {
    const li = el("li"), b = el("button"); b.type = "button"; b.append(el("span", null, name), el("span", "abbr", abbr));
    b.onclick = () => { closeDrawerIfOpen(); ask(l === "hi" ? `${s.overviewOf} ${name}` : `${s.overviewOf} ${phrase}.`); }; li.appendChild(b); acts.appendChild(li);
  });
  renderRecent();
  const ex = $("examples"); ex.textContent = "";
  EXAMPLES[l].filter(q => HINDI || !/[ऀ-ॿ]/.test(q)).forEach(q => { const b = el("button", "chip", q); b.type = "button"; b.onclick = () => ask(q); ex.appendChild(b); });
  document.querySelectorAll("#lang button").forEach(b => b.setAttribute("aria-checked", String(b.dataset.lang === state.lang)));
}

/* ------------------------------------------------------------------ markdown (safe: builds DOM, never innerHTML) */
function inline(parent, text, onCite) {
  text.split(/(\*\*[^*]+\*\*|\[\d{1,2}\])/).forEach(part => {
    if (!part) return;
    let m;
    if ((m = part.match(/^\*\*([^*]+)\*\*$/))) parent.appendChild(el("strong", null, m[1]));
    else if ((m = part.match(/^\[(\d{1,2})\]$/))) {
      const b = el("button", "cite", part); b.type = "button"; b.setAttribute("aria-label", `Source ${m[1]}`);
      b.onclick = () => onCite(m[1]); parent.appendChild(b);
    } else parent.appendChild(document.createTextNode(part));
  });
}
function renderMarkdown(container, text, onCite) {
  container.textContent = "";
  let list = null, para = null, quote = null;
  const flush = () => { list = null; para = null; quote = null; };
  text.split("\n").forEach(raw => {
    const line = raw.trimEnd(), li = line.match(/^\s*(?:[-*•]|\d+[.)])\s+(.*)$/);
    if (!line.trim()) { flush(); return; }
    const hd = line.match(/^(#{1,4})\s+(.*)$/), bq = line.match(/^>\s?(.*)$/);
    if (hd) { flush(); const h = el(hd[1].length <= 2 ? "h3" : "h4"); inline(h, hd[2], onCite); container.appendChild(h); return; }
    if (bq) { list = null; para = null; if (!quote) { quote = el("blockquote"); container.appendChild(quote); quote.appendChild(el("p")); } else quote.firstChild.appendChild(document.createElement("br")); inline(quote.firstChild, bq[1], onCite); return; }
    quote = null;
    if (li) {
      if (!list) { list = el(/^\s*\d/.test(line) ? "ol" : "ul"); container.appendChild(list); }
      const item = el("li"); inline(item, li[1], onCite); list.appendChild(item); para = null;
    } else {
      list = null;
      if (!para) { para = el("p"); container.appendChild(para); } else para.appendChild(document.createElement("br"));
      inline(para, line.replace(/^#{1,4}\s*/, ""), onCite);
    }
  });
}

/* ------------------------------------------------------------------ citation cards */
function ocrClass(s) { return s.low_quality || s.ocr_conf < 80 ? "bad" : s.ocr_conf < 90 ? "warn" : "ok"; }
function tag(text, cls) { return el("span", "tag" + (cls ? " " + cls : ""), text); }

function buildCard(s, idx, prefix = "c") {
  const d = el("details", "card"); d.id = `${prefix}-${idx}-${s.n}`;
  const sum = el("summary");
  sum.appendChild(el("span", "num", String(s.n)));
  const main = el("div", "card-main");
  main.appendChild(el("div", "card-title", s.label));
  const pages = s.page_end !== s.page_start ? `${s.page_start}–${s.page_end}` : `${s.page_start}`;
  let sub = `${s.language === "hi" ? t("hindi") : t("english")} · ${t("page")} ${pages}`;
  if (s.text_source === "ocr") sub += ` · ${t("ocr")} ${Math.round(s.ocr_conf)}%`;
  main.appendChild(el("div", "card-sub", sub));
  sum.appendChild(main); sum.appendChild(chev()); d.appendChild(sum);

  const body = el("div", "card-body"), tags = el("div", "tags");
  tags.appendChild(tag(s.act_name));
  tags.appendChild(tag(`${s.unit_label} ${s.section_number}`));
  tags.appendChild(tag(s.language === "hi" ? t("hindi") : t("english")));
  tags.appendChild(tag(`${t("page")} ${pages}`));
  if (s.text_source === "ocr") tags.appendChild(tag(`${t("ocrConf")}: ${Math.round(s.ocr_conf)}%`, ocrClass(s)));
  if (s.language === "hi" && s.number_verified !== -1) tags.appendChild(tag(s.number_verified === 1 ? t("verified") : t("unverified"), s.number_verified === 1 ? "ok" : "warn"));
  if (s.number_inferred) tags.appendChild(tag(t("inferred"), "warn"));
  if (s.match === "exact") tags.appendChild(tag(t("exact"), "ok"));
  body.appendChild(tags);
  const snip = el("p", "snippet", s.snippet + (s.snippet.length >= 400 ? "…" : "")); if (s.language === "hi") snip.lang = "hi";
  body.appendChild(snip);
  const a = el("a", "pdf-link", `${t("open")} →`);
  a.href = `/pdf/${encodeURIComponent(s.doc_id)}#page=${s.page_start}`; a.target = "_blank"; a.rel = "noopener";
  body.appendChild(a); d.appendChild(body);
  return d;
}

/* ------------------------------------------------------------------ message rendering */
function openCard(idx, n) {
  const card = document.getElementById(`c-${idx}-${n}`); if (!card) return;
  card.open = true; card.classList.add("flash"); card.scrollIntoView({ block: "center", behavior: "smooth" });
  setTimeout(() => card.classList.remove("flash"), 1400);
}
function plainText(msg) {
  const lines = [msg.text];
  (msg.sources || []).forEach(s => lines.push(`[${s.n}] ${s.label}, p. ${s.page_start} (${s.file})`));
  return lines.join("\n");
}
function fillBot(bubble, msg, idx) {
  bubble.textContent = ""; bubble.className = "bubble";
  if (msg.error) {
    bubble.classList.add("error"); bubble.appendChild(el("div", null, `${t("error")}: ${msg.error}`));
    const r = el("button", "tool", t("retry")); r.type = "button"; r.onclick = () => retry(idx); bubble.appendChild(r); return;
  }
  if (msg.pending && !msg.text) {
    const ty = el("div", "typing"); ty.setAttribute("role", "status");
    ty.append(el("i"), el("i"), el("i"), el("span", null, msg.stage === "writing" ? t("writing") : t("searching")));
    bubble.appendChild(ty);
    if (uiLang() === "en") bubble.appendChild(el("div", "wait-hint", "Runs on a local model: this can take a minute or two."));
    return;
  }
  if (msg.status && msg.status !== "answered" && msg.status !== "greeting") bubble.classList.add("info");
  const md = el("div", "md"); renderMarkdown(md, msg.text, n => openPanel(idx, n));
  if (msg.pending) md.classList.add("caret");
  bubble.appendChild(md);
  if (msg.pending) return;
  if (msg.notes && msg.notes.length) {
    const n = el("div", "notes");
    // severity from the backend's fixed note wording: cut-off answers and confirmed verification errors stand out
    msg.notes.forEach(x => n.appendChild(el("div", "note" + (/^(Incomplete answer|Verification error|अधूरा उत्तर|सत्यापन त्रुटि)/.test(x) ? " bad" : ""), x)));
    bubble.appendChild(n);
  }
  if (msg.sources && msg.sources.length) {
    const box = el("div", "sources"); box.appendChild(el("div", "sources-title", `${t("sources")} (${msg.sources.length})`));
    msg.sources.forEach(s => box.appendChild(buildCard(s, idx))); bubble.appendChild(box);
  }
  if (msg.status === "answered") {
    const tools = el("div", "tools"), c = el("button", "tool", t("copy")); c.type = "button";
    c.onclick = async () => { try { await navigator.clipboard.writeText(plainText(msg)); toast(t("copied")); } catch (e) { toast("—"); } };
    if (msg.sources && msg.sources.length) {
      const v = el("button", "tool strong", `${t("viewSources")} (${msg.sources.length})`); v.type = "button"; v.onclick = () => openPanel(idx); tools.appendChild(v);
    }
    tools.appendChild(c); bubble.appendChild(tools);
  }
  if (msg.disclaimer) bubble.appendChild(el("div", "disc", msg.disclaimer));
}
function renderRow(msg, idx) {
  const row = el("div", "row " + (msg.role === "user" ? "user" : "bot")), bubble = el("div", "bubble");
  row.appendChild(bubble);
  if (msg.role === "user") bubble.textContent = msg.text; else fillBot(bubble, msg, idx);
  if (msg.role === "user" && /[ऀ-ॿ]/.test(msg.text)) bubble.lang = "hi";
  row._bubble = bubble; return row;
}
function renderMessages() {
  const box = $("messages"), chat = activeChat();
  box.querySelectorAll(".row").forEach(r => r.remove());
  $("welcome").hidden = !!(chat && chat.messages.length);
  syncHome(); closePanel();
  (chat ? chat.messages : []).forEach((m, i) => box.appendChild(renderRow(m, i)));
  scrollBottom(true);
}

/* ------------------------------------------------------------------ history drawer */
function dateLabel(ts) {
  return new Date(ts).toLocaleDateString(uiLang() === "hi" ? "hi-IN" : "en-IN", { day: "numeric", month: "short" });
}
function renderHistory() {
  const h = $("history"); h.textContent = "";
  if (!state.chats.length) { h.appendChild(el("div", "history-empty", "—")); return; }
  [...state.chats].sort((a, b) => b.updated - a.updated).forEach(c => {
    const item = el("div", "h-item" + (c.id === state.activeId ? " active" : ""));
    const open = el("button", "h-open"); open.type = "button";
    if (c.id === state.activeId) open.setAttribute("aria-current", "true");
    open.append(el("span", "h-title", c.title), el("span", "h-date", dateLabel(c.updated)));
    open.onclick = () => { switchChat(c.id); closeDrawer(); };
    const del = el("button", "icon-btn h-del"); del.type = "button"; del.setAttribute("aria-label", `${t("delete")}: ${c.title}`);
    del.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M10 11v6M14 11v6M6 7l1 12h10l1-12M9 7V4h6v3"/></svg>';
    del.onclick = () => { if (confirm(t("confirmDelete"))) deleteChat(c.id); };
    item.append(open, del); h.appendChild(item);
  });
}
const wide = () => matchMedia("(min-width: 1100px)").matches;
function renderRecent() {
  const box = $("recent"), items = [...state.chats].sort((a, b) => b.updated - a.updated).slice(0, 3);
  box.textContent = ""; $("recent-wrap").hidden = !items.length;
  items.forEach(c => {
    const b = el("button"); b.type = "button"; b.append(el("span", "r-title", c.title), el("span", "r-date", dateLabel(c.updated)));
    b.onclick = () => switchChat(c.id); box.appendChild(b);
  });
}
/* Home state: on desktop the question box sits under the headline; on phones it stays pinned to the bottom. */
function syncHome() {
  const home = !$("welcome").hidden, form = $("form"), slot = $("composer-slot"), main = $("main");
  main.classList.toggle("home", home);
  const target = home && matchMedia("(min-width: 1100px)").matches ? slot : main;
  if (form.parentNode !== target) { target.appendChild(form); if (target === slot && !matchMedia("(pointer: coarse)").matches) form.querySelector("textarea").focus({ preventScroll: true }); }
}
/* Source panel: a docked column on wide screens, otherwise a side drawer / bottom sheet */
let panelOpener = null;
function openPanel(idx, n) {
  const chat = activeChat(), msg = chat && chat.messages[idx]; if (!msg || !msg.sources || !msg.sources.length) return;
  const body = $("panel-body"); body.textContent = "";
  msg.sources.forEach(s => body.appendChild(buildCard(s, idx, "p")));
  const panel = $("panel"); if (!panel.classList.contains("open")) panelOpener = document.activeElement;
  panel.classList.add("open"); if (!matchMedia("(min-width: 1280px)").matches) $("panel-scrim").hidden = false;
  const target = (n != null && document.getElementById(`p-${idx}-${n}`)) || body.querySelector("details.card");
  if (target) { target.open = true; if (n != null) { target.classList.add("flash"); setTimeout(() => target.classList.remove("flash"), 1400); } setTimeout(() => target.scrollIntoView({ block: "nearest", behavior: "smooth" }), 280); }
  panel.focus({ preventScroll: true });
}
function closePanel() {
  if (!$("panel").classList.contains("open")) return;
  $("panel").classList.remove("open"); $("panel-scrim").hidden = true;
  if (panelOpener && document.contains(panelOpener)) panelOpener.focus({ preventScroll: true }); panelOpener = null;
}
function syncCollapseLabels() {
  const c = $("app").classList.contains("collapsed"), s = T[uiLang()];
  $("collapse").setAttribute("aria-label", s.collapse); $("collapse").setAttribute("aria-expanded", String(!c));
  $("open-drawer").setAttribute("aria-label", s.openMenu);
}
function setCollapsed(on) {
  $("app").classList.toggle("collapsed", on); try { localStorage.setItem("ila.side", on ? "0" : "1"); } catch (e) {}
  syncCollapseLabels(); if (on) $("open-drawer").focus(); else $("collapse").focus();
}
function openDrawer() {
  $("drawer").classList.add("open"); $("scrim").hidden = false; $("open-drawer").setAttribute("aria-expanded", "true");
  document.querySelector(".main").inert = true; $("drawer").focus();
}
function closeDrawer() {
  if (wide()) return;
  $("drawer").classList.remove("open"); $("scrim").hidden = true; $("open-drawer").setAttribute("aria-expanded", "false");
  document.querySelector(".main").inert = false; $("open-drawer").focus();
}
function switchChat(id) { state.activeId = id; save(); applyI18n(); renderMessages(); renderHistory(); }
function deleteChat(id) {
  state.chats = state.chats.filter(c => c.id !== id);
  if (state.activeId === id) state.activeId = null;
  save(); applyI18n(); renderMessages(); renderHistory();
}
function newChat() {
  if (busy) return;
  state.activeId = null; save(); applyI18n(); renderMessages(); renderHistory(); $("q").focus();
}

/* ------------------------------------------------------------------ asking */
function setBusy(on) {
  busy = on; $("send").hidden = on; $("stop").hidden = !on; $("q").disabled = false;
  $("messages").setAttribute("aria-busy", String(on));
}
function retry(idx) {
  const chat = activeChat(); if (!chat || busy) return;
  const question = chat.messages[idx - 1] && chat.messages[idx - 1].text;
  if (!question) return;
  chat.messages.splice(idx - 1, 2);          // drop the question and its failed answer; ask() re-adds both
  renderMessages(); ask(question);
}

async function ask(question) {
  question = question.trim(); if (!question || busy) return;
  let chat = activeChat();
  if (!chat) {
    chat = { id: crypto.randomUUID ? crypto.randomUUID() : String(Date.now()), cid: null, title: question.slice(0, 44), updated: Date.now(), messages: [] };
    state.chats.push(chat); state.activeId = chat.id;
  }
  chat.messages.push({ role: "user", text: question });
  const msg = { role: "assistant", text: "", pending: true, stage: "searching" };
  chat.messages.push(msg); chat.updated = Date.now();
  $("welcome").hidden = true; syncHome();
  const idx = chat.messages.length - 1, box = $("messages");
  const row = renderRow(msg, idx), userRow = renderRow(chat.messages[idx - 1], idx - 1);
  box.append(userRow, row); scrollBottom(true);
  $("q").value = ""; autosize(); setBusy(true); closeDrawerIfOpen();

  abortCtl = new AbortController();
  try {
    const res = await fetch("/chat/stream", {
      method: "POST", headers: { "Content-Type": "application/json" }, signal: abortCtl.signal,
      body: JSON.stringify({ question, language: HINDI ? state.lang : "en", conversation_id: chat.cid }),
    });
    if (!res.ok) {
      let detail = `HTTP ${res.status}`;
      try { const j = await res.json(); if (j.detail) detail = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail); } catch (e) {}
      throw new Error(detail);
    }
    const reader = res.body.getReader(), dec = new TextDecoder(); let buf = "", got = false;
    for (;;) {
      const { done, value } = await reader.read(); if (done) break;
      buf += dec.decode(value, { stream: true });
      let nl;
      while ((nl = buf.indexOf("\n")) >= 0) {
        const line = buf.slice(0, nl).trim(); buf = buf.slice(nl + 1); if (!line) continue;
        const ev = JSON.parse(line);
        if (ev.type === "sources") { msg.stage = "writing"; msg.language = ev.language; chat.cid = ev.conversation_id; fillBot(row._bubble, msg, idx); }
        else if (ev.type === "token") { msg.text += ev.text; fillBot(row._bubble, msg, idx); scrollBottom(); }
        else if (ev.type === "final") {
          got = true; chat.cid = ev.conversation_id;
          Object.assign(msg, { text: ev.answer, status: ev.status, sources: ev.sources, notes: ev.notes, disclaimer: ev.disclaimer, language: ev.language, pending: false, stage: null });
        } else if (ev.type === "error") throw new Error(ev.message);
      }
    }
    if (!got) throw new Error("No response received");
  } catch (err) {
    if (err.name === "AbortError") {
      msg.pending = false; msg.text = (msg.text ? msg.text + "\n\n" : "") + t("stopped"); msg.status = "stopped";
    } else { msg.pending = false; msg.error = err.message === "Failed to fetch" ? t("offline") : err.message; msg.text = ""; }
  } finally {
    msg.pending = false; chat.updated = Date.now(); save();
    applyI18n(); fillBot(row._bubble, msg, idx); renderHistory(); scrollBottom(true);
    setBusy(false); abortCtl = null; if (!matchMedia("(pointer: coarse)").matches) $("q").focus();
  }
}
function closeDrawerIfOpen() { if ($("drawer").classList.contains("open")) closeDrawer(); }

/* ------------------------------------------------------------------ composer, viewport, events */
function autosize() {
  const q = $("q"); q.style.height = "auto";
  const h = q.scrollHeight + (q.offsetHeight - q.clientHeight);   // border-box: scrollHeight excludes the border
  q.style.height = Math.min(h, 132) + "px"; q.style.overflowY = h > 132 ? "auto" : "hidden";
}

function fitViewport() {  // keeps the composer above the on-screen keyboard (esp. iOS Safari and older Android)
  const vv = window.visualViewport; if (!vv) return;
  document.documentElement.style.setProperty("--app-h", vv.height + "px");
  if (vv.offsetTop) window.scrollTo(0, 0);
  scrollBottom();
}

async function init() {
  try { HINDI = !!(await (await fetch("/health")).json()).hindi_enabled; } catch (e) { HINDI = false; }
  if (!HINDI) state.lang = "en";
  load(); if (!HINDI) state.lang = "en";
  applyI18n(); renderMessages(); renderHistory();

  $("form").addEventListener("submit", e => { e.preventDefault(); ask($("q").value); });
  $("q").addEventListener("input", autosize);
  $("q").addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey && !e.isComposing && e.keyCode !== 229) { e.preventDefault(); $("form").requestSubmit(); }
  });
  $("stop").onclick = () => abortCtl && abortCtl.abort();

  document.querySelectorAll("#lang button").forEach(b => b.addEventListener("click", () => {
    state.lang = b.dataset.lang; save(); applyI18n(); renderMessages(); renderHistory();
  }));
  $("new-chat").onclick = $("new-chat-drawer").onclick = () => { newChat(); closeDrawerIfOpen(); };
  $("open-drawer").onclick = () => wide() ? setCollapsed(false) : openDrawer();
  $("close-drawer").onclick = closeDrawer; $("scrim").onclick = closeDrawer; $("collapse").onclick = () => setCollapsed(true);
  $("close-panel").onclick = closePanel; $("panel-scrim").onclick = closePanel;
  try { if (localStorage.getItem("ila.side") === "0") $("app").classList.add("collapsed"); } catch (e) {}
  syncCollapseLabels();
  document.addEventListener("keydown", e => {
    if (e.key !== "Escape") return;
    if ($("panel").classList.contains("open")) closePanel(); else if ($("drawer").classList.contains("open")) closeDrawer();
  });

  const about = $("about"), openAbout = () => { closeDrawerIfOpen(); about.showModal(); };
  ["open-about", "open-about-drawer", "open-about-foot"].forEach(id => $(id).addEventListener("click", openAbout));
  $("close-about").onclick = () => about.close();
  about.addEventListener("click", e => { if (e.target === about) about.close(); });

  const syncOnline = () => { $("offline").hidden = navigator.onLine; };
  addEventListener("online", syncOnline); addEventListener("offline", syncOnline); syncOnline();

  if (window.visualViewport) { visualViewport.addEventListener("resize", fitViewport); visualViewport.addEventListener("scroll", fitViewport); }
  matchMedia("(min-width: 1100px)").addEventListener("change", () => { $("drawer").classList.remove("open"); $("scrim").hidden = true; document.querySelector(".main").inert = false; syncHome(); });
  matchMedia("(min-width: 1280px)").addEventListener("change", () => { $("panel-scrim").hidden = true; });

  addEventListener("beforeinstallprompt", e => { e.preventDefault(); deferredInstall = e; $("install").hidden = false; });
  $("install").onclick = async () => { if (!deferredInstall) return; deferredInstall.prompt(); await deferredInstall.userChoice; deferredInstall = null; $("install").hidden = true; };
  addEventListener("appinstalled", () => { $("install").hidden = true; });

  if ("serviceWorker" in navigator) navigator.serviceWorker.register("/sw.js").catch(() => {});
}
init();
