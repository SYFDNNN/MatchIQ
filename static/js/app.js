"use strict";

const copy = {
  id: {
    skip: "Lewati ke prediktor",
    nav_predictor: "Prediktor",
    nav_model: "Model",
    nav_about: "Tentang",
    local: "Lokal",
    hero_eyebrow: "ANALISIS SEPAK BOLA • MODEL PER KOMPETISI",
    hero_line_one: "Lihat pertandingan.",
    hero_line_two: "Sebelum terjadi.",
    hero_lead: "Ubah data historis menjadi probabilitas pertandingan yang jernih, cepat, dan mudah dibaca.",
    hero_cta: "Mulai prediksi",
    hero_secondary: "Pelajari model",
    predict_kicker: "MATCH LAB",
    predict_title: "Prediksi satu pertandingan.",
    predict_intro: "Pilih dua tim. MatchIQ menggabungkan distribusi skor dan machine learning menjadi satu analisis.",
    competition: "Kompetisi",
    competition_hint: "Model dan daftar tim mengikuti kompetisi yang dipilih.",
    home_team: "Tim kandang",
    away_team: "Tim tandang",
    home_hint: "Sisi kiri simulasi",
    away_hint: "Sisi kanan simulasi",
    handicap: "Handicap kandang",
    handicap_hint: "Opsional untuk analisis HDP",
    analyze: "Analisis pertandingan",
    analyzing: "Menganalisis",
    home_short: "KANDANG",
    away_short: "TANDANG",
    expected_goals: "Expected goals",
    model_confidence: "Kejelasan hasil 1X2",
    clarity_note: "Indeks 0–100%: makin tinggi, makin dominan satu hasil. Bukan peluang prediksi benar.",
    exact_score_label: "Skor eksak paling mungkin",
    exact_score_probability: "Peluang skor ini",
    strongest_outcome: "Hasil 1X2 terkuat",
    win_result: "menang",
    score_outcome_note: "Skor eksak adalah satu kombinasi gol. Peluang menang mencakup semua skor kemenangan; peluang seri mencakup 0–0, 1–1, 2–2, dan seterusnya. Karena itu, 1–1 bisa menjadi skor eksak teratas meski satu tim lebih berpeluang menang.",
    data_depth: "Cakupan tim",
    coverage_note: "Menunjukkan apakah kedua tim dikenal model; bukan ukuran kelengkapan seluruh data.",
    model_version: "Model",
    outcome_title: "Probabilitas hasil",
    draw: "Seri",
    score_map: "Peta probabilitas skor",
    home_goals: "Gol kandang",
    away_goals: "Gol tandang",
    likely_scores: "Skor eksak paling mungkin",
    rank: "#",
    score: "Skor",
    probability: "Probabilitas",
    tier: "Level",
    goal_markets: "Pola gol",
    both_score: "Kedua tim mencetak gol",
    btts_note: "Probabilitas setidaknya satu gol dari masing-masing tim.",
    extended_title: "Analisis lanjutan",
    to_qualify: "Simulasi penentuan pemenang",
    qualify_note: "Peluang menang + separuh peluang seri. Asumsi 50:50 jika seri; tidak memperhitungkan agregat, perpanjangan waktu, atau penalti.",
    resilience_note: "Indeks perbandingan Elo dan performa terkini pada skala 0–10.",
    double_chance_note: "1X: kandang atau seri · X2: seri atau tandang · 12: salah satu tim menang.",
    heatmap_note: "Angka dalam %. Pilih sel untuk melihat skor dan peluangnya; gunakan tombol panah untuk berpindah.",
    over_under_note: "Total gol: ungu = di atas batas, biru = di bawah batas. Persentase di kanan adalah peluang di atas batas.",
    over: "Di atas",
    under: "Di bawah",
    stale: "Pilihan berubah. Klik Analisis pertandingan untuk memperbarui hasil.",
    loading_data: "Memuat data kompetisi…",
    retry: "Coba lagi",
    model_unavailable: "Model belum tersedia. Jalankan setup_windows.bat lalu coba lagi.",
    data_until: "Data hingga",
    model_pending: "Informasi model tersedia setelah data kompetisi dimuat.",
    wc_pipeline: "Hybrid v3 menggabungkan probabilitas 1X2 dari Dixon–Coles dan XGBoost terkalibrasi. Skor eksak dan pola gol berasal dari Dixon–Coles.",
    ucl_dc: "Membentuk distribusi skor dan pola gol. Total peluang menang/seri pada distribusi ini diselaraskan dengan probabilitas 1X2 model terpilih.",
    ucl_ml: "Model 1X2 terpilih melalui validasi musim berurutan, menggunakan fitur yang tersedia sebelum pertandingan.",
    ucl_pipeline: "Membandingkan kandidat XGBoost, regresi logistik, model dua tahap, Dixon–Coles, campuran, dan stacking melalui validasi waktu.",
    calibration: "Kalibrasi terpilih",
    calibration_none: "Tanpa koreksi tambahan",
    selection_note: "Komposisi ini berlaku untuk probabilitas 1X2. Dixon–Coles tetap membentuk skor eksak. Pilihan dapat berubah setelah pelatihan ulang.",
    handicap_cover: "Menutup handicap",
    odd_even: "Ganjil / genap",
    resilience: "Resiliensi",
    double_chance: "Double chance",
    win_to_nil: "Menang tanpa kebobolan",
    exact_goals: "Total gol tepat",
    result_note: "Probabilitas adalah estimasi model berdasarkan data historis, bukan kepastian hasil atau saran taruhan.",
    model_kicker: "DI DALAM MODEL",
    model_title: "Dua perspektif. Satu probabilitas.",
    model_intro: "Model mengikuti kompetisi yang dipilih di prediktor.",
    model_dc: "Mengestimasi gol dan seluruh kombinasi skor, dengan koreksi khusus untuk skor rendah.",
    model_xgb: "Membaca form, ELO, serangan, pertahanan, clean sheet, dan 30+ fitur time-aware.",
    model_hybrid: "Mengkalibrasi dan menggabungkan kedua keluaran agar analisis 1X2 dan pasar gol konsisten.",
    blend_label: "Bobot model untuk probabilitas 1X2",
    about_kicker: "TENTANG MATCHIQ",
    about_title: "Analisis yang terasa ringan, tanpa menyederhanakan modelnya.",
    about_body: "MatchIQ menyatukan prediksi Piala Dunia dan Liga Champions dalam satu aplikasi lokal, dengan dataset dan runtime yang tetap terpisah.",
    privacy: "Berjalan di localhost. Tidak ada akun, pelacak, atau data pertandingan yang dikirim keluar.",
    cta_title: "Pertandingan berikutnya sudah menunggu.",
    cta_body: "Pilih dua tim dan lihat bagaimana data membaca pertandingannya.",
    cta_button: "Buat prediksi",
    footer_local: "Local-first",
    featured_group: "Piala Dunia 2026",
    historical_group: "Tim historis",
    featured_clubs: "Klub UCL 2025–26",
    historical_clubs: "Klub UCL lainnya",
    yes: "Ya",
    no: "Tidak",
    high: "Tinggi",
    medium: "Sedang",
    low: "Rendah",
    balanced: "Berimbang",
    odd: "Ganjil",
    even: "Genap",
    cover: "menutup",
    qualify: "unggul dalam simulasi",
    home_favored: "lebih berpeluang menang",
    away_favored: "lebih berpeluang menang",
    draw_favored: "Seri menjadi hasil terkuat",
    prediction_failed: "Prediksi tidak dapat dibuat. Periksa server Flask lalu coba lagi.",
    same_team: "Pilih dua tim yang berbeda.",
    data_high: "Kedua tim dikenal",
    data_medium: "Satu tim dikenal",
    data_low: "Tim belum dikenal",
    push: "Imbang handicap",
  },
  en: {
    skip: "Skip to predictor",
    nav_predictor: "Predictor",
    nav_model: "Model",
    nav_about: "About",
    local: "Local",
    hero_eyebrow: "FOOTBALL ANALYSIS • COMPETITION-SPECIFIC MODELS",
    hero_line_one: "See the match.",
    hero_line_two: "Before it unfolds.",
    hero_lead: "Turn historical data into match probabilities that are clear, fast, and easy to read.",
    hero_cta: "Start predicting",
    hero_secondary: "Explore the model",
    predict_kicker: "MATCH LAB",
    predict_title: "Predict one match.",
    predict_intro: "Choose two teams. MatchIQ combines score distributions and machine learning into one analysis.",
    competition: "Competition",
    competition_hint: "The model and team list follow the selected competition.",
    home_team: "Home team",
    away_team: "Away team",
    home_hint: "Left side of the simulation",
    away_hint: "Right side of the simulation",
    handicap: "Home handicap",
    handicap_hint: "Optional HDP analysis",
    analyze: "Analyze match",
    analyzing: "Analyzing",
    home_short: "HOME",
    away_short: "AWAY",
    expected_goals: "Expected goals",
    model_confidence: "1X2 outcome clarity",
    clarity_note: "0–100% index: higher means one outcome is more dominant. This is not the probability of a correct prediction.",
    exact_score_label: "Most likely exact score",
    exact_score_probability: "Chance of this score",
    strongest_outcome: "Most likely 1X2 outcome",
    win_result: "win",
    score_outcome_note: "An exact score is one goal combination. A win includes every winning score; a draw includes 0–0, 1–1, 2–2, and so on. So 1–1 can be the top exact score even when one team is more likely to win.",
    data_depth: "Team coverage",
    coverage_note: "Shows whether both teams are known to the model; it does not measure completeness of all data.",
    model_version: "Model",
    outcome_title: "Outcome probability",
    draw: "Draw",
    score_map: "Score probability map",
    home_goals: "Home goals",
    away_goals: "Away goals",
    likely_scores: "Most likely exact scores",
    rank: "#",
    score: "Score",
    probability: "Probability",
    tier: "Tier",
    goal_markets: "Goal patterns",
    both_score: "Both teams to score",
    btts_note: "Probability that each team scores at least one goal.",
    extended_title: "Deeper analysis",
    to_qualify: "Winner simulation",
    qualify_note: "Win probability + half the draw probability. Assumes 50:50 after a draw; excludes aggregate scores, extra time, and penalties.",
    resilience_note: "A comparative index of Elo and recent form on a 0–10 scale.",
    double_chance_note: "1X: home or draw · X2: draw or away · 12: either team wins.",
    heatmap_note: "Values in %. Select a cell for its score and probability; use arrow keys to move.",
    over_under_note: "Total goals: purple = over the line, blue = under. The percentage on the right is the chance of going over.",
    over: "Over",
    under: "Under",
    stale: "Selection changed. Click Analyze match to update the results.",
    loading_data: "Loading competition data…",
    retry: "Try again",
    model_unavailable: "The model is unavailable. Run setup_windows.bat and try again.",
    data_until: "Data through",
    model_pending: "Model information will appear when competition data is loaded.",
    wc_pipeline: "Hybrid v3 combines 1X2 probabilities from Dixon–Coles and calibrated XGBoost. Exact scores and goal patterns come from Dixon–Coles.",
    ucl_dc: "Builds score distributions and goal patterns. The win/draw totals are aligned with the selected model’s 1X2 probabilities.",
    ucl_ml: "The 1X2 model selected using sequential season validation and features available before each match.",
    ucl_pipeline: "Compares XGBoost, logistic regression, two-stage models, Dixon–Coles, blends, and stacking using temporal validation.",
    calibration: "Selected calibration",
    calibration_none: "No additional correction",
    selection_note: "This composition applies to 1X2 probabilities. Dixon–Coles still shapes exact scores. Selection may change after retraining.",
    handicap_cover: "Handicap cover",
    odd_even: "Odd / even",
    resilience: "Resilience",
    double_chance: "Double chance",
    win_to_nil: "Win to nil",
    exact_goals: "Exact total goals",
    result_note: "Probabilities are model estimates based on historical data, not guaranteed outcomes or betting advice.",
    model_kicker: "INSIDE THE MODEL",
    model_title: "Two perspectives. One probability.",
    model_intro: "The model follows the competition selected in the predictor.",
    model_dc: "Estimates goals and every score combination, with a dedicated correction for low-scoring matches.",
    model_xgb: "Reads form, ELO, attack, defense, clean sheets, and 30+ time-aware features.",
    model_hybrid: "Calibrates and combines both outputs so 1X2 and goal analysis remain consistent.",
    blend_label: "Model weights for 1X2 probabilities",
    about_kicker: "ABOUT MATCHIQ",
    about_title: "Analysis that feels light without simplifying the model.",
    about_body: "MatchIQ brings World Cup and Champions League predictions into one local app while keeping their datasets and runtimes separate.",
    privacy: "Runs on localhost. No account, trackers, or match data are sent elsewhere.",
    cta_title: "The next match is already waiting.",
    cta_body: "Choose two teams and see how the data reads their matchup.",
    cta_button: "Create prediction",
    footer_local: "Local-first",
    featured_group: "World Cup 2026",
    historical_group: "Historical teams",
    featured_clubs: "2025–26 UCL clubs",
    historical_clubs: "Other UCL clubs",
    yes: "Yes",
    no: "No",
    high: "High",
    medium: "Medium",
    low: "Low",
    balanced: "Balanced",
    odd: "Odd",
    even: "Even",
    cover: "to cover",
    qualify: "leads this simulation",
    home_favored: "is more likely to win",
    away_favored: "is more likely to win",
    draw_favored: "Draw is the strongest outcome",
    prediction_failed: "The prediction could not be created. Check the Flask server and try again.",
    same_team: "Choose two different teams.",
    data_high: "Both teams known",
    data_medium: "One team known",
    data_low: "Teams unknown",
    push: "Handicap tie",
  },
};

const state = {
  language: localStorage.getItem("matchiq-language") === "en" ? "en" : "id",
  competitionId: localStorage.getItem("matchiq-competition") === "ucl" ? "ucl" : "world_cup",
  competitions: [],
  competitionMap: new Map(),
  currentCompetition: null,
  teams: [],
  teamMap: new Map(),
  prediction: null,
  model: null,
  loading: false,
  ready: false,
  feedback: null,
  errorKey: null,
};

const elements = {
  form: document.querySelector("#prediction-form"),
  competition: document.querySelector("#competition"),
  homeSelect: document.querySelector("#home-team"),
  awaySelect: document.querySelector("#away-team"),
  handicap: document.querySelector("#handicap"),
  homeFlag: document.querySelector("#home-flag"),
  awayFlag: document.querySelector("#away-flag"),
  swap: document.querySelector("#swap-teams"),
  language: document.querySelector("#language-toggle"),
  button: document.querySelector("#analyze-button"),
  buttonLabel: document.querySelector("[data-button-label]"),
  status: document.querySelector("#status-message"),
  result: document.querySelector("#result-content"),
};

function t(key) {
  return copy[state.language][key] ?? copy.id[key] ?? key;
}

function percent(value) {
  return new Intl.NumberFormat(state.language === "id" ? "id-ID" : "en-US", {
    style: "percent",
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  }).format(Number(value));
}

function number(value, digits = 2) {
  return new Intl.NumberFormat(state.language === "id" ? "id-ID" : "en-US", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(Number(value));
}

function translatedTier(value) {
  return t(value === "high" ? "high" : value === "medium" ? "medium" : "low");
}

function applyLanguage(language) {
  state.language = language;
  localStorage.setItem("matchiq-language", language);
  document.documentElement.lang = language;
  document.documentElement.dataset.language = language;
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    const key = node.dataset.i18n;
    if (copy[language][key]) node.textContent = copy[language][key];
  });
  document.querySelectorAll("[data-lang-option]").forEach((node) => {
    node.classList.toggle("active", node.dataset.langOption === language);
    node.setAttribute("aria-pressed", String(node.dataset.langOption === language));
  });
  elements.swap.setAttribute("aria-label", language === "id" ? "Tukar tim" : "Swap teams");
  elements.swap.title = language === "id" ? "Tukar tim" : "Swap teams";
  if (state.competitions.length) populateCompetitions(true);
  if (state.teams.length) populateTeams(true);
  if (state.prediction) renderPrediction(state.prediction);
  renderModel();
  renderFeedback();
  if (state.errorKey) showError(state.errorKey);
  setLoading(state.loading);
}

function competitionName(competition) {
  return state.language === "id" ? competition.name_id : competition.name_en;
}

function populateCompetitions(preserve = true) {
  const selected = preserve ? state.competitionId : "world_cup";
  elements.competition.replaceChildren();
  state.competitions.forEach((competition) => {
    const option = document.createElement("option");
    option.value = competition.id;
    option.textContent = competitionName(competition);
    elements.competition.append(option);
  });
  elements.competition.value = state.competitionMap.has(selected) ? selected : "world_cup";
  state.competitionId = elements.competition.value;
  state.currentCompetition = state.competitionMap.get(state.competitionId) || null;
}

function optionFor(team) {
  const option = document.createElement("option");
  option.value = team.id;
  option.textContent = team.name;
  option.dataset.flag = team.flag;
  return option;
}

function populateSelect(select, selectedValue) {
  select.replaceChildren();
  const featured = document.createElement("optgroup");
  const clubMode = state.currentCompetition?.team_type === "club";
  featured.label = t(clubMode ? "featured_clubs" : "featured_group");
  const historical = document.createElement("optgroup");
  historical.label = t(clubMode ? "historical_clubs" : "historical_group");

  state.teams.forEach((team) => {
    (team.featured ? featured : historical).append(optionFor(team));
  });
  select.append(featured);
  if (historical.children.length) select.append(historical);
  if (state.teamMap.has(selectedValue)) select.value = selectedValue;
}

function populateTeams(preserve = false) {
  const defaults = state.currentCompetition?.default_matchup || { home: "France", away: "England" };
  const home = preserve ? elements.homeSelect.value : defaults.home;
  const away = preserve ? elements.awaySelect.value : defaults.away;
  populateSelect(elements.homeSelect, home);
  populateSelect(elements.awaySelect, away);
  if (!elements.homeSelect.value && state.teams.length) elements.homeSelect.value = state.teams[0].id;
  if (!elements.awaySelect.value && state.teams.length > 1) elements.awaySelect.value = state.teams[1].id;
  updateFormFlags();
}

function updateFormFlags() {
  elements.homeFlag.textContent = state.teamMap.get(elements.homeSelect.value)?.flag || "⚽";
  elements.awayFlag.textContent = state.teamMap.get(elements.awaySelect.value)?.flag || "⚽";
}

async function loadCompetitions() {
  const payload = await fetchPayload("/api/competitions");
  state.competitions = payload.competitions;
  state.competitionMap = new Map(state.competitions.map((competition) => [competition.id, competition]));
  if (!state.competitionMap.has(state.competitionId)) state.competitionId = payload.default;
  populateCompetitions(true);
}

async function loadTeams({ preserve = false } = {}) {
  const query = new URLSearchParams({ competition: state.competitionId });
  const payload = await fetchPayload(`/api/teams?${query}`);
  state.model = payload.model;
  state.currentCompetition = payload.competition;
  state.competitionMap.set(payload.competition.id, payload.competition);
  state.teams = payload.teams;
  state.teamMap = new Map(state.teams.map((team) => [team.id, team]));
  populateTeams(preserve);
  renderModel();
}

function setLoading(loading) {
  state.loading = loading;
  elements.button.disabled = loading;
  for (const control of [elements.competition, elements.homeSelect, elements.awaySelect, elements.handicap, elements.swap]) {
    control.disabled = loading || (!state.ready && control !== elements.competition);
  }
  elements.form.setAttribute("aria-busy", String(loading));
  elements.button.classList.toggle("loading", loading);
  elements.buttonLabel.textContent = loading ? t(state.ready ? "analyzing" : "loading_data") : t(state.ready ? "analyze" : "retry");
}

function showError(key) {
  state.errorKey = copy.id[key] ? key : "prediction_failed";
  elements.status.textContent = t(state.errorKey);
  elements.status.hidden = false;
}

function clearError() {
  state.errorKey = null;
  elements.status.hidden = true;
  elements.status.textContent = "";
}

function renderFeedback() {
  const node = document.querySelector("#form-feedback");
  node.hidden = !state.feedback;
  node.textContent = state.feedback ? t(state.feedback) : "";
}

function invalidatePrediction() {
  state.prediction = null;
  elements.result.hidden = true;
  state.feedback = "stale";
  clearError();
  renderFeedback();
  updateFormFlags();
}

async function fetchPayload(url, options = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 30000);
  try {
    const response = await fetch(url, { ...options, signal: controller.signal });
    const payload = await response.json();
    if (!response.ok || !payload.ok) throw new Error(payload.error === "model_unavailable" ? "model_unavailable" : "prediction_failed");
    return payload;
  } finally {
    clearTimeout(timeout);
  }
}

async function requestPrediction({ scroll = false } = {}) {
  if (state.loading) return;
  if (!state.ready) return initialize();
  clearError();
  if (elements.homeSelect.value === elements.awaySelect.value) {
    showError("same_team");
    elements.awaySelect.focus();
    return;
  }
  state.prediction = null;
  elements.result.hidden = true;
  state.feedback = "analyzing";
  renderFeedback();
  setLoading(true);
  try {
    const payload = await fetchPayload("/api/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({
        competition: state.competitionId,
        home_team: elements.homeSelect.value,
        away_team: elements.awaySelect.value,
        handicap: Number(elements.handicap.value),
      }),
    });
    state.prediction = payload.prediction;
    renderPrediction(state.prediction);
    elements.result.hidden = false;
    if (scroll) {
      elements.result.scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "instant" : "smooth", block: "start" });
    }
  } catch (error) {
    showError(error.message);
  } finally {
    state.feedback = null;
    renderFeedback();
    setLoading(false);
  }
}

function setText(selector, value) {
  const node = document.querySelector(selector);
  if (node) node.textContent = value;
}

function setBar(selector, probability) {
  const node = document.querySelector(selector);
  if (node) node.style.width = `${Math.max(0, Math.min(100, Number(probability) * 100))}%`;
}

function renderModel() {
  const model = state.model;
  document.querySelector("#model-flow").hidden = !model;
  document.querySelector("#model-blend").hidden = !model;
  if (!model) {
    setText("#model-context", t("model_pending"));
    setText("#model-selection-note", "");
    return;
  }
  const ucl = model.pipeline_version === "ucl_v4_audited";
  const names = {
    logistic_compact: "Logistic Compact", xgb_compact: "XGBoost Compact",
    xgb_full: "XGBoost Full", xgb_depth3: "XGBoost Depth 3",
    two_stage_full: "Two-stage XGBoost (Full)", two_stage_compact: "Two-stage XGBoost (Compact)",
    dc: "Dixon–Coles",
  };
  const blend = model.blend;
  const stack = ucl && blend?.kind === "stack";
  const component = ucl ? names[blend?.component] || blend?.component || "Ensemble" : "XGBoost";
  setText("#model-context", `${competitionName(state.currentCompetition)} · ${t("data_until")} ${model.data_until}`);
  setText("#model-dc-description", t(ucl ? "ucl_dc" : "model_dc"));
  setText("#model-ml-name", stack ? "Stacking ensemble" : component);
  setText("#model-ml-description", t(ucl ? "ucl_ml" : "model_xgb"));
  setText("#model-pipeline-name", model.model_name);
  setText("#model-pipeline-description", t(ucl ? "ucl_pipeline" : "wc_pipeline"));
  const weight = ucl ? blend?.weight : 0.6;
  const hasWeights = !stack && Number.isFinite(weight);
  document.querySelector("#model-blend-track").hidden = !hasWeights;
  if (hasWeights) {
    const dcWeight = ucl && blend.component === "dc" ? 1 : 1 - weight;
    const mlWeight = 1 - dcWeight;
    const parts = [];
    if (dcWeight > 0) parts.push(`${percent(dcWeight)} Dixon–Coles`);
    if (mlWeight > 0) parts.push(`${percent(mlWeight)} ${component}`);
    setText("#model-blend-text", parts.join(" + "));
    setBar("#model-blend-track i", dcWeight);
    setBar("#model-blend-track b", mlWeight);
  } else {
    setText("#model-blend-text", stack ? "Stacking ensemble" : model.model_name);
  }
  setText("#model-selection-note", ucl
    ? `${t("calibration")}: ${blend?.calibration === "none" ? t("calibration_none") : blend?.calibration || "—"}. ${t("selection_note")}`
    : "");
}

function renderHeader(prediction) {
  const { home, away } = prediction.match;
  setText("#result-model-chip", `MATCHIQ · ${prediction.competition?.short_name || "V3"}`);
  setText("#result-home-name", home.name);
  setText("#result-away-name", away.name);
  const [homeScore = "0", awayScore = "0"] = String(prediction.headline.score).split("-");
  setText("#result-score-home", homeScore);
  setText("#result-score-away", awayScore);
  const exactScore = prediction.top_scores.find((item) => item.score === prediction.headline.score);
  setText("#result-score-probability", exactScore
    ? `${t("exact_score_probability")}: ${percent(exactScore.probability)}`
    : "");
  const scoreDisplay = document.querySelector("#result-score");
  if (scoreDisplay) {
    scoreDisplay.setAttribute(
      "aria-label",
      `${t("exact_score_label")}: ${homeScore}–${awayScore}`,
    );
  }

  let call;
  if (prediction.headline.outcome === "home") call = `${home.name} ${t("win_result")}`;
  else if (prediction.headline.outcome === "away") call = `${away.name} ${t("win_result")}`;
  else call = t("draw");
  setText("#result-outcome", `${call} (${percent(prediction.one_x_two[prediction.headline.outcome])})`);
  setText("#result-model-name", prediction.model.name);

  setText("#xg-home", number(prediction.expected_goals.home, 2));
  setText("#xg-away", number(prediction.expected_goals.away, 2));
  const clarity = prediction.headline.confidence;
  const clarityTier = clarity >= 0.35 ? "high" : clarity >= 0.12 ? "medium" : "low";
  setText("#confidence-value", `${percent(clarity)} · ${translatedTier(clarityTier)}`);
  setText("#data-quality", t(`data_${prediction.headline.data_quality}`));
}

function renderOutcomes(prediction) {
  const outcomes = prediction.one_x_two;
  setText("#outcome-home-name", prediction.match.home.name);
  setText("#outcome-away-name", prediction.match.away.name);
  setText("#outcome-home-value", percent(outcomes.home));
  setText("#outcome-draw-value", percent(outcomes.draw));
  setText("#outcome-away-value", percent(outcomes.away));
  requestAnimationFrame(() => {
    setBar("#outcome-home-bar", outcomes.home);
    setBar("#outcome-draw-bar", outcomes.draw);
    setBar("#outcome-away-bar", outcomes.away);
  });
}

function heatColor(probability, maximum) {
  const normalized = maximum > 0 ? probability / maximum : 0;
  const alpha = 0.07 + normalized * 0.82;
  const red = Math.round(70 + normalized * 65);
  const green = Math.round(85 - normalized * 30);
  const blue = Math.round(125 + normalized * 125);
  return `rgba(${red}, ${green}, ${blue}, ${alpha})`;
}

function renderHeatmap(prediction) {
  const container = document.querySelector("#score-heatmap");
  const matrix = prediction.score_matrix;
  const maximum = Math.max(...matrix.flat());
  container.replaceChildren();
  setText("#heatmap-detail", "");
  container.setAttribute("aria-label", t("score_map"));

  const corner = document.createElement("span");
  corner.className = "heatmap-axis";
  container.append(corner);
  for (let away = 0; away < matrix.length; away += 1) {
    const label = document.createElement("span");
    label.className = "heatmap-axis";
    label.textContent = away;
    container.append(label);
  }

  for (let home = matrix.length - 1; home >= 0; home -= 1) {
    const label = document.createElement("span");
    label.className = "heatmap-axis";
    label.textContent = home;
    container.append(label);
    for (let away = 0; away < matrix.length; away += 1) {
      const probability = matrix[home][away];
      const cell = document.createElement("button");
      cell.type = "button";
      cell.tabIndex = home === matrix.length - 1 && away === 0 ? 0 : -1;
      cell.className = "heatmap-cell";
      if (probability === maximum) cell.classList.add("best");
      cell.style.backgroundColor = heatColor(probability, maximum);
      cell.textContent = probability >= 0.008 ? number(probability * 100, 1) : "";
      cell.title = `${home}-${away}: ${percent(probability)}`;
      cell.setAttribute("aria-label", `${home}-${away}: ${percent(probability)}`);
      cell.addEventListener("focus", () => setText("#heatmap-detail", cell.title));
      cell.addEventListener("click", () => {
        container.querySelectorAll("button").forEach((node) => { node.tabIndex = node === cell ? 0 : -1; });
        setText("#heatmap-detail", cell.title);
      });
      cell.addEventListener("keydown", (event) => {
        const offsets = { ArrowLeft: -1, ArrowRight: 1, ArrowUp: -matrix.length, ArrowDown: matrix.length };
        if (!(event.key in offsets)) return;
        event.preventDefault();
        const cells = [...container.querySelectorAll("button")];
        const next = cells[Math.max(0, Math.min(cells.length - 1, cells.indexOf(cell) + offsets[event.key]))];
        cells.forEach((node) => { node.tabIndex = node === next ? 0 : -1; });
        next.focus();
      });
      container.append(cell);
    }
  }
}

function renderTopScores(prediction) {
  const rows = document.querySelector("#top-score-rows");
  rows.replaceChildren();
  prediction.top_scores.forEach((item, index) => {
    const row = document.createElement("div");
    row.className = "score-table-row";
    row.setAttribute("role", "row");
    [String(index + 1), item.score, percent(item.probability)].forEach((value) => {
      const cell = document.createElement("span");
      cell.setAttribute("role", "cell");
      cell.textContent = value;
      row.append(cell);
    });
    const tier = document.createElement("span");
    tier.setAttribute("role", "cell");
    tier.className = `tier ${item.confidence}`;
    tier.textContent = translatedTier(item.confidence);
    row.append(tier);
    rows.append(row);
  });
}

function renderGoals(prediction) {
  const btts = prediction.btts.yes;
  const donut = document.querySelector("#btts-donut");
  donut.style.background = `conic-gradient(var(--cyan) 0 ${btts * 100}%, #202020 ${btts * 100}% 100%)`;
  setText("#btts-value", percent(btts));
  setText("#btts-call", btts >= 0.5 ? t("yes") : t("no"));

  const chart = document.querySelector("#over-under-chart");
  chart.replaceChildren();
  prediction.over_under.forEach((item) => {
    const row = document.createElement("div");
    row.className = "ou-row";
    const label = document.createElement("span");
    label.textContent = `${t("over")} ${number(item.line, 1)}`;
    const track = document.createElement("div");
    track.className = "ou-track";
    const over = document.createElement("i");
    const under = document.createElement("b");
    over.style.width = `${item.over * 100}%`;
    under.style.width = `${item.under * 100}%`;
    track.append(over, under);
    const value = document.createElement("span");
    value.textContent = percent(item.over);
    row.setAttribute("aria-label", `${label.textContent}: ${percent(item.over)}; ${t("under")}: ${percent(item.under)}`);
    row.append(label, track, value);
    chart.append(row);
  });
}

function signed(value) {
  const numeric = Number(value);
  return numeric > 0 ? `+${numeric}` : String(numeric);
}

function renderExtended(prediction) {
  const { home, away, handicap } = prediction.match;
  const extended = prediction.extended;

  const homeQualify = extended.qualify.home;
  const qualifyTeam = homeQualify >= extended.qualify.away ? home.name : away.name;
  setText("#qualify-call", `${qualifyTeam} ${t("qualify")}`);
  setText("#qualify-detail", `${home.name} ${percent(homeQualify)} · ${away.name} ${percent(extended.qualify.away)}`);

  const homeCover = extended.handicap.home_cover;
  const awayCover = extended.handicap.away_cover;
  const coverTeam = homeCover >= awayCover ? home.name : away.name;
  setText("#handicap-call", `${coverTeam} ${t("cover")}`);
  let handicapDetail = `${home.name} ${signed(handicap)} ${percent(homeCover)} · ${away.name} ${percent(awayCover)}`;
  if (extended.handicap.push > 0.0001) handicapDetail += ` · ${t("push")} ${percent(extended.handicap.push)}`;
  setText("#handicap-detail", handicapDetail);

  const evenIsHigher = extended.odd_even.even >= extended.odd_even.odd;
  setText("#odd-even-call", evenIsHigher ? t("even") : t("odd"));
  setText("#odd-even-detail", `${t("odd")} ${percent(extended.odd_even.odd)} · ${t("even")} ${percent(extended.odd_even.even)}`);

  const resilience = extended.resilience;
  let resilienceCall = t("balanced");
  if (resilience.status === "home") resilienceCall = home.name;
  if (resilience.status === "away") resilienceCall = away.name;
  setText("#resilience-call", resilienceCall);
  setText("#resilience-detail", `${home.name} ${number(resilience.home, 1)}/10 · ${away.name} ${number(resilience.away, 1)}/10`);

  const dc = extended.double_chance;
  setText("#double-chance-values", `1X ${percent(dc["1x"])} · X2 ${percent(dc.x2)} · 12 ${percent(dc["12"])}`);
  setText("#win-to-nil-values", `${home.name} ${percent(extended.win_to_nil.home)} · ${away.name} ${percent(extended.win_to_nil.away)}`);
  const exact = extended.exact_goals.slice(0, 3).map((item) => `${item.goals} (${percent(item.probability)})`).join(" · ");
  setText("#exact-goals-values", exact);
}

function renderPrediction(prediction) {
  renderHeader(prediction);
  renderOutcomes(prediction);
  renderHeatmap(prediction);
  renderTopScores(prediction);
  renderGoals(prediction);
  renderExtended(prediction);
}

elements.form.addEventListener("submit", (event) => {
  event.preventDefault();
  requestPrediction({ scroll: true });
});

elements.swap.addEventListener("click", () => {
  const previousHome = elements.homeSelect.value;
  elements.homeSelect.value = elements.awaySelect.value;
  elements.awaySelect.value = previousHome;
  invalidatePrediction();
});

elements.homeSelect.addEventListener("change", invalidatePrediction);
elements.awaySelect.addEventListener("change", invalidatePrediction);
elements.handicap.addEventListener("change", invalidatePrediction);
elements.competition.addEventListener("change", () => {
  state.competitionId = elements.competition.value;
  state.currentCompetition = state.competitionMap.get(state.competitionId) || null;
  localStorage.setItem("matchiq-competition", state.competitionId);
  initialize();
});
elements.language.addEventListener("click", (event) => {
  const option = event.target.closest("[data-lang-option]");
  if (option) applyLanguage(option.dataset.langOption);
});

async function initialize() {
  if (state.loading) return;
  state.ready = false;
  state.model = null;
  state.teams = [];
  state.teamMap.clear();
  state.prediction = null;
  elements.result.hidden = true;
  elements.homeSelect.replaceChildren();
  elements.awaySelect.replaceChildren();
  state.feedback = "loading_data";
  clearError();
  setLoading(true);
  applyLanguage(state.language);
  try {
    await loadCompetitions();
    await loadTeams({ preserve: false });
    state.ready = true;
  } catch (error) {
    showError(error.message);
  } finally {
    state.feedback = null;
    renderFeedback();
    setLoading(false);
  }
  if (state.ready) await requestPrediction({ scroll: false });
}

initialize();
