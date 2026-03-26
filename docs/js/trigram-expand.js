(function() {
  "use strict";

  let trigramData = null;

  async function loadTrigramData() {
    if (trigramData) return trigramData;
    const resp = await fetch("data/trigrams.json");
    trigramData = await resp.json();
    return trigramData;
  }

  function buildCompletionHTML(completions) {
    if (!completions || Object.keys(completions).length === 0) {
      return '<p class="no-completions">No completions found.</p>';
    }

    const sorted = Object.entries(completions).sort((a, b) => b[1] - a[1]);
    const total = sorted.reduce((sum, [, count]) => sum + count, 0);
    const maxCount = sorted[0][1];

    const items = sorted.map(([letter, count]) => {
      const pct = ((count / total) * 100).toFixed(1);
      const barWidth = ((count / maxCount) * 100).toFixed(1);
      return `<div class="completion-item">
        <span class="completion-letter">${letter}</span>
        <span class="completion-bar" style="width: ${barWidth}%"></span>
        <span class="completion-count">${count}</span>
        <span class="completion-pct">(${pct}%)</span>
      </div>`;
    }).join("\n");

    return `<div class="completion-list">${items}</div>`;
  }

  let activeCell = null;

  // Event delegation — survives Zensical instant navigation DOM swaps
  document.addEventListener("click", async function(e) {
    var cell = e.target.closest(".trigram-cell:not(.empty)");
    if (!cell) return;

    var gridEl = cell.closest(".trigram-grid");
    if (!gridEl) return;

    var grid = gridEl.dataset.grid;
    var known1 = cell.dataset.known1;
    var known2 = cell.dataset.known2;
    var expansionDiv = document.getElementById("expand-" + grid);

    if (!expansionDiv) return;

    // Toggle off if clicking same cell
    if (activeCell === cell) {
      expansionDiv.classList.remove("active");
      expansionDiv.innerHTML = "";
      activeCell = null;
      return;
    }

    // Close any previously active expansion
    document.querySelectorAll(".trigram-expansion.active").forEach(function(div) {
      div.classList.remove("active");
      div.innerHTML = "";
    });

    let data;
    try {
      data = await loadTrigramData();
    } catch (err) {
      expansionDiv.innerHTML = '<p>Failed to load trigram data.</p>';
      expansionDiv.classList.add("active");
      return;
    }
    var completions = data[grid]?.[known1]?.[known2];

    expansionDiv.innerHTML = buildCompletionHTML(completions);
    expansionDiv.classList.add("active");
    activeCell = cell;
  });
})();
