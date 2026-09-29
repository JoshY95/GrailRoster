const GUEST_STORAGE_KEY = "grailroster.collection.v1";
const USER_STORAGE_PREFIX = "grailroster.collection.user";
const LEGACY_GUEST_STORAGE_KEY = "ringvault.collection.v1";
const LEGACY_USER_STORAGE_PREFIX = "ringvault.collection.user";
const PAGE_SIZE = 100;
const API_PAGE_SIZE = 1000;
let authMode = "sign-in";

const state = {
  catalogue: null,
  images: { cards: {}, sets: {} },
  collection: loadCollection(),
  supabase: null,
  user: null,
  syncing: false,
  view: "dashboard",
  query: "",
  setId: "all",
  category: "all",
  status: "all",
  visibleCards: PAGE_SIZE,
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

function collectionStorageKey(userId = state?.user?.id) {
  return userId ? `${USER_STORAGE_PREFIX}.${userId}.v1` : GUEST_STORAGE_KEY;
}

function legacyStorageKeyFor(storageKey) {
  if (storageKey === GUEST_STORAGE_KEY) return LEGACY_GUEST_STORAGE_KEY;
  if (storageKey.startsWith(`${USER_STORAGE_PREFIX}.`)) return storageKey.replace(USER_STORAGE_PREFIX, LEGACY_USER_STORAGE_PREFIX);
  return null;
}

function loadCollection(storageKey = GUEST_STORAGE_KEY) {
  try {
    const legacyStorageKey = legacyStorageKeyFor(storageKey);
    const storedCollection = localStorage.getItem(storageKey);
    const legacyCollection = storedCollection === null && legacyStorageKey ? localStorage.getItem(legacyStorageKey) : null;
    const collection = JSON.parse(storedCollection ?? legacyCollection) || {};
    if (storedCollection === null && legacyCollection !== null) localStorage.setItem(storageKey, legacyCollection);
    return Object.fromEntries(Object.entries(collection).filter(([, item]) => ["owned", "wanted", "missing"].includes(item?.status)));
  } catch { return {}; }
}

function saveCollection() {
  localStorage.setItem(collectionStorageKey(), JSON.stringify(state.collection));
}

function mergeLocalCollections(primary, incoming) {
  const merged = { ...primary };
  for (const [cardId, entry] of Object.entries(incoming)) {
    if (!merged[cardId] || new Date(entry.updatedAt || 0) > new Date(merged[cardId].updatedAt || 0)) merged[cardId] = entry;
  }
  return merged;
}

function migrateLegacyCollectionIds() {
  const replacements = [
    ["2025-WMCJ-CCA-", "2025-TCWWE-CJWM-CCA-"],
    ["2025-WMCJ-CJA-", "2025-TCWWE-CJWM-AUTO-"],
  ];
  const validCardIds = new Set((state.catalogue?.cards || []).map((card) => card.id));
  let changed = false;
  for (const [oldId, entry] of Object.entries({ ...state.collection })) {
    // Never migrate a current canonical ID. This prevents similarly named sets
    // from sharing collection state when a historical prefix is reused.
    if (validCardIds.has(oldId)) continue;
    const replacement = replacements.find(([prefix]) => oldId.startsWith(prefix));
    if (!replacement) continue;
    const newId = replacement[1] + oldId.slice(replacement[0].length);
    if (!validCardIds.has(newId)) continue;
    if (!state.collection[newId] || new Date(entry.updatedAt || 0) > new Date(state.collection[newId].updatedAt || 0)) state.collection[newId] = entry;
    delete state.collection[oldId];
    changed = true;
  }
  if (changed) saveCollection();
}

function entryFor(cardId) { return state.collection[cardId] || null; }
function statusFor(cardId) { return entryFor(cardId)?.status || "missing"; }

async function setStatus(cardId, nextStatus) {
  const current = statusFor(cardId);
  state.collection[cardId] = {
    ...(entryFor(cardId) || {}),
    status: current === nextStatus ? "missing" : nextStatus,
    updatedAt: new Date().toISOString(),
  };
  saveCollection();
  renderAll();
  if (state.user) {
    updateSyncStatus("syncing", "Saving change…");
    try {
      await syncCard(cardId);
      updateSyncStatus("cloud", "Synced to your account");
    } catch (error) {
      updateSyncStatus("pending", "Saved here · sync pending");
      console.error(error);
    }
  }
  showToast(current === nextStatus ? "Card removed from your list" : nextStatus === "owned" ? "Added to your collection" : "Added to your wanted list");
}

function counts() {
  const cards = state.catalogue?.cards || [];
  return {
    owned: cards.filter((card) => statusFor(card.id) === "owned").length,
    wanted: cards.filter((card) => statusFor(card.id) === "wanted").length,
  };
}

function setOwnedCount(setId) {
  return state.catalogue.cards.filter((card) => card.setId === setId && statusFor(card.id) === "owned").length;
}

function formatPercentage(value, total) {
  if (!total || value <= 0) return "0%";
  if (value >= total) return "100%";
  return `${((value / total) * 100).toFixed(2)}%`;
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>'"]/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" })[character]);
}

function safeUrl(value, allowRelative = true) {
  if (!value) return "";
  try {
    const url = new URL(value, location.href);
    if (!["http:", "https:"].includes(url.protocol)) return "";
    if (!allowRelative && url.origin === location.origin && !/^https?:/i.test(value)) return "";
    return url.href;
  } catch { return ""; }
}

function approvedImage(entry) { return entry?.rightsStatus === "approved" ? entry : null; }
function cardImage(cardId) { return approvedImage(state.images.cards?.[cardId]); }
function setImage(setId) { return approvedImage(state.images.sets?.[setId]); }
function initials(value) { return String(value || "GR").split(/\s+/).filter(Boolean).slice(0, 2).map((part) => part[0]).join("").toUpperCase(); }

function imageMarkup(entry, alt, fallback, className = "", placeholder = "") {
  const source = safeUrl(entry?.thumbnail || entry?.front || entry?.image);
  return `<div class="image-frame ${className} ${source ? "has-image" : ""}">
    ${placeholder || `<span class="image-fallback" aria-hidden="true">${escapeHtml(fallback)}</span>`}
    ${source ? `<img src="${escapeHtml(source)}" alt="${escapeHtml(alt)}" loading="lazy" decoding="async" onerror="this.parentElement.classList.remove('has-image');this.remove()" />` : ""}
  </div>`;
}

function setCard(set) {
  const owned = setOwnedCount(set.id);
  const progress = set.cardCount ? (owned / set.cardCount) * 100 : 0;
  const progressLabel = formatPercentage(owned, set.cardCount);
  const approved = setImage(set.id);
  return `<article class="set-card" role="button" tabindex="0" aria-label="Open ${escapeHtml(set.shortName)} checklist" data-set-id="${escapeHtml(set.id)}">
    <div class="set-visual" aria-hidden="true">
      ${imageMarkup(approved, "", "", "set-cover", GrailUI.setCover(set))}
    </div>
    <div class="set-card-body">
      <span class="set-year">${set.year} · ${escapeHtml(set.manufacturer)}</span>
      <h3>${escapeHtml(set.shortName)}</h3>
      <div class="set-meta">${set.cardCount.toLocaleString()} cards · ${set.subsetCount} subsets</div>
      <div class="progress-track" role="progressbar" aria-label="Set collected" aria-valuenow="${owned}" aria-valuemin="0" aria-valuemax="${set.cardCount}"><div class="progress-fill" style="--progress:${progress}%"></div></div>
      <div class="progress-label"><span>${owned.toLocaleString()} collected</span><strong>${progressLabel}</strong></div>
    </div>
  </article>`;
}

function renderStats() {
  const { owned, wanted } = counts();
  const completion = formatPercentage(owned, state.catalogue.cardCount);
  $("#heroProgress").innerHTML = `<strong>${completion}</strong><span>of the catalogue collected</span>`;
  $("#stats").innerHTML = [
    ["Cards owned", owned.toLocaleString(), `${completion} of catalogued cards`],
    ["Wanted cards", wanted.toLocaleString(), "Your active chase list"],
    ["Completed sets", state.catalogue.sets.filter((set) => setOwnedCount(set.id) === set.cardCount).length, `of ${state.catalogue.setCount} available`],
    ["Cards catalogued", state.catalogue.cardCount.toLocaleString(), "Verified master identities"],
  ].map(([label, value, note]) => `<div class="stat-card"><p>${label}</p><strong>${value}</strong><small>${note}</small></div>`).join("");
}

function renderSets() {
  const cards = state.catalogue.sets.map(setCard).join("");
  $("#dashboardSets").innerHTML = cards;
  const query = $("#setSearch").value.trim().toLocaleLowerCase();
  const collecting = $("#setOwnership").value === "collecting";
  const sets = state.catalogue.sets.filter(set => (!query || `${set.name} ${set.year}`.toLocaleLowerCase().includes(query)) && (!collecting || setOwnedCount(set.id) > 0));
  $("#setLibraryCount").textContent = `${sets.length} of ${state.catalogue.sets.length} WWE sets`;
  $("#allSets").innerHTML = sets.length ? sets.map(setCard).join("") : emptyState("No sets found", collecting ? "Mark a card as Owned to start collecting a set." : "Try another set name or year.");
}

function renderRecent() {
  const recent = state.catalogue.cards.filter((card) => statusFor(card.id) === "owned")
    .sort((a, b) => new Date(entryFor(b.id)?.updatedAt || 0) - new Date(entryFor(a.id)?.updatedAt || 0))
    .slice(0, 6);
  $("#dashboardRecent").innerHTML = recent.length ? recent.map((card) => `<button class="recent-card" data-open-card="${escapeHtml(card.id)}" aria-label="View ${escapeHtml(card.name)}">
    ${imageMarkup(cardImage(card.id), `${card.name} card`, initials(card.name), "recent-image", GrailUI.cardPlaceholder(card, state.catalogue.sets.find(set => set.id === card.setId)))}
    <span class="recent-name">${escapeHtml(card.name)}</span><span class="recent-number">#${escapeHtml(card.number)} · ${escapeHtml(card.subset)}</span>
    <span class="recent-owned">✓ Owned</span>
  </button>`).join("") : emptyState("Your collection starts here", "Mark a card as Owned and it will appear in your vault.");
}

function filteredCards(collectionOnly = false) {
  const query = state.query.trim().toLocaleLowerCase();
  return state.catalogue.cards.filter((card) => {
    if (collectionOnly && statusFor(card.id) !== "owned") return false;
    if (state.setId !== "all" && card.setId !== state.setId) return false;
    if (state.category !== "all" && card.category !== state.category) return false;
    if (state.status !== "all" && statusFor(card.id) !== state.status) return false;
    if (!query) return true;
    return [card.name, card.subject2, card.number, card.subset, card.subsetCode, card.roster].filter(Boolean).some((value) => String(value).toLocaleLowerCase().includes(query));
  });
}

function cardRow(card) {
  const set = state.catalogue.sets.find((item) => item.id === card.setId);
  const status = statusFor(card.id);
  return `<article class="card-row">
    <button class="card-image-button" data-open-card="${escapeHtml(card.id)}" aria-label="View ${escapeHtml(card.name)}">
      ${imageMarkup(cardImage(card.id), `${card.name} card`, initials(card.name), "card-thumbnail", GrailUI.cardPlaceholder(card, set))}
    </button>
    <div class="card-number">#${escapeHtml(card.number)}</div>
    <button class="card-name card-name-button" data-open-card="${escapeHtml(card.id)}">${escapeHtml(card.name)}<small>${escapeHtml(card.subset)}${card.rookie === "Yes" ? " · Rookie" : ""}</small></button>
    <div class="card-set">${escapeHtml(set.shortName)}<small>${escapeHtml(card.roster || "WWE")}</small></div>
    <span class="category-pill">${escapeHtml(card.category)}</span>
    <div class="card-actions">
      <button class="state-button owned ${status === "owned" ? "active" : ""}" aria-pressed="${status === "owned"}" data-card-id="${card.id}" data-status="owned">${status === "owned" ? "✓ " : ""}Owned</button>
      <button class="state-button wanted ${status === "wanted" ? "active" : ""}" aria-pressed="${status === "wanted"}" data-card-id="${card.id}" data-status="wanted">Wanted</button>
    </div>
  </article>`;
}

function openCard(cardId) {
  const card = state.catalogue.cards.find((item) => item.id === cardId);
  if (!card) return;
  const set = state.catalogue.sets.find((item) => item.id === card.setId);
  const entry = cardImage(card.id);
  const front = safeUrl(entry?.front || entry?.image || entry?.thumbnail);
  const back = safeUrl(entry?.back);
  const source = safeUrl(entry?.sourceUrl, false);
  const collectionEntry = entryFor(card.id) || {};
  const selected = (value, current) => value === current ? " selected" : "";
  $("#cardDialogContent").innerHTML = `<div class="dialog-grid">
    <div class="dialog-images">
      ${imageMarkup(front ? { front, rightsStatus: "approved" } : null, `${card.name} front`, initials(card.name), "card-preview", GrailUI.cardPlaceholder(card, set))}
      ${back ? imageMarkup({ front: back, rightsStatus: "approved" }, `${card.name} back`, "BACK", "card-preview") : ""}
    </div>
    <div class="dialog-details">
      <p class="eyebrow">${escapeHtml(set.shortName)}</p><h2>${escapeHtml(card.name)}</h2>
      <dl>
        <div><dt>Card number</dt><dd>${escapeHtml(card.number)}</dd></div>
        <div><dt>Subset</dt><dd>${escapeHtml(card.subset)}</dd></div>
        <div><dt>Category</dt><dd>${escapeHtml(card.category)}</dd></div>
        <div><dt>Year</dt><dd>${escapeHtml(set.year)}</dd></div>
      </dl>
      <p class="image-status ${entry ? "approved" : "pending"}">${entry ? "Approved reference image" : "Reference image not yet added"}</p>
      ${entry?.photographerCredit ? `<p class="image-credit">Image: ${escapeHtml(entry.photographerCredit)}</p>` : ""}
      ${source ? `<a class="source-link" href="${escapeHtml(source)}" target="_blank" rel="noopener noreferrer">View image source</a>` : ""}
      <form class="collection-details-form" id="collectionDetailsForm" data-card-id="${escapeHtml(card.id)}">
        <div class="collection-form-heading"><strong>Collection details</strong><small>${state.user ? "Synced to your account" : "Saved on this device"}</small></div>
        <div class="form-grid">
          <label>Status<select name="status">
            <option value="missing"${selected("missing", collectionEntry.status || "missing")}>Missing</option>
            <option value="owned"${selected("owned", collectionEntry.status)}>Owned</option>
            <option value="wanted"${selected("wanted", collectionEntry.status)}>Wanted</option>
          </select></label>
          <label>Quantity<input name="quantity" type="number" min="1" max="999" value="${escapeHtml(collectionEntry.quantity || 1)}" /></label>
          <label>Condition<select name="condition">
            <option value=""${selected("", collectionEntry.condition || "")}>Not specified</option>
            <option value="Raw"${selected("Raw", collectionEntry.condition)}>Raw</option>
            <option value="Near Mint"${selected("Near Mint", collectionEntry.condition)}>Near Mint</option>
            <option value="Excellent"${selected("Excellent", collectionEntry.condition)}>Excellent</option>
            <option value="Good"${selected("Good", collectionEntry.condition)}>Good</option>
            <option value="Graded"${selected("Graded", collectionEntry.condition)}>Graded</option>
          </select></label>
          <label>Purchase price<input name="purchasePrice" type="number" min="0" step="0.01" inputmode="decimal" value="${escapeHtml(collectionEntry.purchasePrice ?? "")}" placeholder="0.00" /></label>
          <label>Currency<input name="purchaseCurrency" maxlength="3" pattern="[A-Za-z]{3}" value="${escapeHtml(collectionEntry.purchaseCurrency || "AUD")}" /></label>
          <label>Acquired<input name="acquiredAt" type="date" value="${escapeHtml(collectionEntry.acquiredAt || "")}" /></label>
        </div>
        <label class="notes-field">Notes<textarea name="notes" maxlength="2000" rows="3" placeholder="Grade, serial number, where you found it…">${escapeHtml(collectionEntry.notes || "")}</textarea></label>
        <button class="secondary-button" type="submit">Save details</button>
      </form>
    </div>
  </div>`;
  const dialog = $("#cardDialog");
  if (typeof dialog.showModal === "function") dialog.showModal(); else dialog.setAttribute("open", "");
}

async function saveCollectionDetails(form) {
  const values = new FormData(form);
  const cardId = form.dataset.cardId;
  const status = values.get("status");
  state.collection[cardId] = {
    status,
    quantity: Math.min(999, Math.max(1, Number(values.get("quantity")) || 1)),
    condition: String(values.get("condition") || "").trim() || null,
    purchasePrice: values.get("purchasePrice") === "" ? null : Math.max(0, Number(values.get("purchasePrice"))),
    purchaseCurrency: String(values.get("purchaseCurrency") || "AUD").trim().toUpperCase(),
    acquiredAt: values.get("acquiredAt") || null,
    notes: String(values.get("notes") || "").trim() || null,
    updatedAt: new Date().toISOString(),
  };
  saveCollection();
  renderAll();
  if (state.user) {
    updateSyncStatus("syncing", "Saving details…");
    try {
      await syncCard(cardId);
      updateSyncStatus("cloud", "Synced to your account");
    } catch (error) {
      updateSyncStatus("pending", "Saved here · sync pending");
      console.error(error);
    }
  }
  showToast(status === "missing" ? "Card removed from your list" : "Collection details saved");
}

function renderCards() {
  const matches = filteredCards();
  const shown = matches.slice(0, state.visibleCards);
  $("#resultCount").textContent = `${matches.length.toLocaleString()} card${matches.length === 1 ? "" : "s"}`;
  const selectedSet = state.catalogue.sets.find((set) => set.id === state.setId);
  const context = $("#setContext");
  context.hidden = !selectedSet;
  context.innerHTML = selectedSet ? `<button class="text-button" data-go="sets">← Set library</button><h2>${escapeHtml(selectedSet.shortName)}</h2><p>${selectedSet.year} · ${setOwnedCount(selectedSet.id)} / ${selectedSet.cardCount.toLocaleString()} checklist cards · ${formatPercentage(setOwnedCount(selectedSet.id), selectedSet.cardCount)}</p><div class="progress-track"><div class="progress-fill" style="--progress:${selectedSet.cardCount ? setOwnedCount(selectedSet.id) / selectedSet.cardCount * 100 : 0}%"></div></div>` : "";
  $("#activeSetLabel").textContent = selectedSet ? selectedSet.name : "Across all sets";
  $("#cardList").innerHTML = shown.length ? shown.map(cardRow).join("") : emptyState("No cards match these filters", "Try changing the set, category, status or search.");
  $("#loadMore").hidden = shown.length >= matches.length;
}

function renderCollection() {
  const ownedCards = state.catalogue.cards.filter((card) => statusFor(card.id) === "owned");
  const wanted = state.catalogue.cards.filter((card) => statusFor(card.id) === "wanted").length;
  const representedSets = new Set(ownedCards.map((card) => card.setId)).size;
  $("#collectionSummary").innerHTML = [
    ["Total cards", ownedCards.length.toLocaleString()], ["Sets represented", representedSets], ["Wanted cards", wanted.toLocaleString()],
  ].map(([label, value]) => `<div class="summary-card"><span>${label}</span><strong>${value}</strong></div>`).join("");
  const query = $("#ownedSearch").value.trim().toLocaleLowerCase();
  const sort = $("#ownedSort").value;
  const shown = ownedCards.filter(card => matchesPersonalSearch(card, query)).sort((a,b) => sort === "name" ? a.name.localeCompare(b.name) : sort === "set" ? a.setId.localeCompare(b.setId) || String(a.number).localeCompare(String(b.number), undefined, {numeric:true}) : new Date(entryFor(b.id)?.updatedAt || 0) - new Date(entryFor(a.id)?.updatedAt || 0));
  $("#collectionList").innerHTML = shown.length ? shown.map(cardRow).join("") : emptyState(ownedCards.length ? "No matching cards" : "Your collection starts here", ownedCards.length ? "Try another wrestler, set or card number." : "Browse the set library and mark your first card as Owned.");
  const wantedCards = state.catalogue.cards.filter(card => statusFor(card.id) === "wanted");
  const wantedQuery = $("#wantedSearch").value.trim().toLocaleLowerCase();
  const wantedShown = wantedCards.filter(card => matchesPersonalSearch(card, wantedQuery));
  $("#wantedCount").textContent = `${wantedCards.length} card${wantedCards.length === 1 ? "" : "s"} on your wanted list`;
  $("#wantedList").innerHTML = wantedShown.length ? wantedShown.map(cardRow).join("") : emptyState(wantedCards.length ? "No matching cards" : "Plan your next find", wantedCards.length ? "Try another search." : "Mark cards as Wanted while browsing a set. Your chase list will appear here.");
}

function matchesPersonalSearch(card, query) {
  const set = state.catalogue.sets.find(item => item.id === card.setId);
  return !query || [card.name, card.number, card.subset, set?.name].some(value => String(value || "").toLocaleLowerCase().includes(query));
}

function emptyState(title, message) { return `<div class="empty-state"><strong>${title}</strong><span>${message}</span></div>`; }
function renderAll() { renderStats(); renderSets(); renderRecent(); renderCards(); renderCollection(); }

function populateFilters() {
  $("#setFilter").innerHTML = `<option value="all">All sets</option>${state.catalogue.sets.map((set) => `<option value="${set.id}">${escapeHtml(set.shortName)}</option>`).join("")}`;
  const categories = [...new Set(state.catalogue.cards.map((card) => card.category))].sort();
  $("#categoryFilter").innerHTML = `<option value="all">All categories</option>${categories.map((category) => `<option value="${escapeHtml(category)}">${escapeHtml(category)}</option>`).join("")}`;
}

function changeView(view) {
  if (!["dashboard", "sets", "cards", "collection", "wanted"].includes(view)) return;
  state.view = view;
  $$(".view").forEach((element) => element.classList.toggle("active", element.id === `${view}View`));
  $$(".nav-link").forEach((element) => {
    const active = element.dataset.navGroup === "collection" ? ["dashboard", "collection"].includes(view) : element.dataset.navGroup === "sets" ? ["sets", "cards"].includes(view) : element.dataset.view === view;
    element.classList.toggle("active", active);
    if (active) element.setAttribute("aria-current", "page"); else element.removeAttribute("aria-current");
  });
  $("#collectionTabs").hidden = !["dashboard", "collection", "cards"].includes(view);
  $(".global-search").hidden = view !== "cards";
  $("#pageTitle").textContent = { dashboard: "My collection", sets: "Set library", cards: "Card catalogue", collection: "Owned cards", wanted: "Wanted" }[view];
  toggleMenu(false);
  history.replaceState(null, "", `#${view}`);
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function toggleMenu(open) {
  $(".sidebar").classList.toggle("open", open);
  $("#menuButton").setAttribute("aria-expanded", String(open));
  $("[data-profile]").setAttribute("aria-expanded", String(open));
  if (open) $(".sidebar-close").focus();
}

function showToast(message) {
  const toast = $("#toast");
  toast.textContent = message;
  toast.classList.add("show");
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => toast.classList.remove("show"), 2200);
}

function updateSyncStatus(mode, message) {
  const element = $("#syncStatus");
  if (!element) return;
  element.className = `sync-status ${mode}`;
  element.innerHTML = `<span class="status-dot"></span>${escapeHtml(message)}`;
}

function updateAuthUI() {
  const signedIn = Boolean(state.user);
  $("#authButton").hidden = signedIn;
  $("#accountSettingsButton").hidden = !signedIn;
  $("#signOutButton").hidden = !signedIn;
  $("#accountName").textContent = signedIn ? state.user.email : "Guest mode";
  $("#accountNote").textContent = signedIn ? "Your vault follows you" : "Sign in for cloud sync";
  updateSyncStatus(signedIn ? "cloud" : "local", signedIn ? "Synced to your account" : "Saved on this device");
}

function backupCollection() {
  const blob = new Blob([JSON.stringify({ version: 2, exportedAt: new Date().toISOString(), collection: state.collection }, null, 2)], { type: "application/json" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = `grailroster-backup-${new Date().toISOString().slice(0, 10)}.json`;
  link.click();
  URL.revokeObjectURL(link.href);
}

async function restoreCollection(file) {
  try {
    const payload = JSON.parse(await file.text());
    if (!payload.collection || typeof payload.collection !== "object") throw new Error("Invalid backup");
    state.collection = payload.collection;
    migrateLegacyCollectionIds();
    saveCollection();
    renderAll();
    if (state.user) await syncCollection();
    showToast("Collection restored");
  } catch (error) {
    showToast("That backup file could not be restored");
    console.error(error);
  }
}

async function fetchAllRows(table, columns, orderColumns) {
  const rows = [];
  for (let from = 0; ; from += API_PAGE_SIZE) {
    let query = state.supabase.from(table).select(columns);
    for (const column of [].concat(orderColumns)) query = query.order(column);
    const { data, error } = await query.range(from, from + API_PAGE_SIZE - 1);
    if (error) throw error;
    rows.push(...data);
    if (data.length < API_PAGE_SIZE) return rows;
  }
}

async function loadCatalogue() {
  const offlineResponse = await fetch("data/catalogue.json");
  if (!offlineResponse.ok) throw new Error("Catalogue failed to load");
  const offlineCatalogue = await offlineResponse.json();
  if (state.supabase) {
    try {
      const [sets, subsets, cards] = await Promise.all([
        fetchAllRows("catalogue_sets", "id,name,short_name,year,manufacturer,release_date,accent,card_count,subset_count", ["release_date", "id"]),
        fetchAllRows("catalogue_subsets", "set_id,subset_code,category,name,card_count", ["set_id", "subset_code"]),
        fetchAllRows("catalogue_cards", "id,set_id,checklist_order,card_number,display_name,subject_2,category,subset_code,roster,rookie,parallel_group", ["set_id", "checklist_order"]),
      ]);
      const subsetMap = new Map(subsets.map((subset) => [`${subset.set_id}\u0000${subset.subset_code}`, subset.name]));
      const remoteCatalogue = {
        schemaVersion: 2,
        setCount: sets.length,
        cardCount: cards.length,
        sets: sets.map((set) => ({
          id: set.id, name: set.name, shortName: set.short_name, year: set.year, manufacturer: set.manufacturer,
          releaseDate: set.release_date, accent: set.accent, cardCount: set.card_count, subsetCount: set.subset_count,
          subsets: subsets.filter((subset) => subset.set_id === set.id).map((subset) => ({ category: subset.category, name: subset.name, code: subset.subset_code, count: subset.card_count })),
        })),
        cards: cards.map((card) => ({
          id: card.id, setId: card.set_id, order: card.checklist_order, number: card.card_number, name: card.display_name,
          subject2: card.subject_2, category: card.category, subset: subsetMap.get(`${card.set_id}\u0000${card.subset_code}`),
          subsetCode: card.subset_code, roster: card.roster, rookie: card.rookie ? "Yes" : "No", parallelGroup: card.parallel_group,
        })),
      };
      if (remoteCatalogue.cardCount >= offlineCatalogue.cardCount) return remoteCatalogue;
      console.warn(`Supabase catalogue has ${remoteCatalogue.cardCount} cards; using the newer ${offlineCatalogue.cardCount}-card bundled catalogue.`);
    } catch (error) {
      console.warn("Supabase catalogue unavailable; using offline catalogue.", error);
    }
  }
  return offlineCatalogue;
}

function remoteRowToEntry(row) {
  return {
    status: row.status, quantity: row.quantity, condition: row.condition, purchasePrice: row.purchase_price,
    purchaseCurrency: row.purchase_currency, acquiredAt: row.acquired_at, notes: row.notes, updatedAt: row.updated_at,
  };
}

function entryToRemote(cardId, entry) {
  return {
    user_id: state.user.id, card_id: cardId, status: entry.status, quantity: entry.quantity || 1,
    condition: entry.condition || null, purchase_price: entry.purchasePrice ?? null,
    purchase_currency: entry.purchaseCurrency || "AUD", acquired_at: entry.acquiredAt || null,
    notes: entry.notes || null, updated_at: entry.updatedAt || new Date().toISOString(),
  };
}

async function syncCard(cardId) {
  const entry = entryFor(cardId);
  if (!entry || entry.status === "missing") {
    const { error } = await state.supabase.from("collection_items").delete().eq("user_id", state.user.id).eq("card_id", cardId);
    if (error) throw error;
    return;
  }
  const { error } = await state.supabase.from("collection_items").upsert(entryToRemote(cardId, entry), { onConflict: "user_id,card_id" });
  if (error) throw error;
}

async function syncCollection() {
  if (!state.user || state.syncing) return;
  state.syncing = true;
  updateSyncStatus("syncing", "Syncing your vault…");
  try {
    const remoteRows = await fetchAllRows("collection_items", "card_id,status,quantity,condition,purchase_price,purchase_currency,acquired_at,notes,updated_at", "card_id");
    const remote = new Map(remoteRows.map((row) => [row.card_id, remoteRowToEntry(row)]));
    const validCardIds = new Set(state.catalogue.cards.map((card) => card.id));
    const upserts = [];
    const deletions = [];

    for (const cardId of new Set([...Object.keys(state.collection), ...remote.keys()])) {
      if (!validCardIds.has(cardId)) continue;
      const localEntry = state.collection[cardId];
      const remoteEntry = remote.get(cardId);
      if (!localEntry && remoteEntry) {
        state.collection[cardId] = remoteEntry;
        continue;
      }
      if (!localEntry) continue;
      if (!remoteEntry) {
        if (localEntry.status !== "missing") upserts.push(entryToRemote(cardId, localEntry));
        continue;
      }
      if (new Date(remoteEntry.updatedAt || 0) > new Date(localEntry.updatedAt || 0)) {
        state.collection[cardId] = remoteEntry;
      } else if (localEntry.status === "missing") {
        deletions.push(cardId);
      } else {
        upserts.push(entryToRemote(cardId, localEntry));
      }
    }

    if (upserts.length) {
      const { error } = await state.supabase.from("collection_items").upsert(upserts, { onConflict: "user_id,card_id" });
      if (error) throw error;
    }
    if (deletions.length) {
      const { error } = await state.supabase.from("collection_items").delete().eq("user_id", state.user.id).in("card_id", deletions);
      if (error) throw error;
    }
    saveCollection();
    localStorage.setItem(GUEST_STORAGE_KEY, "{}");
    renderAll();
    updateSyncStatus("cloud", "Synced to your account");
  } catch (error) {
    updateSyncStatus("pending", "Saved here · sync pending");
    console.error(error);
  } finally {
    state.syncing = false;
  }
}

async function handleSession(session) {
  const previousUserId = state.user?.id;
  const nextUser = session?.user || null;
  if (nextUser?.id !== previousUserId) {
    state.user = nextUser;
    state.collection = nextUser
      ? mergeLocalCollections(loadCollection(collectionStorageKey(nextUser.id)), loadCollection(GUEST_STORAGE_KEY))
      : loadCollection(GUEST_STORAGE_KEY);
    if (state.catalogue) migrateLegacyCollectionIds();
  } else {
    state.user = nextUser;
  }
  updateAuthUI();
  if (state.catalogue) renderAll();
  if (state.user && state.user.id !== previousUserId && state.catalogue) await syncCollection();
}

function recoveryRequestedInUrl() {
  return new URLSearchParams(location.search).get("type") === "recovery"
    || new URLSearchParams(location.hash.replace(/^#/, "")).get("type") === "recovery";
}

function openPasswordUpdate() {
  setAuthMode("update-password");
  if (!$("#authDialog").open) $("#authDialog").showModal();
}

async function handleAuthEvent(event, session) {
  await handleSession(session);
  if (event === "PASSWORD_RECOVERY") openPasswordUpdate();
}

async function initSupabase() {
  const config = window.GRAILROSTER_CONFIG;
  if (!config?.supabaseUrl || !config?.supabasePublishableKey || !window.supabase?.createClient) return;
  const recoveryRequested = recoveryRequestedInUrl();
  state.supabase = window.supabase.createClient(config.supabaseUrl, config.supabasePublishableKey, {
    auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true },
  });
  state.supabase.auth.onAuthStateChange((event, session) => setTimeout(() => handleAuthEvent(event, session), 0));
  const { data, error } = await state.supabase.auth.getSession();
  if (error) console.error(error);
  state.user = data?.session?.user || null;
  if (state.user) state.collection = mergeLocalCollections(loadCollection(collectionStorageKey(state.user.id)), loadCollection(GUEST_STORAGE_KEY));
  if (recoveryRequested && data?.session) openPasswordUpdate();
}

async function sendMagicLink(email) {
  if (!state.supabase) throw new Error("Cloud sync is unavailable right now");
  const redirect = new URL(location.href);
  redirect.hash = "";
  redirect.search = "";
  const { error } = await state.supabase.auth.signInWithOtp({
    email,
    options: { emailRedirectTo: redirect.href, shouldCreateUser: true },
  });
  if (error) throw error;
}

async function signInWithPassword(email, password) {
  if (!state.supabase) throw new Error("Cloud sync is unavailable right now");
  const { data, error } = await state.supabase.auth.signInWithPassword({ email, password });
  if (error) throw error;
  return data;
}

async function signUpWithPassword(email, password) {
  if (!state.supabase) throw new Error("Cloud sync is unavailable right now");
  const redirect = new URL(location.href);
  redirect.hash = "";
  redirect.search = "";
  const { data, error } = await state.supabase.auth.signUp({
    email,
    password,
    options: { emailRedirectTo: redirect.href },
  });
  if (error) throw error;
  return data;
}

async function sendPasswordReset(email) {
  if (!state.supabase) throw new Error("Cloud sync is unavailable right now");
  const redirect = new URL(location.href);
  redirect.pathname = "/";
  redirect.hash = "";
  redirect.search = "";
  const { error } = await state.supabase.auth.resetPasswordForEmail(email, { redirectTo: redirect.href });
  if (error) throw error;
}

async function updatePassword(password) {
  if (!state.supabase) throw new Error("Cloud sync is unavailable right now");
  const { error } = await state.supabase.auth.updateUser({ password });
  if (error) throw error;
}

async function reauthenticate(currentPassword) {
  if (!state.user?.email) throw new Error("Please sign in again before changing account settings.");
  await signInWithPassword(state.user.email, currentPassword);
}

async function requestEmailChange(newEmail) {
  const redirect = new URL(location.href);
  redirect.hash = "";
  redirect.search = "";
  const { error } = await state.supabase.auth.updateUser(
    { email: newEmail },
    { emailRedirectTo: redirect.href },
  );
  if (error) throw error;
}

async function deleteCurrentAccount() {
  if (!state.user) throw new Error("Please sign in again before deleting your account.");
  const userId = state.user.id;
  const userStorageKey = collectionStorageKey(userId);
  const legacyUserStorageKey = legacyStorageKeyFor(userStorageKey);
  const { error } = await state.supabase.functions.invoke("delete-account", { body: {} });
  if (error) throw error;
  localStorage.removeItem(userStorageKey);
  if (legacyUserStorageKey) localStorage.removeItem(legacyUserStorageKey);
  localStorage.removeItem(GUEST_STORAGE_KEY);
  localStorage.removeItem(LEGACY_GUEST_STORAGE_KEY);
  await state.supabase.auth.signOut({ scope: "local" }).catch(() => {});
  state.user = null;
  state.collection = {};
  saveCollection();
  updateAuthUI();
  renderAll();
}

function authErrorMessage(error) {
  const message = error?.message || "Account access failed. Please try again.";
  if (/invalid login credentials/i.test(message)) return "Email or password is incorrect.";
  if (/email not confirmed/i.test(message)) return "Confirm your email before signing in.";
  if (/rate limit/i.test(message)) return "Email limit reached. Try password sign-in or wait before requesting another email.";
  return message;
}

function setAuthMode(mode) {
  authMode = mode;
  const signingUp = mode === "sign-up";
  const requestingReset = mode === "forgot-password";
  const updatingPassword = mode === "update-password";
  const regularAuth = !requestingReset && !updatingPassword;
  $("#authSignInTab").classList.toggle("active", !signingUp);
  $("#authSignInTab").setAttribute("aria-selected", String(!signingUp));
  $("#authSignUpTab").classList.toggle("active", signingUp);
  $("#authSignUpTab").setAttribute("aria-selected", String(signingUp));
  $("#authTabs").hidden = !regularAuth;
  $("#authEmailLabel").hidden = updatingPassword;
  $("#authEmail").hidden = updatingPassword;
  $("#authEmail").required = !updatingPassword;
  $("#authPasswordLabel").hidden = requestingReset;
  $("#authPassword").hidden = requestingReset;
  $("#authPassword").required = !requestingReset;
  const confirmingPassword = signingUp || updatingPassword;
  $("#authPasswordConfirmLabel").hidden = !confirmingPassword;
  $("#authPasswordConfirm").hidden = !confirmingPassword;
  $("#authPasswordConfirm").required = confirmingPassword;
  $("#authPasswordConfirmLabel").textContent = updatingPassword ? "Confirm new password" : "Confirm password";
  $("#authPasswordConfirm").placeholder = updatingPassword ? "Enter the new password again" : "Enter your password again";
  $("#passwordHint").hidden = requestingReset;
  $("#forgotPasswordButton").hidden = mode !== "sign-in";
  $("#authDivider").hidden = !regularAuth;
  $("#magicLinkButton").hidden = !regularAuth;
  $("#authBackButton").hidden = !requestingReset;
  $("#authPassword").autocomplete = signingUp || updatingPassword ? "new-password" : "current-password";
  $("#authEyebrow").textContent = updatingPassword ? "ACCOUNT SECURITY" : "CLOUD SYNC";
  $("#authTitle").textContent = requestingReset
    ? "Reset your password."
    : updatingPassword ? "Choose a new password." : signingUp ? "Create your vault." : "Sign in to your vault.";
  $("#authDescription").textContent = requestingReset
    ? "Enter your account email and we’ll send you a secure password-reset link."
    : updatingPassword ? "Use at least 8 characters. Your new password will apply immediately."
      : "Use an account to keep your collection synced across devices. Cards saved on this device will be merged into your account.";
  $("#passwordHint").textContent = signingUp || updatingPassword
    ? "Use at least 8 characters."
    : "Use the password for your GrailRoster account.";
  $("#authSubmit").textContent = requestingReset
    ? "Send reset link" : updatingPassword ? "Save new password" : signingUp ? "Create account" : "Sign in";
  $("#authSubmit").disabled = false;
  $("#magicLinkButton").textContent = "Email me a one-time sign-in link";
  $("#magicLinkButton").disabled = false;
  $("#authPassword").value = "";
  $("#authPasswordConfirm").value = "";
  $("#authMessage").textContent = "";
}

function attachEvents() {
  document.addEventListener("click", (event) => {
    if (event.target.closest("[data-profile]")) { toggleMenu(true); return; }
    if (event.target.closest("[data-close-menu]")) { toggleMenu(false); $("#menuButton").focus(); return; }
    const layout = event.target.closest("[data-layout-target]");
    if (layout) {
      document.getElementById(layout.dataset.layoutTarget).dataset.layout = layout.dataset.layout;
      $$(`[data-layout-target="${layout.dataset.layoutTarget}"]`).forEach(button => button.setAttribute("aria-pressed", String(button === layout)));
      return;
    }
    const open = event.target.closest("[data-open-card]");
    if (open) { openCard(open.dataset.openCard); return; }
    const nav = event.target.closest("[data-view]");
    if (nav) { event.preventDefault(); changeView(nav.dataset.view); return; }
    const go = event.target.closest("[data-go]");
    if (go) { changeView(go.dataset.go); return; }
    const set = event.target.closest("[data-set-id]");
    if (set) {
      state.setId = set.dataset.setId; state.category = state.status = "all"; state.query = "";
      $("#globalSearch").value = ""; $("#categoryFilter").value = $("#statusFilter").value = "all";
      $("#setFilter").value = state.setId; state.visibleCards = PAGE_SIZE;
      changeView("cards"); renderCards(); return;
    }
    const action = event.target.closest("[data-card-id]");
    if (action) setStatus(action.dataset.cardId, action.dataset.status);
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && $(".sidebar").classList.contains("open")) { toggleMenu(false); $("#menuButton").focus(); }
    const set = event.target.closest(".set-card[data-set-id]");
    if (!set || !["Enter", " "].includes(event.key)) return;
    event.preventDefault();
    set.click();
  });
  document.addEventListener("submit", (event) => {
    if (event.target.id !== "collectionDetailsForm") return;
    event.preventDefault();
    saveCollectionDetails(event.target);
  });
  $("#menuButton").addEventListener("click", () => toggleMenu(!$(".sidebar").classList.contains("open")));
  $("#setSearch").addEventListener("input", renderSets);
  $("#setOwnership").addEventListener("change", renderSets);
  $("#ownedSearch").addEventListener("input", renderCollection);
  $("#wantedSearch").addEventListener("input", renderCollection);
  $("#ownedSort").addEventListener("change", renderCollection);
  $("#globalSearch").addEventListener("input", (event) => { state.query = event.target.value; state.visibleCards = PAGE_SIZE; if (state.query && state.view !== "cards") changeView("cards"); renderCards(); });
  $("#setFilter").addEventListener("change", (event) => { state.setId = event.target.value; state.visibleCards = PAGE_SIZE; renderCards(); });
  $("#categoryFilter").addEventListener("change", (event) => { state.category = event.target.value; state.visibleCards = PAGE_SIZE; renderCards(); });
  $("#statusFilter").addEventListener("change", (event) => { state.status = event.target.value; state.visibleCards = PAGE_SIZE; renderCards(); });
  $("#clearFilters").addEventListener("click", () => {
    state.setId = state.category = state.status = "all"; state.query = ""; state.visibleCards = PAGE_SIZE;
    $("#setFilter").value = $("#categoryFilter").value = $("#statusFilter").value = "all"; $("#globalSearch").value = ""; renderCards();
  });
  $("#loadMore").addEventListener("click", () => { state.visibleCards += PAGE_SIZE; renderCards(); });
  $("#backupButton").addEventListener("click", backupCollection);
  $("#restoreInput").addEventListener("change", (event) => { if (event.target.files[0]) restoreCollection(event.target.files[0]); event.target.value = ""; });
  $("#closeCardDialog").addEventListener("click", () => $("#cardDialog").close());
  $("#cardDialog").addEventListener("click", (event) => { if (event.target === event.currentTarget) event.currentTarget.close(); });
  $("#authButton").addEventListener("click", () => { setAuthMode("sign-in"); $("#authDialog").showModal(); });
  $("#accountSettingsButton").addEventListener("click", () => {
    $("#settingsAccountEmail").textContent = state.user?.email || "";
    $$("#accountSettingsDialog form").forEach((form) => form.reset());
    $$("#accountSettingsDialog .settings-message").forEach((message) => { message.textContent = ""; });
    $("#accountSettingsDialog").showModal();
  });
  $("#closeAccountSettings").addEventListener("click", () => $("#accountSettingsDialog").close());
  $("#accountSettingsDialog").addEventListener("click", (event) => { if (event.target === event.currentTarget) event.currentTarget.close(); });
  $("#closeAuthDialog").addEventListener("click", () => $("#authDialog").close());
  $("#authDialog").addEventListener("click", (event) => { if (event.target === event.currentTarget) event.currentTarget.close(); });
  $("#authSignInTab").addEventListener("click", () => setAuthMode("sign-in"));
  $("#authSignUpTab").addEventListener("click", () => setAuthMode("sign-up"));
  $("#forgotPasswordButton").addEventListener("click", () => setAuthMode("forgot-password"));
  $("#authBackButton").addEventListener("click", () => setAuthMode("sign-in"));
  $("#signOutButton").addEventListener("click", async () => {
    const { error } = await state.supabase.auth.signOut();
    if (error) showToast("Sign out failed. Please try again."); else showToast("Signed out · cloud collection stays with your account");
  });
  $("#emailChangeForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const button = form.querySelector("button[type='submit']");
    const message = $("#emailChangeMessage");
    const newEmail = $("#newAccountEmail").value.trim();
    const currentPassword = $("#emailCurrentPassword").value;
    button.disabled = true;
    message.textContent = "Checking your password…";
    try {
      await reauthenticate(currentPassword);
      message.textContent = "Sending confirmation email…";
      await requestEmailChange(newEmail);
      form.reset();
      message.textContent = "Confirmation sent. Follow the email instructions to finish changing your address.";
    } catch (error) {
      message.textContent = authErrorMessage(error);
    } finally {
      button.disabled = false;
    }
  });
  $("#passwordChangeForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const button = form.querySelector("button[type='submit']");
    const message = $("#passwordChangeMessage");
    const currentPassword = $("#settingsCurrentPassword").value;
    const newPassword = $("#settingsNewPassword").value;
    const confirmPassword = $("#settingsConfirmPassword").value;
    if (newPassword !== confirmPassword) {
      message.textContent = "The new passwords do not match.";
      return;
    }
    if (currentPassword === newPassword) {
      message.textContent = "Choose a password different from your current password.";
      return;
    }
    button.disabled = true;
    message.textContent = "Checking your current password…";
    try {
      await reauthenticate(currentPassword);
      message.textContent = "Updating your password…";
      await updatePassword(newPassword);
      form.reset();
      message.textContent = "Password updated successfully.";
    } catch (error) {
      message.textContent = authErrorMessage(error);
    } finally {
      button.disabled = false;
    }
  });
  $("#deleteAccountForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const button = form.querySelector("button[type='submit']");
    const message = $("#deleteAccountMessage");
    if ($("#deleteConfirmation").value !== "DELETE") {
      message.textContent = "Type DELETE exactly to confirm.";
      return;
    }
    button.disabled = true;
    message.textContent = "Checking your password…";
    try {
      await reauthenticate($("#deleteCurrentPassword").value);
      message.textContent = "Deleting your account and cloud collection…";
      await deleteCurrentAccount();
      $("#accountSettingsDialog").close();
      showToast("Your account and cloud collection were deleted");
    } catch (error) {
      message.textContent = authErrorMessage(error);
      button.disabled = false;
    }
  });
  $("#authForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = $("#authSubmit");
    const magicButton = $("#magicLinkButton");
    const message = $("#authMessage");
    const email = $("#authEmail").value.trim();
    const password = $("#authPassword").value;
    const passwordConfirm = $("#authPasswordConfirm").value;
    button.disabled = true;
    magicButton.disabled = true;
    if (authMode === "forgot-password") {
      message.textContent = "Sending your password-reset link…";
      try {
        await sendPasswordReset(email);
        message.textContent = "If an account exists for that email, a GrailRoster reset link is on its way.";
        button.textContent = "Reset link sent";
      } catch (error) {
        message.textContent = authErrorMessage(error);
        button.disabled = false;
      }
      return;
    }
    if (["sign-up", "update-password"].includes(authMode) && password !== passwordConfirm) {
      message.textContent = "The passwords do not match.";
      button.disabled = false;
      magicButton.disabled = false;
      return;
    }
    if (authMode === "update-password") {
      message.textContent = "Updating your password…";
      try {
        await updatePassword(password);
        $("#authDialog").close();
        setAuthMode("sign-in");
        showToast("Password updated successfully");
      } catch (error) {
        message.textContent = authErrorMessage(error);
        button.disabled = false;
      }
      return;
    }
    message.textContent = authMode === "sign-up" ? "Creating your account…" : "Signing you in…";
    try {
      const data = authMode === "sign-up"
        ? await signUpWithPassword(email, password)
        : await signInWithPassword(email, password);
      if (authMode === "sign-up" && !data.session) {
        message.textContent = "Account created. Check your email to confirm it before signing in.";
        button.textContent = "Confirmation required";
        magicButton.disabled = false;
      } else {
        $("#authDialog").close();
        showToast(authMode === "sign-up" ? "Account created · your vault is syncing" : "Signed in · your vault is syncing");
      }
    } catch (error) {
      message.textContent = authErrorMessage(error);
      button.disabled = false;
      magicButton.disabled = false;
    }
  });
  $("#magicLinkButton").addEventListener("click", async () => {
    const email = $("#authEmail");
    const button = $("#magicLinkButton");
    const submit = $("#authSubmit");
    const message = $("#authMessage");
    if (!email.reportValidity()) return;
    button.disabled = true;
    submit.disabled = true;
    message.textContent = "Sending your secure sign-in link…";
    try {
      await sendMagicLink(email.value.trim());
      message.textContent = "Check your email and open the GrailRoster sign-in link.";
      button.textContent = "Link sent";
    } catch (error) {
      message.textContent = authErrorMessage(error);
      button.disabled = false;
      submit.disabled = false;
    }
  });
  window.addEventListener("online", () => { if (state.user) syncCollection(); });
}

async function init() {
  try {
    GrailUI.mountIcons();
    await initSupabase();
    const [catalogue, imageResponse] = await Promise.all([loadCatalogue(), fetch("data/images.json").catch(() => null)]);
    state.catalogue = catalogue;
    if (imageResponse?.ok) state.images = await imageResponse.json();
    migrateLegacyCollectionIds();
    populateFilters();
    attachEvents();
    updateAuthUI();
    renderAll();
    if (state.user) await syncCollection();
    const requested = location.hash.slice(1);
    changeView(["dashboard", "sets", "cards", "collection", "wanted"].includes(requested) ? requested : "dashboard");
    if ("serviceWorker" in navigator && location.protocol !== "file:") navigator.serviceWorker.register("sw.js");
  } catch (error) {
    $(".content").innerHTML = emptyState("GrailRoster could not load", "Refresh the page to try again.");
    console.error(error);
  }
}

init();
