const DATA = window.MUSEUM || { title: "家展", stats: {}, photos: [], exhibitions: [] };
const $ = (id) => document.getElementById(id);
let activeExhibition = null;
let activeYear = null;
let query = "";

function esc(value) {
  return String(value == null ? "" : value).replace(/[&<>"']/g, (ch) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[ch]));
}

function renderStats() {
  const stats = DATA.stats || {};
  $("stats").innerHTML = `
    <div class="stat"><b>${stats.photos || 0}</b><span>PHOTOS / 照片</span></div>
    <div class="stat"><b>${esc(stats.year_span || "—")}</b><span>YEARS / 年份</span></div>
    <div class="stat"><b>${stats.places || 0}</b><span>PLACES / 地点</span></div>
    <div class="stat"><b>${stats.duplicates || 0}</b><span>DUPLICATES / 重复</span></div>`;
}

function renderExhibitions() {
  const list = (DATA.exhibitions || []).slice(0, 12);
  $("exhibitions").innerHTML = list.map((item) => `
    <button class="exhibition ${activeExhibition === item.key ? "active" : ""}" data-key="${esc(item.key)}">
      <img src="${esc(item.cover)}" alt="${esc(item.title)}" loading="lazy">
      <div class="label"><b>${esc(item.title)}</b><span>${item.count} 件 · ${esc(item.subtitle)}</span></div>
    </button>`).join("") || `<div class="empty">还没有展厅。先往照片目录里放几张图。</div>`;
  document.querySelectorAll(".exhibition").forEach((node) => {
    node.addEventListener("click", () => {
      activeExhibition = activeExhibition === node.dataset.key ? null : node.dataset.key;
      activeYear = null;
      renderAll();
    });
  });
}

function renderYears() {
  const years = (DATA.stats && DATA.stats.years) || [];
  $("years").innerHTML = years.map((year) => `
    <button class="year ${activeYear === year ? "active" : ""}" data-year="${year}">${year}</button>`).join("");
  document.querySelectorAll(".year").forEach((node) => {
    node.addEventListener("click", () => {
      activeYear = activeYear === Number(node.dataset.year) ? null : Number(node.dataset.year);
      activeExhibition = null;
      renderAll();
    });
  });
}

function matches(photo) {
  if (activeYear && photo.year !== activeYear) return false;
  if (activeExhibition && `${photo.year}-${photo.season}` !== activeExhibition) return false;
  if (query) {
    const hay = `${photo.caption} ${photo.album} ${photo.file} ${photo.date}`.toLowerCase();
    if (!hay.includes(query.toLowerCase())) return false;
  }
  return true;
}

function renderGrid() {
  const items = (DATA.photos || []).filter(matches);
  const all = (DATA.photos || []).length;
  $("status").textContent = items.length === all
    ? `正在展出全部 ${all} 件`
    : `正在展出 ${items.length} 件 / 共 ${all} 件`;
  $("grid").innerHTML = items.map((photo) => `
    <button class="photo" data-id="${photo.id}">
      <div class="frame"><img src="${esc(photo.thumb)}" alt="${esc(photo.caption)}" loading="lazy"></div>
      <div class="cap">${esc(photo.caption || photo.file)}</div>
      <div class="meta">${esc(photo.date)} · ${esc(photo.album)}</div>
    </button>`).join("") || `<div class="empty">没有符合条件的展品。换个年份，或清空搜索。</div>`;
  document.querySelectorAll(".photo").forEach((node) => {
    node.addEventListener("click", () => openLightbox(Number(node.dataset.id)));
  });
}

function renderAll() {
  renderExhibitions();
  renderYears();
  renderGrid();
}

function openLightbox(id) {
  const photo = (DATA.photos || []).find((item) => item.id === id);
  if (!photo) return;
  $("lightImg").src = photo.full || photo.thumb;
  $("lightImg").alt = photo.caption || photo.file;
  $("lightCaption").textContent = `${photo.caption || photo.file} · ${photo.date} · ${photo.album}`;
  $("lightbox").classList.remove("hidden");
  document.body.style.overflow = "hidden";
}

function closeLightbox() {
  $("lightbox").classList.add("hidden");
  document.body.style.overflow = "";
}

$("search").addEventListener("input", (event) => { query = event.target.value.trim(); renderGrid(); });
$("btnAll").addEventListener("click", () => {
  activeExhibition = null; activeYear = null; query = ""; $("search").value = "";
  renderAll();
});
$("close").addEventListener("click", closeLightbox);
$("lightbox").addEventListener("click", (event) => { if (event.target.id === "lightbox") closeLightbox(); });
document.addEventListener("keydown", (event) => { if (event.key === "Escape") closeLightbox(); });

if (DATA.title) {
  $("title").textContent = DATA.title;
  document.title = `${DATA.title} · 家展`;
}
if (DATA.photos && DATA.photos.length) {
  const cover = DATA.photos[0].thumb;
  $("hero").style.setProperty("--cover", `url("${cover}")`);
}
renderStats();
renderAll();
