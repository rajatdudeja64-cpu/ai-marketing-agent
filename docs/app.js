const MARKETING_STRATEGIES = [
  {
    name: "Morning Habit Acquisition",
    summary: "Win the daily milk search and turn it into a 7 AM subscription.",
    positioning:
      "Milkbasket is the default 7 AM milk run: a fresh pouch at the door before the day starts, on a subscription the household does not have to reorder.",
    target_persona:
      "Dual-income households in Delhi NCR apartments, ages 25-45, who still buy milk from a kirana or place a separate morning order.",
    offer: "First 7 days of milk delivery with free doorstep delivery. Cancel anytime.",
    tone: "Direct and practical",
    primary_channel: "Google Search",
    google_ads_share: 70,
    keyword_focus: "daily milk delivery, milk subscription near me, morning milk home delivery Delhi NCR",
    core_steps: [
      "Bid on high-intent milk delivery and milk subscription searches in Delhi NCR only.",
      "Send new subscribers a 7-day milk trial with a before-7 AM promise on the landing page.",
      "Retarget trial users on day 5 with a subscribe-and-save offer before the trial ends.",
    ],
  },
  {
    name: "Society Launch Density",
    summary: "Fill one apartment society at a time so the morning route pays for itself.",
    positioning:
      "Milkbasket wins building by building, so neighbors share one morning crate instead of ten separate milk runs.",
    target_persona:
      "Residents of large societies in Gurugram, Noida, and Dwarka who try a service after it shows up in the society WhatsApp group.",
    offer: "Society launch week: free bread with every milk order for the first 7 days, only for that society.",
    tone: "Local and neighborly",
    primary_channel: "Instagram and geo-tight Google Search",
    google_ads_share: 55,
    keyword_focus: "milk delivery in named Gurugram, Noida, and Dwarka societies and their pin codes",
    core_steps: [
      "Pick 10 high-rise societies and run pin-code search plus Instagram geo ads only there.",
      "Use a society-only bread add-on so the first order feels like a neighbor deal.",
      "After a successful 7 AM drop, ask the first subscribers to forward the launch note in the society group.",
    ],
  },
  {
    name: "Switch from Quick Commerce",
    summary: "Move people who reorder the same milk every morning onto a standing order.",
    positioning:
      "Stop paying a fresh delivery fee for the same milk every morning. Milkbasket is the standing order already downstairs before 7 AM.",
    target_persona:
      "People in Delhi NCR who reorder the same 500 ml or 1 L milk pouch on a quick-commerce app several mornings a week.",
    offer: "Price-lock the daily pouch for 30 days, delivery included, when they move the standing order to Milkbasket.",
    tone: "Sharp comparison, no competitor names in ad copy",
    primary_channel: "Google Search",
    google_ads_share: 80,
    keyword_focus: "daily milk delivery cost, milk subscription instead of ordering every day, morning milk home delivery",
    core_steps: [
      "Capture comparison and near-me searches from people already buying milk online.",
      "Landing page shows a 30-day pouch price against a typical per-order morning total with delivery fees.",
      "Block job, recipe, and wholesale searches so the budget stays on switchers.",
    ],
  },
  {
    name: "Basket Size and Retention",
    summary: "Keep milk subscribers and add bread, eggs, or fruit to tomorrow's crate.",
    positioning:
      "The milk order is already a habit. Bread, eggs, and fruit ride along so the household skips the evening kirana run.",
    target_persona:
      "Current Milkbasket subscribers, especially families with children, whose basket is only milk.",
    offer: "Add bread, eggs, or a fruit pouch to tomorrow's order and get that add-on free twice this week.",
    tone: "Helpful, like a household reminder",
    primary_channel: "Instagram, with brand search only",
    google_ads_share: 35,
    keyword_focus: "brand search and add-on terms such as bread with milk delivery and morning eggs home delivery",
    core_steps: [
      "Put most of the budget into Instagram and brand search, not cold generic milk terms.",
      "Show a real morning crate: milk plus the one breakfast item they still buy elsewhere.",
      "Judge the plan on add-on attach rate, not on new-customer volume.",
    ],
  },
  {
    name: "Freshness Trust Brand",
    summary: "Lead with a sealed pouch and an on-time crate, not a discount.",
    positioning:
      "Milk you can trust because it was packed for your door and arrives before 7 AM, not left in an open shop crate.",
    target_persona:
      "Health-conscious parents in Delhi NCR who worry about open milk, late delivery, and unfamiliar brands.",
    offer: "Tamper-evident pouch, a delivery window shown before signup, and a replacement if the crate is late.",
    tone: "Calm and trustworthy",
    primary_channel: "Instagram",
    google_ads_share: 40,
    keyword_focus: "fresh milk home delivery, hygienic milk delivery, farm pouch milk Delhi NCR",
    core_steps: [
      "Lead with delivery proof and pouch close-ups, not discount headlines.",
      "Run Instagram Reels of the morning drop, and Search only on freshness queries.",
      "Put the replacement promise in every ad description so trust is the offer.",
    ],
  },
];

const SAMPLE_LIVE_CAMPAIGNS = [
  {
    "Campaign ID": "24554585401",
    "Campaign Name": "Milkbasket - Morning Habit Acquisition - AI Search",
    Status: "PAUSED",
    Channel: "SEARCH",
    "Daily Budget": "466.67",
    "Impressions (30d)": 0,
    "Clicks (30d)": 0,
    "Cost (30d)": "0.00",
  },
  {
    "Campaign ID": "24554585112",
    "Campaign Name": "Delhi NCR - Brand Search Core",
    Status: "ENABLED",
    Channel: "SEARCH",
    "Daily Budget": "600.00",
    "Impressions (30d)": 18420,
    "Clicks (30d)": 1420,
    "Cost (30d)": "9,850.00",
  },
  {
    "Campaign ID": "24554584905",
    "Campaign Name": "Gurugram Societies - Breakfast Add-ons",
    Status: "ENABLED",
    Channel: "SEARCH",
    "Daily Budget": "350.00",
    "Impressions (30d)": 9310,
    "Clicks (30d)": 615,
    "Cost (30d)": "4,920.00",
  },
  {
    "Campaign ID": "24554584388",
    "Campaign Name": "Noida Morning Milk Trial - Legacy",
    Status: "PAUSED",
    Channel: "SEARCH",
    "Daily Budget": "400.00",
    "Impressions (30d)": 2140,
    "Clicks (30d)": 118,
    "Cost (30d)": "1,410.00",
  },
];

const LOG_STORAGE_KEY = "ai_marketing_agent_audit_log";
const state = {
  selectedStrategy: MARKETING_STRATEGIES[0].name,
  liveCampaigns: [],
  lastResult: null,
  lastBusiness: null,
};

const $ = (id) => document.getElementById(id);

function escapeHtml(str) {
  return String(str ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function loadAuditLog() {
  try {
    return JSON.parse(localStorage.getItem(LOG_STORAGE_KEY) || "[]");
  } catch {
    return [];
  }
}

function logActivity(action, details, status = "INFO") {
  const entries = loadAuditLog();
  entries.push({
    timestamp: new Date().toISOString(),
    status,
    action,
    details,
  });
  localStorage.setItem(LOG_STORAGE_KEY, JSON.stringify(entries.slice(-50)));
  renderAuditLog();
}

function renderAuditLog() {
  const entries = loadAuditLog().slice(-10).reverse();
  $("auditLogView").textContent = JSON.stringify(entries, null, 2);
}

function checkBudgetGuardrail(requestedMonthly, maxMonthly, maxDaily, emergencyStop) {
  if (emergencyStop) {
    logActivity("BUDGET_CHECK", { reason: "Emergency stop active" }, "BLOCKED");
    return [false, "BLOCKED: Emergency Stop is active. All campaign actions are paused."];
  }
  if (requestedMonthly <= 0) {
    return [false, "BLOCKED: Monthly budget must be greater than 0."];
  }
  if (requestedMonthly > maxMonthly) {
    const msg = `BLOCKED: Requested monthly budget (${requestedMonthly.toLocaleString()}) exceeds your hard limit (${maxMonthly.toLocaleString()}).`;
    logActivity("BUDGET_CHECK", { requested: requestedMonthly, max_monthly: maxMonthly }, "BLOCKED");
    return [false, msg];
  }
  const estimatedDaily = requestedMonthly / 30;
  if (estimatedDaily > maxDaily) {
    const msg = `BLOCKED: Estimated daily spend (${Math.round(estimatedDaily).toLocaleString()}/day) exceeds your daily cap (${maxDaily.toLocaleString()}/day).`;
    logActivity("BUDGET_CHECK", { estimated_daily: estimatedDaily, max_daily: maxDaily }, "BLOCKED");
    return [false, msg];
  }
  logActivity(
    "BUDGET_CHECK",
    { requested: requestedMonthly, estimated_daily: Number(estimatedDaily.toFixed(2)) },
    "APPROVED"
  );
  return [true, `PASSED: Budget within limits (~${Math.round(estimatedDaily).toLocaleString()}/day).`];
}

function validateLandingUrl(url) {
  const cleaned = String(url || "").trim();
  if (!cleaned) return [false, "BLOCKED: Landing Page URL is required."];
  try {
    const parsed = new URL(cleaned);
    if (!["http:", "https:"].includes(parsed.protocol) || !parsed.hostname) {
      return [false, "BLOCKED: Landing Page URL must start with http:// or https:// and include a valid domain."];
    }
    if (!parsed.hostname.includes(".") && parsed.hostname !== "localhost") {
      return [false, "BLOCKED: Landing Page URL must include a valid domain name (e.g., https://www.milkbasket.com)."];
    }
    return [true, cleaned];
  } catch {
    return [false, "BLOCKED: Landing Page URL must start with http:// or https:// and include a valid domain."];
  }
}

function validateGoogleAdsCopy(headlines, descriptions) {
  const issues = [];
  const uniqH = new Set();
  for (const h of headlines) {
    const t = String(h || "").trim();
    if (!t) {
      issues.push("Empty headline found.");
      continue;
    }
    uniqH.add(t);
    if (t.length > 30) issues.push(`Headline too long (${t.length}/30 chars): '${t}'`);
  }
  const uniqD = new Set();
  for (const d of descriptions) {
    const t = String(d || "").trim();
    if (!t) {
      issues.push("Empty description found.");
      continue;
    }
    uniqD.add(t);
    if (t.length > 90) issues.push(`Description too long (${t.length}/90 chars): '${t}'`);
  }
  if (uniqH.size < 3) issues.push(`Google Ads requires at least 3 unique headlines (found ${uniqH.size}).`);
  if (uniqD.size < 2) issues.push(`Google Ads requires at least 2 unique descriptions (found ${uniqD.size}).`);
  return issues;
}

function currentStrategyConfig() {
  return {
    name: state.selectedStrategy,
    positioning: $("cfgPositioning").value.trim(),
    target_persona: $("cfgPersona").value.trim(),
    offer: $("cfgOffer").value.trim(),
    tone: $("cfgTone").value.trim(),
    primary_channel: $("cfgChannel").value.trim(),
    google_ads_share: Number($("googleShare").value),
    keyword_focus: $("cfgKeywordFocus").value.trim(),
    core_steps: $("cfgSteps")
      .value.split("\n")
      .map((s) => s.trim())
      .filter(Boolean),
    agent_notes: $("cfgNotes").value.trim(),
    sample_limit: Math.max(5, Math.min(100, Number($("sampleLimit").value) || 50)),
  };
}

function applyPreset(name) {
  const preset = MARKETING_STRATEGIES.find((p) => p.name === name) || MARKETING_STRATEGIES[0];
  state.selectedStrategy = preset.name;
  $("strategySummary").textContent = preset.summary;
  $("googleShare").value = preset.google_ads_share;
  $("cfgPositioning").value = preset.positioning;
  $("cfgPersona").value = preset.target_persona;
  $("cfgOffer").value = preset.offer;
  $("cfgTone").value = preset.tone;
  $("cfgChannel").value = preset.primary_channel;
  $("cfgKeywordFocus").value = preset.keyword_focus;
  $("cfgSteps").value = preset.core_steps.join("\n");
  $("cfgNotes").value = "";
  renderStrategyRadios();
  updateBanner();
}

function renderStrategyRadios() {
  const wrap = $("strategyRadios");
  wrap.innerHTML = "";
  for (const preset of MARKETING_STRATEGIES) {
    const label = document.createElement("label");
    label.className = "radio-option" + (preset.name === state.selectedStrategy ? " selected" : "");
    const input = document.createElement("input");
    input.type = "radio";
    input.name = "strategy_choice";
    input.value = preset.name;
    input.checked = preset.name === state.selectedStrategy;
    input.addEventListener("change", () => applyPreset(preset.name));
    label.append(input, document.createTextNode(preset.name));
    wrap.append(label);
  }
}

function updateBanner() {
  const cfg = currentStrategyConfig();
  const igShare = 100 - cfg.google_ads_share;
  $("shareLabel").textContent = `${cfg.google_ads_share}%`;
  $("instagramShareCaption").textContent = `Instagram receives the other ${igShare}%. The agent cannot change this split.`;
  $("selectedStrategyBanner").innerHTML =
    `<strong>Selected strategy:</strong> ${escapeHtml(cfg.name)}<br>` +
    `<strong>Offer:</strong> ${escapeHtml(cfg.offer)}<br>` +
    `<strong>Channel:</strong> ${escapeHtml(cfg.primary_channel)}<br>` +
    `<strong>Budget split:</strong> ${cfg.google_ads_share}% Google Ads / ${igShare}% Instagram`;
  updateSampleCaption();
}

function updateSampleCaption() {
  const limit = Math.max(5, Math.min(100, Number($("sampleLimit").value) || 50));
  $("sampleCaption").textContent =
    `Sample size is ${limit}. ${state.liveCampaigns.length} campaigns are loaded. ` +
    `With "Send live campaign samples to the agent" on, the next workflow receives these rows.`;
}

function summarizeLiveCampaigns(rows, limit = 50) {
  if (!rows.length) return "";
  return rows.slice(0, Math.max(1, Math.min(limit, 100))).map((r) => {
    const imp = r["Impressions (30d)"] === "" || r["Impressions (30d)"] == null ? "n/a" : r["Impressions (30d)"];
    const clk = r["Clicks (30d)"] === "" || r["Clicks (30d)"] == null ? "n/a" : r["Clicks (30d)"];
    const cost = r["Cost (30d)"] === "" || r["Cost (30d)"] == null ? "n/a" : r["Cost (30d)"];
    return `- ${r["Campaign Name"]} | ${r.Status} | ${r.Channel} | daily budget ${r["Daily Budget"]} | 30d impressions ${imp} | clicks ${clk} | cost ${cost}`;
  }).join("\n");
}

async function askGeminiJson(apiKey, prompt) {
  const models = ["gemini-2.5-flash", "gemini-2.0-flash"];
  let lastError = null;
  for (const model of models) {
    try {
      const resp = await fetch(
        `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${encodeURIComponent(apiKey)}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            contents: [{ parts: [{ text: prompt }] }],
            generationConfig: { responseMimeType: "application/json" },
          }),
        }
      );
      if (!resp.ok) {
        lastError = new Error(`Gemini ${model} error (${resp.status}): ${await resp.text()}`);
        continue;
      }
      const data = await resp.json();
      const raw = data?.candidates?.[0]?.content?.parts?.[0]?.text || "";
      const cleaned = raw.replace(/^```(?:json)?\s*/i, "").replace(/```$/, "").trim();
      return JSON.parse(cleaned);
    } catch (err) {
      lastError = err;
    }
  }
  throw lastError || new Error("Gemini API request failed.");
}

function generateDemoOutput(business, cfg, googleBudget, instagramBudget) {
  const biz = business.name;
  const focusTerms = cfg.keyword_focus
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
  const seed = focusTerms[0] || "daily milk delivery";

  const strategy = {
    strategy_name: cfg.name,
    positioning: cfg.positioning,
    target_persona: cfg.target_persona,
    offer: cfg.offer,
    tone: cfg.tone,
    primary_channel: cfg.primary_channel,
    google_ads_monthly_budget: googleBudget,
    instagram_monthly_budget: instagramBudget,
    core_steps: cfg.core_steps.length ? cfg.core_steps.slice(0, 3) : [
      "Target high-intent search queries in core service areas.",
      "Highlight the core offer above the fold on the landing page.",
      "Review 30-day delivery metrics weekly and refine negative keywords.",
    ],
  };

  const research = {
    high_intent_keywords: [
      { keyword: seed, match_type: "Exact" },
      { keyword: `${biz.toLowerCase()} subscription`, match_type: "Exact" },
      { keyword: "morning milk delivery near me", match_type: "Phrase" },
      { keyword: "fresh milk home delivery", match_type: "Exact" },
      { keyword: "daily grocery subscription delhi ncr", match_type: "Phrase" },
      { keyword: "7 am doorstep milk delivery", match_type: "Phrase" },
      { keyword: "milk and bread morning delivery", match_type: "Phrase" },
      { keyword: "monthly milk delivery plan", match_type: "Exact" },
      { keyword: focusTerms[1] || "daily essentials delivery", match_type: "Phrase" },
      { keyword: focusTerms[2] || "pouch milk home delivery", match_type: "Phrase" },
    ],
    negative_keywords: [
      "dairy farm jobs",
      "milk recipes",
      "wholesale dairy distributor",
      "free milk scheme",
      "dairy machine price",
      "milk powder bulk",
      "delivery boy vacancy",
      "franchise cost",
    ],
    target_locations: ["Gurugram", "Noida", "Dwarka, New Delhi", "South Delhi", "Faridabad"],
    audience_interests: [
      "Online grocery shopping",
      "Family meal planning",
      "Organic & fresh food",
      "Working parents",
      "Gated community living",
      "Healthy breakfast habits",
    ],
  };

  const shortBiz = biz.slice(0, 14);
  const headlines = [
    `${shortBiz} Before 7 AM`,
    "Fresh Milk At Your Door",
    "Order By Midnight Daily",
    "Skip Morning Reorders",
    "Daily Milk Subscription",
    "7-Day Free Delivery Trial",
    "Sealed Fresh Milk Pouch",
    "Cancel Anytime Easily",
  ].map((h) => h.slice(0, 30));

  const descriptions = [
    `${cfg.offer}`.slice(0, 90),
    `Get fresh milk & daily essentials delivered before 7 AM with ${shortBiz}.`,
    `Designed for ${business.audience.slice(0, 42)}. Subscribe once, relax daily.`.slice(0, 90),
    `Tone: ${cfg.tone}. Reliable doorstep delivery without daily delivery fees.`.slice(0, 90),
  ];

  const content = {
    google_ads_headlines: headlines,
    google_ads_descriptions: descriptions,
    validation_issues: validateGoogleAdsCopy(headlines, descriptions),
    instagram_posts: [
      {
        format: "Reel",
        visual_idea: `6:45 AM doorstep crate drop showcasing ${biz} milk pouch, bread, and fresh eggs.`,
        caption: `${cfg.positioning} ${cfg.offer}`,
        hashtags: ["#MorningRoutine", "#DelhiNCR", "#FreshMilk", "#Before7AM", `#${biz.replace(/\s+/g, "")}`],
      },
      {
        format: "Carousel",
        visual_idea: "3-slide breakdown: Order by midnight -> Packed fresh -> Delivered silently by 7 AM.",
        caption: `Stop scrambling every morning. ${cfg.offer}`,
        hashtags: ["#DailyEssentials", "#SmartHouseholds", "#Subscription", "#DoorstepDelivery", "#GroceryHack"],
      },
      {
        format: "Single Image",
        visual_idea: "Clean breakfast table shot highlighting the strategy's core promise and delivery window.",
        caption: `Built for ${cfg.target_persona}. Try ${biz} tomorrow morning.`,
        hashtags: ["#BreakfastTime", "#FamilyFirst", "#FreshDaily", "#Gurugram", "#Noida"],
      },
    ],
  };

  return { strategy, research, content };
}

async function runWorkflow(business, cfg) {
  const maxMonthly = Number($("maxMonthly").value);
  const maxDaily = Number($("maxDaily").value);
  const emergencyStop = $("emergencyStop").checked;

  const statusBox = $("statusBox");
  const statusTitle = $("statusTitle");
  const statusSteps = $("statusSteps");
  statusBox.classList.remove("hidden");
  statusTitle.textContent = "Running AI Marketing Agents...";
  statusSteps.innerHTML = "";
  const pushStep = (msg) => {
    const li = document.createElement("li");
    li.textContent = msg;
    statusSteps.append(li);
  };

  pushStep("1/4 Checking budget limits & safety guardrails...");
  const [allowed, guardrailMsg] = checkBudgetGuardrail(business.monthly_budget, maxMonthly, maxDaily, emergencyStop);
  if (!allowed) {
    statusTitle.textContent = "Blocked by Safety Guardrails";
    return { blocked: true, guardrail_message: guardrailMsg };
  }

  const liveRows = $("includeLiveSamples").checked ? state.liveCampaigns.slice(0, cfg.sample_limit) : [];
  const liveContext = summarizeLiveCampaigns(liveRows, cfg.sample_limit);
  const share = Math.max(0, Math.min(cfg.google_ads_share, 100)) / 100;
  const googleBudget = Number((business.monthly_budget * share).toFixed(2));
  const instagramBudget = Number((business.monthly_budget - googleBudget).toFixed(2));

  const apiKey = $("geminiKey").value.trim();

  if (!apiKey) {
    pushStep(`2/4 Strategy Agent is applying "${cfg.name}" (Demo Mode)...`);
    await new Promise((r) => setTimeout(r, 180));
    pushStep("3/4 Research Agent is finding high-intent keywords & audiences (Demo Mode)...");
    await new Promise((r) => setTimeout(r, 180));
    pushStep("4/4 Content Agent is writing & validating Google Ads + Instagram copy (Demo Mode)...");
    await new Promise((r) => setTimeout(r, 180));
    const demo = generateDemoOutput(business, cfg, googleBudget, instagramBudget);
    logActivity("STRATEGY_AGENT", { business: business.name, strategy: cfg.name, mode: "demo" }, "COMPLETED");
    logActivity("RESEARCH_AGENT", { business: business.name, strategy: cfg.name, keywords: demo.research.high_intent_keywords.length, mode: "demo" }, "COMPLETED");
    logActivity("CONTENT_AGENT", { business: business.name, strategy: cfg.name, validation_issues: demo.content.validation_issues.length, mode: "demo" }, "COMPLETED");
    logActivity("WORKFLOW_COMPLETE", { business: business.name, strategy: cfg.name, mode: "demo" }, "AWAITING_APPROVAL");
    statusTitle.textContent = "All 3 Agents Finished (Demo Mode) — Ready for Approval";
    return { blocked: false, guardrail_message: guardrailMsg, ...demo };
  }

  pushStep(`2/4 Strategy Agent is applying "${cfg.name}" via Gemini...`);
  const strategy = await askGeminiJson(
    apiKey,
    `You are the Strategy Agent. Keep the selected strategy. Return ONLY valid JSON with keys: strategy_name, positioning, target_persona, offer, tone, primary_channel, google_ads_monthly_budget (${googleBudget}), instagram_monthly_budget (${instagramBudget}), core_steps (array of 3 strings).\nConfig: ${JSON.stringify(cfg)}\nBusiness: ${JSON.stringify(business)}\nLive campaigns:\n${liveContext || "None"}`
  );
  strategy.strategy_name = cfg.name;
  strategy.google_ads_monthly_budget = googleBudget;
  strategy.instagram_monthly_budget = instagramBudget;
  logActivity("STRATEGY_AGENT", { business: business.name, strategy: cfg.name, mode: "gemini" }, "COMPLETED");

  pushStep("3/4 Research Agent is finding high-intent keywords & audiences via Gemini...");
  const research = await askGeminiJson(
    apiKey,
    `You are the Research Agent. Return ONLY valid JSON with keys: high_intent_keywords (list of 10 {keyword, match_type} where match_type is Exact or Phrase), negative_keywords (8 strings), target_locations (5 strings), audience_interests (6 strings).\nBusiness: ${JSON.stringify(business)}\nStrategy: ${JSON.stringify(strategy)}\nLive campaigns:\n${liveContext || "None"}`
  );
  logActivity("RESEARCH_AGENT", { business: business.name, strategy: cfg.name, keywords: (research.high_intent_keywords || []).length, mode: "gemini" }, "COMPLETED");

  pushStep("4/4 Content Agent is writing & validating Google Ads + Instagram copy via Gemini...");
  const content = await askGeminiJson(
    apiKey,
    `You are the Content Agent. Return ONLY valid JSON with keys: google_ads_headlines (8 strings <=30 chars each), google_ads_descriptions (4 strings <=90 chars each), instagram_posts (3 objects with format, visual_idea, caption, hashtags array).\nBusiness: ${JSON.stringify(business)}\nStrategy: ${JSON.stringify(strategy)}\nKeywords: ${JSON.stringify((research.high_intent_keywords || []).slice(0, 8))}`
  );
  content.validation_issues = validateGoogleAdsCopy(content.google_ads_headlines || [], content.google_ads_descriptions || []);
  logActivity("CONTENT_AGENT", { business: business.name, strategy: cfg.name, validation_issues: content.validation_issues.length, mode: "gemini" }, "COMPLETED");
  logActivity("WORKFLOW_COMPLETE", { business: business.name, strategy: cfg.name, mode: "gemini" }, "AWAITING_APPROVAL");
  statusTitle.textContent = "All 3 Agents Finished — Ready for Approval";
  return { blocked: false, guardrail_message: guardrailMsg, strategy, research, content };
}

function renderResults(result, business) {
  const banner = $("guardrailResult");
  banner.classList.remove("hidden", "alert-success", "alert-error");
  if (result.blocked) {
    banner.classList.add("alert-error");
    banner.textContent = result.guardrail_message;
    $("resultsSection").classList.add("hidden");
    return;
  }

  banner.classList.add("alert-success");
  banner.textContent = result.guardrail_message;
  $("resultsSection").classList.remove("hidden");

  const cur = business.currency;
  const { strategy, research, content } = result;

  $("tab1").innerHTML = `
    <h3>${escapeHtml(strategy.strategy_name || "Positioning & Target Persona")}</h3>
    <p><strong>Positioning:</strong> ${escapeHtml(strategy.positioning)}</p>
    <p><strong>Ideal Buyer:</strong> ${escapeHtml(strategy.target_persona)}</p>
    <p><strong>Offer:</strong> ${escapeHtml(strategy.offer || "")}</p>
    <p><strong>Tone:</strong> ${escapeHtml(strategy.tone || "")} · <strong>Channel:</strong> ${escapeHtml(strategy.primary_channel || "")}</p>
    <div class="metrics-grid">
      <div class="metric-card"><div class="metric-label">Google Ads Monthly Budget</div><div class="metric-value">${escapeHtml(cur)} ${Number(strategy.google_ads_monthly_budget).toLocaleString()}</div></div>
      <div class="metric-card"><div class="metric-label">Instagram Monthly Budget</div><div class="metric-value">${escapeHtml(cur)} ${Number(strategy.instagram_monthly_budget).toLocaleString()}</div></div>
    </div>
    <h4>Core Action Steps</h4>
    <ol>${(strategy.core_steps || []).map((s) => `<li>${escapeHtml(s)}</li>`).join("")}</ol>
  `;

  $("tab2").innerHTML = `
    <h3>High-Intent Google Ads Keywords</h3>
    <div class="table-wrap">
      <table>
        <thead><tr><th>Keyword</th><th>Match Type</th></tr></thead>
        <tbody>
          ${(research.high_intent_keywords || [])
            .map((k) => `<tr><td>${escapeHtml(k.keyword)}</td><td>${escapeHtml(k.match_type)}</td></tr>`)
            .join("")}
        </tbody>
      </table>
    </div>
    <div class="three-col">
      <div><strong>Negative Keywords (Blocked)</strong><ul>${(research.negative_keywords || []).map((k) => `<li>${escapeHtml(k)}</li>`).join("")}</ul></div>
      <div><strong>Target Locations</strong><ul>${(research.target_locations || []).map((k) => `<li>${escapeHtml(k)}</li>`).join("")}</ul></div>
      <div><strong>Instagram Interests</strong><ul>${(research.audience_interests || []).map((k) => `<li>${escapeHtml(k)}</li>`).join("")}</ul></div>
    </div>
  `;

  const issues = content.validation_issues || [];
  const issueBanner = issues.length
    ? `<div class="alert alert-warn"><strong>Guardrail Warnings:</strong><ul>${issues.map((i) => `<li>${escapeHtml(i)}</li>`).join("")}</ul></div>`
    : `<div class="alert alert-success">All Google Ads headlines (≤30 chars), descriptions (≤90 chars), and minimum RSA counts passed validation!</div>`;

  $("tab3").innerHTML = `
    ${issueBanner}
    <h3>Google Ads Headlines</h3>
    <ul>${(content.google_ads_headlines || [])
      .map((h) => `<li>${escapeHtml(h)} <span class="char-badge ${h.length > 30 ? "over" : ""}">(${h.length}/30 chars)</span></li>`)
      .join("")}</ul>
    <h3>Google Ads Descriptions</h3>
    <ul>${(content.google_ads_descriptions || [])
      .map((d) => `<li>${escapeHtml(d)} <span class="char-badge ${d.length > 90 ? "over" : ""}">(${d.length}/90 chars)</span></li>`)
      .join("")}</ul>
    <h3>Instagram Content Plan</h3>
    ${(content.instagram_posts || [])
      .map(
        (p, idx) => `
      <div class="post-card">
        <strong>Post ${idx + 1}: ${escapeHtml(p.format || "Post")}</strong>
        <p><strong>Visual Idea:</strong> ${escapeHtml(p.visual_idea || "")}</p>
        <p><strong>Caption:</strong> ${escapeHtml(p.caption || "")}</p>
        <p><strong>Hashtags:</strong> ${escapeHtml((p.hashtags || []).join(" "))}</p>
      </div>`
      )
      .join("")}
  `;

  const gadsMonthly = Number(strategy.google_ads_monthly_budget);
  const dailyPreview = gadsMonthly > 0 ? Math.max(1, Number((gadsMonthly / 30).toFixed(2))) : 0;
  const campName = strategy.strategy_name
    ? `${business.name} - ${strategy.strategy_name} - AI Search`
    : `${business.name} - AI Search`;
  const posCount = (research.high_intent_keywords || []).length;
  const negCount = (research.negative_keywords || []).length;

  $("tab4").innerHTML = `
    <h3>Google Ads Campaign Preview &amp; Approval Gate</h3>
    <div class="alert alert-info">
      <strong>Campaign Name:</strong> ${escapeHtml(campName)}<br>
      <strong>Target Account:</strong> ${escapeHtml($("customerId").value)} (Test Sandbox)<br>
      <strong>Daily Budget:</strong> ${escapeHtml(cur)} ${dailyPreview.toLocaleString()}/day<br>
      <strong>Keywords:</strong> ${posCount} positive · ${negCount} negative<br>
      <strong>Initial Status:</strong> PAUSED (safe — no ads will serve automatically)
    </div>
    <label class="field">
      <span>Landing Page URL (required by Google Ads)</span>
      <input type="text" id="finalUrlInput" value="https://www.milkbasket.com" />
    </label>
    <button type="button" id="launchBtn" class="btn-primary" ${$("emergencyStop").checked ? "disabled" : ""}>
      Approve &amp; Simulate PAUSED Campaign Launch (Static Demo)
    </button>
    <div id="launchOutput" class="alert hidden" style="margin-top: 12px;"></div>
  `;

  $("launchBtn").addEventListener("click", () => {
    const out = $("launchOutput");
    out.classList.remove("hidden", "alert-success", "alert-error");
    const [okBudget, budgetMsg] = checkBudgetGuardrail(
      gadsMonthly,
      Number($("maxMonthly").value),
      Number($("maxDaily").value),
      $("emergencyStop").checked
    );
    if (!okBudget) {
      out.classList.add("alert-error");
      out.textContent = budgetMsg;
      return;
    }
    const [okUrl, urlOrErr] = validateLandingUrl($("finalUrlInput").value);
    if (!okUrl) {
      out.classList.add("alert-error");
      out.textContent = urlOrErr;
      return;
    }
    const fakeId = Math.floor(24554600000 + Math.random() * 90000);
    const resource = `customers/${$("customerId").value.replaceAll("-", "")}/campaigns/${fakeId}`;
    logActivity("HUMAN_APPROVAL", { business: business.name, daily_budget: dailyPreview, strategy: strategy.strategy_name }, "APPROVED");
    logActivity(
      "GOOGLE_ADS_SIMULATED_CAMPAIGN_CREATED",
      {
        business: business.name,
        strategy: strategy.strategy_name,
        campaign_resource: resource,
        keywords_added: posCount,
        negative_keywords_added: negCount,
        final_url: urlOrErr,
        daily_budget: dailyPreview,
        status: "PAUSED",
      },
      "SIMULATED"
    );
    state.liveCampaigns.unshift({
      "Campaign ID": String(fakeId),
      "Campaign Name": campName,
      Status: "PAUSED",
      Channel: "SEARCH",
      "Daily Budget": dailyPreview.toFixed(2),
      "Impressions (30d)": 0,
      "Clicks (30d)": 0,
      "Cost (30d)": "0.00",
    });
    renderCampaignsTable();
    out.classList.add("alert-success");
    out.textContent = `Simulated PAUSED campaign created with Ad Group, ${posCount} keywords, ${negCount} negative keywords, and Responsive Search Ad! Resource: ${resource}`;
  });
}

function renderCampaignsTable() {
  updateSampleCaption();
  const wrap = $("campaignsTableWrap");
  if (!state.liveCampaigns.length) {
    wrap.innerHTML = `<p class="muted">No campaigns loaded yet. Click "Refresh Live Campaigns" to load the sample dataset.</p>`;
    return;
  }
  const cols = Object.keys(state.liveCampaigns[0]);
  wrap.innerHTML = `
    <table>
      <thead><tr>${cols.map((c) => `<th>${escapeHtml(c)}</th>`).join("")}</tr></thead>
      <tbody>
        ${state.liveCampaigns
          .map((row) => `<tr>${cols.map((c) => `<td>${escapeHtml(row[c])}</td>`).join("")}</tr>`)
          .join("")}
      </tbody>
    </table>
  `;
}

function init() {
  applyPreset(MARKETING_STRATEGIES[0].name);
  renderAuditLog();
  renderCampaignsTable();

  $("emergencyStop").addEventListener("change", (e) => {
    $("emergencyBanner").classList.toggle("hidden", !e.target.checked);
    const launchBtn = $("launchBtn");
    if (launchBtn) launchBtn.disabled = e.target.checked;
  });

  ["googleShare", "cfgOffer", "cfgChannel", "sampleLimit"].forEach((id) => {
    $(id).addEventListener("input", updateBanner);
  });

  document.querySelectorAll(".tab").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
      document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
      btn.classList.add("active");
      $(btn.dataset.tab).classList.add("active");
    });
  });

  $("refreshCampaignsBtn").addEventListener("click", () => {
    const limit = Math.max(5, Math.min(100, Number($("sampleLimit").value) || 50));
    state.liveCampaigns = SAMPLE_LIVE_CAMPAIGNS.slice(0, limit).map((r) => ({ ...r }));
    renderCampaignsTable();
  });

  $("clearLogBtn").addEventListener("click", () => {
    localStorage.removeItem(LOG_STORAGE_KEY);
    renderAuditLog();
  });

  $("businessForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const name = $("bizName").value.trim();
    const product = $("bizProduct").value.trim();
    if (!name || !product) return;

    const business = {
      name,
      product,
      audience: $("bizAudience").value.trim(),
      goal: $("bizGoal").value,
      monthly_budget: Number($("bizBudget").value),
      currency: $("bizCurrency").value,
    };
    const cfg = currentStrategyConfig();
    $("runBtn").disabled = true;
    try {
      const result = await runWorkflow(business, cfg);
      state.lastResult = result;
      state.lastBusiness = business;
      renderResults(result, business);
    } catch (err) {
      const banner = $("guardrailResult");
      banner.classList.remove("hidden", "alert-success");
      banner.classList.add("alert-error");
      banner.textContent = `Something went wrong: ${err.message}`;
    } finally {
      $("runBtn").disabled = false;
    }
  });
}

init();
