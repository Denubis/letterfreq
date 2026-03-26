# Test Pseudocode

Human-readable description of what each test does, organised by domain.
Maintained by project-claude-librarian at branch completion.

Overlapping tests and coverage gaps are documented intentionally --
they reveal where the test suite is redundant or incomplete.

## Word Loading (sanity checks)

### Word count is positive
**File:** tests/test_frequencies.py::test_word_count_is_positive
1. Load words from system dictionary
2. Assert count > 1000

**Verifies:** The word source produces a meaningful dataset

### All words are five lowercase letters
**File:** tests/test_frequencies.py::test_all_words_are_five_letters
1. Load words from system dictionary
2. For each word, assert length == 5 and all lowercase alpha

**Verifies:** The word filter correctly selects only five-letter lowercase words

## Overall Frequency

### Frequency sum equals 5 times word count
**File:** tests/test_frequencies.py::test_frequency_sum_equals_five_times_word_count
1. Compute overall frequencies from loaded words
2. Sum all letter counts
3. Assert sum == 5 * len(words)

**Verifies:** Every letter position in every word is counted exactly once

### All 26 letters present
**File:** tests/test_frequencies.py::test_all_26_letters_present
1. Compute overall frequencies
2. Collect the set of letters in the result
3. Assert set equals a-z

**Verifies:** No letter is dropped during frequency computation

### Spot-check letter 'e'
**File:** tests/test_frequencies.py::test_spot_check_letter_e
1. Compute overall frequencies via Polars
2. Manually count occurrences of 'e' across all words
3. Assert Polars count matches manual count

**Verifies:** Polars computation matches naive Python counting for a known high-frequency letter

## Positional Unigrams

### Column sums equal word count
**File:** tests/test_frequencies.py::test_positional_unigram_column_sums
1. Compute positional unigrams
2. For each of the 5 positions, sum counts across all 26 letters
3. Assert each sum == word_count

**Verifies:** Each position accounts for exactly one letter per word

### All 26 letters have entries
**File:** tests/test_frequencies.py::test_positional_unigram_all_26_letters
1. Compute positional unigrams
2. Assert the dict has all 26 lowercase keys

**Verifies:** No letter is dropped from positional counting

### Spot-check 'e' at position 5
**File:** tests/test_frequencies.py::test_positional_unigram_spot_check_e_pos5
1. Compute positional unigrams
2. Manually count words where the 5th character is 'e'
3. Assert Polars count matches manual count

**Verifies:** Positional slicing is correct at the last position

## Bigrams

### Position pair sums equal word count (parametrised: 1_2, 2_3, 3_4, 4_5)
**File:** tests/test_frequencies.py::test_bigram_position_sum
1. Compute bigrams for all 4 adjacent position pairs
2. For each pair, sum all bigram counts across all letter combinations
3. Assert sum == word_count

**Verifies:** Each position pair accounts for exactly one bigram per word

### Spot-check 'th' at positions 1-2
**File:** tests/test_frequencies.py::test_bigram_spot_check_th
1. Compute bigrams
2. Look up bigrams['1_2']['t']['h']
3. Manually count words starting with "th"
4. Assert counts match

**Verifies:** Bigram computation matches naive counting for a common English pair

## Neighbour Distributions (bigram drill-downs)

### Middle position has both left and right
**File:** tests/test_frequencies.py::test_neighbour_middle_position_has_both
1. Get neighbour distributions for 'e' at position 3
2. Assert both 'left' and 'right' keys exist and are non-empty

**Verifies:** Middle positions correctly produce bidirectional neighbour data

### Position 1 has only right neighbour
**File:** tests/test_frequencies.py::test_neighbour_position_1_only_right
1. Get neighbour distributions for 's' at position 1
2. Assert 'right' exists and 'left' does not

**Verifies:** Edge position correctly omits impossible direction

### Position 5 has only left neighbour
**File:** tests/test_frequencies.py::test_neighbour_position_5_only_left
1. Get neighbour distributions for 's' at position 5
2. Assert 'left' exists and 'right' does not

**Verifies:** Edge position correctly omits impossible direction

### Neighbour sum matches unigram count (cross-check)
**File:** tests/test_frequencies.py::test_neighbour_sum_matches_unigram
1. Compute both unigrams and neighbour distributions
2. For several letter/position combos, sum right-neighbour counts
3. Assert sum equals the unigram count at that position
4. Repeat for left-neighbour sums at positions 2-5

**Verifies:** Neighbour distributions are consistent with positional unigrams (data integrity cross-check)

## Trigrams

### Nine expected keys present
**File:** tests/test_frequencies.py::test_trigram_data_has_nine_keys
1. Compute trigrams
2. Assert top-level keys are exactly the 9 gap/window combinations

**Verifies:** All 9 trigram configurations are computed (3 gaps x 3 windows)

### Spot-check gap1_win123 for 'h','e'
**File:** tests/test_frequencies.py::test_trigram_gap1_win123_spot_check
1. Compute trigrams
2. Look up completions for known1='h', known2='e' in gap1_win123
3. Sum completion counts
4. Manually count words matching pattern .he..
5. Assert counts match

**Verifies:** Trigram computation matches regex-based counting for a known pattern

### Empty pair returns no data
**File:** tests/test_frequencies.py::test_trigram_empty_pair_returns_no_data
1. Compute trigrams
2. Check that 'q' at position 2 + 'z' at position 3 produces no completions
3. Manually verify no words match this pattern

**Verifies:** Absent letter combinations are correctly omitted rather than producing zero-count entries
