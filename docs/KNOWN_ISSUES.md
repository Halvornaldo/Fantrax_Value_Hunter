# Known Issues

## Name Matching Issues (December 2025)

### 1. Understat JSON Import - 3 Players Not Matching
**Status:** Open
**Severity:** Low (workaround exists)

**Problem:**
When importing Understat player JSON, 3 players consistently fail to match despite having exact name matches in the database:
- Ezra Mayers (WHU)
- Yoane Wissa (NEW)
- Zach Abbott (NOT)

**Workaround:**
Manual name mappings have been added to the database. These should auto-match in future imports.

**Root Cause (To Investigate):**
- Names appear identical but may have encoding differences (unicode normalization?)
- The `UnifiedNameMatcher` may not be finding exact matches in certain cases
- Need to add logging to see what the matcher is receiving vs what's in the DB

---

### 2. Validation Dropdown Not Suggesting Players
**Status:** Open
**Severity:** Medium

**Problem:**
In the game validation modal (Manual Player Matching Required), the dropdown for unmatched players only shows "Skip this player" option. It should suggest potential Fantrax player matches.

**Expected Behavior:**
Dropdown should show suggested matches from the database based on fuzzy name matching, team, etc.

**Location:**
- Frontend: `/import-games` page validation modal
- Backend: Likely the endpoint that returns `suggestions` array for unmatched players

**To Investigate:**
- Check if backend is returning `suggestions` array in the validation response
- Check if frontend is rendering the suggestions in the dropdown
- The `UnifiedNameMatcher` should return `suggested_matches` for low-confidence matches

---

### 3. Exact Name Matches Failing
**Status:** Open
**Severity:** Medium

**Problem:**
Some players with exact name matches in the database are not being matched automatically. This suggests the matching logic may have issues with:
- Case sensitivity
- Unicode/accent handling
- Source system filtering

**Players Affected:**
- Ezra Mayers (exact match exists)
- Yoane Wissa (exact match exists)
- Zach Abbott (exact match exists)

**To Investigate:**
- Add debug logging to `UnifiedNameMatcher.match_player()`
- Check if source_system filter is too restrictive
- Verify exact string comparison is working correctly

---

## Resolved Issues

### Understat JSON Import Not Saving Data (Fixed Dec 2025)
**Problem:** When uploading Understat JSON with unmatched players, clicking OK on verification dialog redirected without saving matched players.
**Fix:** Changed `frontend/src/App.js` to always apply matched players immediately before showing any dialogs.

### Game Scores Import - io Module Error (Fixed Dec 2025)
**Problem:** `name 'io' is not defined` error when importing game scores.
**Fix:** Added `import io` to `src/app.py`.
