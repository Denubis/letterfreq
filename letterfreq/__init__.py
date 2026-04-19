"""Pure-functional building blocks for the ten-letter analysis page.

Modules:
    reference: Baseline frequency counters for letter, bigram, start/end trigram,
               and first/last letter over an arbitrary word corpus.
    scoring:   Per-word scoring functions for ranking ten-letter words.
    render:    HTML rendering helpers for the reference and ranking tables.

Each module is side-effect-free; entry scripts (`main.py`, `main_ten.py`)
do I/O and call into these modules.
"""
