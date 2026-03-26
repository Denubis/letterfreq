(function () {
  "use strict";

  /* --- Column sorting for all .sortable-table tables --- */

  function sortTable(table, colIdx, ascending) {
    var tbody = table.querySelector("tbody");
    var rows = Array.from(tbody.querySelectorAll("tr"));

    rows.sort(function (a, b) {
      var cellA = a.children[colIdx];
      var cellB = b.children[colIdx];
      var valA = cellA ? cellA.getAttribute("data-value") : "";
      var valB = cellB ? cellB.getAttribute("data-value") : "";

      // Numeric if both parse
      var numA = parseFloat(valA);
      var numB = parseFloat(valB);
      if (!isNaN(numA) && !isNaN(numB)) {
        return ascending ? numA - numB : numB - numA;
      }
      // Fall back to text (letters)
      var textA = (cellA ? cellA.textContent : "").trim();
      var textB = (cellB ? cellB.textContent : "").trim();
      return ascending
        ? textA.localeCompare(textB)
        : textB.localeCompare(textA);
    });

    rows.forEach(function (row) {
      tbody.appendChild(row);
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".sortable-table .sortable").forEach(function (th) {
      th.style.cursor = "pointer";
      th.addEventListener("click", function () {
        var table = this.closest("table");
        var colIdx = parseInt(this.getAttribute("data-col"), 10);
        var wasAsc = this.getAttribute("data-sort-dir") === "asc";
        var ascending = !wasAsc;

        // Clear sort indicators on siblings
        table.querySelectorAll("thead .sortable").forEach(function (h) {
          h.removeAttribute("data-sort-dir");
          h.classList.remove("sort-asc", "sort-desc");
        });

        this.setAttribute("data-sort-dir", ascending ? "asc" : "desc");
        this.classList.add(ascending ? "sort-asc" : "sort-desc");
        sortTable(table, colIdx, ascending);
      });
    });

    /* --- Bigram row click → drill-down expansion --- */

    var bigramData = null;

    function loadBigramData() {
      if (bigramData) return Promise.resolve(bigramData);
      return fetch("data/bigrams.json")
        .then(function (r) { return r.json(); })
        .then(function (d) { bigramData = d; return d; });
    }

    function buildBarChart(distribution, label) {
      var sorted = Object.entries(distribution).sort(function (a, b) {
        return b[1] - a[1];
      });
      if (sorted.length === 0) return "";

      var max = sorted[0][1];
      var html = '<h4>' + label + '</h4>';
      sorted.forEach(function (entry) {
        var letter = entry[0], count = entry[1];
        var width = ((count / max) * 100).toFixed(1);
        html += '<div class="bar-row">'
          + '<span class="bar-label">' + letter + '</span>'
          + '<span class="bar" style="width: ' + width + '%"></span>'
          + '<span class="bar-count">' + count + '</span>'
          + '</div>';
      });
      return html;
    }

    var activeBigramRow = null;

    document.querySelectorAll(".bigram-row").forEach(function (cell) {
      cell.style.cursor = "pointer";
      cell.addEventListener("click", function () {
        var letter = this.getAttribute("data-letter");
        var pos = parseInt(this.getAttribute("data-pos"), 10);
        var grid = this.closest(".bigram-grid");
        var expansionDiv = document.getElementById("expand-" + grid.id);

        if (!expansionDiv) return;

        // Toggle off
        if (activeBigramRow === this) {
          expansionDiv.classList.remove("active");
          expansionDiv.innerHTML = "";
          activeBigramRow = null;
          return;
        }

        // Close any other open bigram expansion
        document.querySelectorAll(".bigram-expansion.active").forEach(function (d) {
          d.classList.remove("active");
          d.innerHTML = "";
        });

        loadBigramData().then(function (data) {
          var parts = [];

          // Left neighbour
          if (pos > 1) {
            var leftKey = (pos - 1) + "_" + pos;
            var leftData = data[leftKey] || {};
            var leftDist = {};
            Object.keys(leftData).forEach(function (first) {
              var count = leftData[first][letter];
              if (count) leftDist[first] = count;
            });
            if (Object.keys(leftDist).length > 0) {
              parts.push(buildBarChart(leftDist, "Position " + (pos - 1) + " \u2192 " + letter));
            }
          }

          // Right neighbour
          if (pos < 5) {
            var rightKey = pos + "_" + (pos + 1);
            var rightDist = data[rightKey] ? (data[rightKey][letter] || {}) : {};
            if (Object.keys(rightDist).length > 0) {
              parts.push(buildBarChart(rightDist, letter + " \u2192 Position " + (pos + 1)));
            }
          }

          if (parts.length === 0) {
            expansionDiv.innerHTML = "<p>No neighbour data for this letter.</p>";
          } else {
            expansionDiv.innerHTML = '<div class="neighbour-bars">' + parts.join("") + '</div>';
          }
          expansionDiv.classList.add("active");
          activeBigramRow = cell;
        }).catch(function () {
          expansionDiv.innerHTML = "<p>Failed to load bigram data.</p>";
          expansionDiv.classList.add("active");
        });
      });
    });
  });
})();
