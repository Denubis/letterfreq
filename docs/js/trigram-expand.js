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

  document.addEventListener("DOMContentLoaded", function() {
    document.querySelectorAll(".trigram-cell:not(.empty)").forEach(function(cell) {
      cell.addEventListener("click", async function() {
        const grid = this.closest(".trigram-grid").dataset.grid;
        const known1 = this.dataset.known1;
        const known2 = this.dataset.known2;
        const expansionDiv = document.getElementById("expand-" + grid);

        if (!expansionDiv) return;

        // Toggle off if clicking same cell
        if (activeCell === this) {
          expansionDiv.classList.remove("active");
          expansionDiv.innerHTML = "";
          activeCell = null;
          return;
        }

        const data = await loadTrigramData();
        const completions = data[grid]?.[known1]?.[known2];

        expansionDiv.innerHTML = buildCompletionHTML(completions);
        expansionDiv.classList.add("active");
        activeCell = this;
      });
    });
  });
})();
