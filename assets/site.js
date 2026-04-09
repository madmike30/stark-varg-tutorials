const state = {
  tutorials: [],
  filter: "all",
  query: "",
};

const listEl = document.getElementById("tutorial-list");
const resultsCountEl = document.getElementById("results-count");
const totalCountEl = document.getElementById("total-count");
const mxCountEl = document.getElementById("mx-count");
const exCountEl = document.getElementById("ex-count");
const template = document.getElementById("tutorial-row-template");
const searchInput = document.getElementById("search-input");
const filterButtons = Array.from(document.querySelectorAll(".filter-chip"));

function updateCounts(tutorials) {
  const mxCount = tutorials.filter((item) => item.applicable_models.includes("MX 1.2")).length;
  const exCount = tutorials.filter((item) => item.applicable_models.includes("EX")).length;

  totalCountEl.textContent = tutorials.length;
  mxCountEl.textContent = mxCount;
  exCountEl.textContent = exCount;
}

function getVisibleTutorials() {
  const query = state.query.trim().toLowerCase();

  return state.tutorials.filter((item) => {
    const matchesFilter = state.filter === "all" || item.applicable_models.includes(state.filter);
    const matchesQuery =
      !query ||
      item.title.toLowerCase().includes(query) ||
      item.full_title.toLowerCase().includes(query) ||
      item.applicability_label.toLowerCase().includes(query);

    return matchesFilter && matchesQuery;
  });
}

function renderTutorials() {
  const visibleTutorials = getVisibleTutorials();
  listEl.innerHTML = "";

  if (!visibleTutorials.length) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.textContent = "No tutorials match the current filters.";
    listEl.appendChild(empty);
    resultsCountEl.textContent = "0 tutorials shown";
    return;
  }

  const fragment = document.createDocumentFragment();

  visibleTutorials.forEach((item) => {
    const row = template.content.firstElementChild.cloneNode(true);
    row.querySelector(".model-pill").textContent = item.applicability_label;
    row.querySelector("h3").textContent = item.title;

    const [pdfLink, videoLink] = row.querySelectorAll(".row-link");
    pdfLink.href = item.pdf_url;
    videoLink.href = item.video_url;

    fragment.appendChild(row);
  });

  listEl.appendChild(fragment);
  resultsCountEl.textContent = `${visibleTutorials.length} tutorial${visibleTutorials.length === 1 ? "" : "s"} shown`;
}

function setActiveFilter(nextFilter) {
  state.filter = nextFilter;
  filterButtons.forEach((button) => {
    const isActive = button.dataset.filter === nextFilter;
    button.classList.toggle("is-active", isActive);
    button.setAttribute("aria-pressed", String(isActive));
  });
  renderTutorials();
}

async function loadTutorials() {
  const response = await fetch("data/tutorials.json");
  const payload = await response.json();
  state.tutorials = payload.tutorials;
  updateCounts(state.tutorials);
  renderTutorials();
}

filterButtons.forEach((button) => {
  button.addEventListener("click", () => setActiveFilter(button.dataset.filter));
});

searchInput.addEventListener("input", (event) => {
  state.query = event.target.value;
  renderTutorials();
});

loadTutorials().catch(() => {
  resultsCountEl.textContent = "Unable to load tutorial data.";
  listEl.innerHTML = '<div class="empty-state">The tutorial list could not be loaded.</div>';
});
