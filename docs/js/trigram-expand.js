(function() {
  "use strict";

  let trigramData = null;

  async function loadTrigramData() {
    if (trigramData) return trigramData;
    const resp = await fetch("data/trigrams.json");
    trigramData = await resp.json();
    return trigramData;
  }

  function buildCompletionHTML(completions, gridName, known1, known2) {
    if (!completions || Object.keys(completions).length === 0) {
      return '<p class="no-completions">No completions found.</p>';
    }

    // Parse grid name to determine gap position and build the trigram pattern
    // gridName is like "gap2_win123" → gap at position 2 of the trigram, window 1-2-3
    var gapPos = parseInt(gridName.charAt(3), 10); // 1, 2, or 3
    // known1 is always the lower word position, known2 the higher

    var sorted = Object.entries(completions).sort(function(a, b) { return b[1] - a[1]; });
    var total = sorted.reduce(function(sum, entry) { return sum + entry[1]; }, 0);
    var maxCount = sorted[0][1];

    var items = sorted.map(function(entry) {
      var gapLetter = entry[0], count = entry[1];
      var pct = ((count / total) * 100).toFixed(1);
      var barWidth = ((count / maxCount) * 100).toFixed(1);

      // Build the trigram: position the gap letter correctly
      var trigram;
      if (gapPos === 1) {
        trigram = gapLetter + known1 + known2;
      } else if (gapPos === 2) {
        trigram = known1 + gapLetter + known2;
      } else {
        trigram = known1 + known2 + gapLetter;
      }

      return '<div class="completion-item">'
        + '<span class="completion-letter">' + trigram + '</span>'
        + '<span class="completion-bar" style="width: ' + barWidth + '%"></span>'
        + '<span class="completion-count">' + count + '</span>'
        + '<span class="completion-pct">(' + pct + '%)</span>'
        + '</div>';
    }).join("\n");

    // Heading that explains what you're looking at
    var pattern;
    if (gapPos === 1) {
      pattern = "_" + known1 + known2;
    } else if (gapPos === 2) {
      pattern = known1 + "_" + known2;
    } else {
      pattern = known1 + known2 + "_";
    }

    return '<h4>Completions for ' + pattern + ' (' + total + ' words)</h4>'
      + '<div class="completion-list">' + items + '</div>';
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

    expansionDiv.innerHTML = buildCompletionHTML(completions, grid, known1, known2);
    expansionDiv.classList.add("active");
    activeCell = cell;
  });
})();
