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

      var numA = parseFloat(valA);
      var numB = parseFloat(valB);
      if (!isNaN(numA) && !isNaN(numB)) {
        return ascending ? numA - numB : numB - numA;
      }
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

  /* --- Bigram drill-down --- */

  var bigramData = null;

  function loadBigramData() {
    if (bigramData) return Promise.resolve(bigramData);
    return fetch("data/bigrams.json")
      .then(function (r) { return r.json(); })
      .then(function (d) { bigramData = d; return d; });
  }

  function buildBarChart(distribution, heading, mainLetter, direction) {
    var sorted = Object.entries(distribution).sort(function (a, b) {
      return b[1] - a[1];
    });
    if (sorted.length === 0) return "";

    var max = sorted[0][1];
    var html = '<h4>' + heading + '</h4>';
    sorted.forEach(function (entry) {
      var nbLetter = entry[0], count = entry[1];
      var pair = direction === "left"
        ? nbLetter + mainLetter
        : mainLetter + nbLetter;
      var width = ((count / max) * 100).toFixed(1);
      html += '<div class="bar-row">'
        + '<span class="bar-label">' + pair + '</span>'
        + '<span class="bar" style="width: ' + width + '%"></span>'
        + '<span class="bar-count">' + count + '</span>'
        + '</div>';
    });
    return html;
  }

  var activeBigramElement = null;

  function showBigramDrilldown(element, letter, pos) {
    var grid = element.closest(".bigram-grid");
    if (!grid) return;
    var expansionDiv = document.getElementById("expand-" + grid.id);
    if (!expansionDiv) return;

    if (activeBigramElement === element) {
      expansionDiv.classList.remove("active");
      expansionDiv.innerHTML = "";
      activeBigramElement = null;
      return;
    }

    document.querySelectorAll(".bigram-expansion.active").forEach(function (d) {
      d.classList.remove("active");
      d.innerHTML = "";
    });

    loadBigramData().then(function (data) {
      var parts = [];

      if (pos > 1) {
        var leftKey = (pos - 1) + "_" + pos;
        var leftData = data[leftKey] || {};
        var leftDist = {};
        Object.keys(leftData).forEach(function (first) {
          var count = leftData[first][letter];
          if (count) leftDist[first] = count;
        });
        if (Object.keys(leftDist).length > 0) {
          parts.push(buildBarChart(leftDist, "What precedes " + letter + " (pos " + (pos - 1) + "\u2013" + pos + ")", letter, "left"));
        }
      }

      if (pos < 5) {
        var rightKey = pos + "_" + (pos + 1);
        var rightDist = data[rightKey] ? (data[rightKey][letter] || {}) : {};
        if (Object.keys(rightDist).length > 0) {
          parts.push(buildBarChart(rightDist, "What follows " + letter + " (pos " + pos + "\u2013" + (pos + 1) + ")", letter, "right"));
        }
      }

      if (parts.length === 0) {
        expansionDiv.innerHTML = "<p>No neighbour data for this letter.</p>";
      } else {
        expansionDiv.innerHTML = '<div class="neighbour-bars">' + parts.join("") + '</div>';
      }
      expansionDiv.classList.add("active");
      activeBigramElement = element;
    }).catch(function () {
      expansionDiv.innerHTML = "<p>Failed to load bigram data.</p>";
      expansionDiv.classList.add("active");
    });
  }

  /* --- Single delegated click handler for everything --- */

  document.addEventListener("click", function (e) {
    // Sortable column header
    var sortTh = e.target.closest(".sortable-table .sortable");
    if (sortTh) {
      var table = sortTh.closest("table");
      var colIdx = parseInt(sortTh.getAttribute("data-col"), 10);
      var wasAsc = sortTh.getAttribute("data-sort-dir") === "asc";
      var ascending = !wasAsc;

      table.querySelectorAll("thead .sortable").forEach(function (h) {
        h.removeAttribute("data-sort-dir");
        h.classList.remove("sort-asc", "sort-desc");
      });

      sortTh.setAttribute("data-sort-dir", ascending ? "asc" : "desc");
      sortTh.classList.add(ascending ? "sort-asc" : "sort-desc");
      sortTable(table, colIdx, ascending);
    }

    // Bigram column header drill-down
    var bigramCol = e.target.closest(".bigram-col");
    if (bigramCol) {
      var letter = bigramCol.getAttribute("data-letter");
      var pos = parseInt(bigramCol.getAttribute("data-pos"), 10);
      showBigramDrilldown(bigramCol, letter, pos);
      return;
    }

    // Bigram row label drill-down
    var bigramRow = e.target.closest(".bigram-row");
    if (bigramRow) {
      var letter = bigramRow.getAttribute("data-letter");
      var pos = parseInt(bigramRow.getAttribute("data-pos"), 10);
      showBigramDrilldown(bigramRow, letter, pos);
      return;
    }

    // Bigram cell click — show drill-downs for both row and column letters
    var bigramCell = e.target.closest(".bigram-cell[data-row]");
    if (bigramCell) {
      var rowLetter = bigramCell.getAttribute("data-row");
      var colLetter = bigramCell.getAttribute("data-col-letter");
      var rowPos = parseInt(bigramCell.getAttribute("data-row-pos"), 10);
      var colPos = parseInt(bigramCell.getAttribute("data-col-pos"), 10);
      var count = bigramCell.getAttribute("data-value");
      var grid = bigramCell.closest(".bigram-grid");
      if (!grid) return;
      var expansionDiv = document.getElementById("expand-" + grid.id);
      if (!expansionDiv) return;

      // Toggle off
      if (activeBigramElement === bigramCell) {
        expansionDiv.classList.remove("active");
        expansionDiv.innerHTML = "";
        activeBigramElement = null;
        return;
      }

      document.querySelectorAll(".bigram-expansion.active").forEach(function (d) {
        d.classList.remove("active");
        d.innerHTML = "";
      });

      loadBigramData().then(function (data) {
        var parts = [];
        var pair = rowLetter + colLetter;
        parts.push("<h4>" + pair + ": " + count + " words</h4>");

        // What precedes rowLetter (_X drill-down)
        if (rowPos > 1) {
          var leftKey = (rowPos - 1) + "_" + rowPos;
          var leftData = data[leftKey] || {};
          var leftDist = {};
          Object.keys(leftData).forEach(function (first) {
            var c = leftData[first][rowLetter];
            if (c) leftDist[first] = c;
          });
          if (Object.keys(leftDist).length > 0) {
            parts.push(buildBarChart(leftDist, "What precedes " + rowLetter + " (pos " + (rowPos - 1) + "\u2013" + rowPos + ")", rowLetter, "left"));
          }
        }

        // What follows colLetter (X_ drill-down)
        if (colPos < 5) {
          var rightKey = colPos + "_" + (colPos + 1);
          var rightDist = data[rightKey] ? (data[rightKey][colLetter] || {}) : {};
          if (Object.keys(rightDist).length > 0) {
            parts.push(buildBarChart(rightDist, "What follows " + colLetter + " (pos " + colPos + "\u2013" + (colPos + 1) + ")", colLetter, "right"));
          }
        }

        expansionDiv.innerHTML = '<div class="neighbour-bars">' + parts.join("") + '</div>';
        expansionDiv.classList.add("active");
        activeBigramElement = bigramCell;
      }).catch(function () {
        expansionDiv.innerHTML = "<p>Failed to load bigram data.</p>";
        expansionDiv.classList.add("active");
      });
      return;
    }
  });
})();
