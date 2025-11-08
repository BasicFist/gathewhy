# AI Dashboard Layout Redesign - Detailed CSS Diff

## File: scripts/ai-dashboard

### Change 1: Grid Structure (Lines 977-1016)

```diff
-    /* Body grid - REDESIGNED FOR BETTER VISUAL BALANCE
-       Left column: 60% (overview compact, table prominent)
-       Right column: 40% (GPU bigger, detail/log balanced)
-
-       ┌──────────────────┬──────────────┐
-       │ overview (small) │ gpu (bigger) │
-       │ service table    │ detail       │
-       │  (prominent)     │ event log    │
-       └──────────────────┴──────────────┘
-    */
-
-    Container#body {
-        layout: grid;
-        grid-size: 2;
-        grid-columns: 3fr 2fr;
-        grid-rows: auto 1fr;
-        height: 1fr;
-        padding: 1 2;
-        background: #0a0e27;
-    }
-
-    Vertical#left-column,
-    Vertical#right-column {
-        layout: vertical;
-    }
+    /* Body grid - REDESIGNED FOR SPACE EFFICIENCY
+       Strategy: Service table DOMINATES, panels only take space when needed
+       Left column: 75% (service table is KING)
+       Right column: 25% (conditional panels, compact)
+
+       ┌────────────────────────────┬──────────┐
+       │ overview (3 lines)         │ gpu      │
+       ├────────────────────────────┤ (compact)│
+       │                            ├──────────┤
+       │   SERVICE TABLE            │ detail   │
+       │   (DOMINANT - 60-70%)      │ (auto)   │
+       │                            │          │
+       ├────────────────────────────┴──────────┤
+       │ event log (full width, 10 lines)      │
+       └────────────────────────────────────────┘
+    */
+
+    Container#body {
+        layout: grid;
+        grid-size: 2;
+        grid-columns: 4fr 1fr;      /* ← CHANGED: was 3fr 2fr */
+        grid-rows: auto 1fr auto;   /* ← CHANGED: was auto 1fr */
+        height: 1fr;
+        padding: 1 2;
+        background: #0a0e27;
+    }
+
+    Vertical#left-column {
+        layout: vertical;
+        column-span: 1;             /* ← NEW: explicit span */
+    }
+
+    Vertical#right-column {
+        layout: vertical;
+        column-span: 1;             /* ← NEW: explicit span */
+    }
+
+    #event-log-container {          /* ← NEW: event log container */
+        column-span: 2;             /* ← NEW: spans both columns */
+    }
```

**Impact**: Service table now gets 80% of width instead of 60%, event log spans full width

---

### Change 2: Overview Panel (Lines 1018-1028)

```diff
-    /* ═══════════════════════════════════════════════════════════════════════
-       OVERVIEW PANEL - HOT PINK border (more compact now)
-       Height reduced for better balance - overview is a summary, not main focus
-       ═══════════════════════════════════════════════════════════════════════ */
     OverviewPanel {
         border: heavy #FF10F0;
         background: #1a1a2e;
         color: #ffffff;
         padding: 1;
-        height: 5;
+        height: 7;                  /* ← CHANGED: was 5 */
     }
+    /* ═══════════════════════════════════════════════════════════════════════
+       OVERVIEW PANEL - HOT PINK border (ultra-compact)
+       Just 3 lines - overview is a status bar, not main focus
+       ═══════════════════════════════════════════════════════════════════════ */
```

**Impact**: Slightly taller for proper 3-line content display with padding

---

### Change 3: GPU Card (Lines 1060-1072)

```diff
-    /* ═══════════════════════════════════════════════════════════════════════
-       GPU CARD - LASER GREEN glow (bigger for more visibility)
-       GPU metrics are critical - give them more space
-       ═══════════════════════════════════════════════════════════════════════ */
     GPUCard {
         border: heavy #39FF14;
         background: #1a1a2e;
         color: #ffffff;
         padding: 1;
-        height: 10;
+        height: auto;               /* ← CHANGED: was 10 */
+        min-height: 5;              /* ← NEW: minimum size */
+        max-height: 12;             /* ← NEW: maximum size */
     }
+    /* ═══════════════════════════════════════════════════════════════════════
+       GPU CARD - LASER GREEN glow (compact, expands with content)
+       Auto-sized: tiny when no GPU, bigger when GPU detected
+       ═══════════════════════════════════════════════════════════════════════ */
```

**Impact**: No GPU = ~5 lines (saves 5 lines), GPU detected = 8-12 lines (scales with content)

---

### Change 4: Detail Panel (Lines 1074-1086) - KEY FIX!

```diff
-    /* ═══════════════════════════════════════════════════════════════════════
-       DETAIL PANEL - BLAZING YELLOW glow (balanced sizing)
-       ═══════════════════════════════════════════════════════════════════════ */
     #detail-panel {
         border: heavy #FFFF00;
         background: #1a1a2e;
         color: #ffffff;
         padding: 1;
-        height: 1fr;
+        height: auto;               /* ← KEY FIX: was 1fr (filled all space) */
+        min-height: 8;              /* ← NEW: reasonable minimum */
+        max-height: 20;             /* ← NEW: prevent bloat */
     }
+    /* ═══════════════════════════════════════════════════════════════════════
+       DETAIL PANEL - BLAZING YELLOW glow (auto-sized, no waste)
+       Only takes space when populated, max 20 lines to prevent bloat
+       ═══════════════════════════════════════════════════════════════════════ */
```

**Impact**: **THIS WAS THE BUG** - Empty detail panel was consuming ~15 lines, now only ~8 lines

---

### Change 5: Event Log CSS (Lines 1175-1192)

```diff
-    /* ═══════════════════════════════════════════════════════════════════════
-       EVENT LOG - NEON PURPLE border (compact but visible)
-       ═══════════════════════════════════════════════════════════════════════ */
     Log {
-        height: 8;
+        height: 10;                 /* ← CHANGED: was 8 */
         border: heavy #BF00FF;
         background: #0f0f1f;
         color: #00F0FF;
         padding: 1;
     }

     #event-log {
         border: heavy #BF00FF;
         background: #0f0f1f;
         color: #00F0FF;
+        height: 10;                 /* ← NEW: explicit height */
     }
+    /* ═══════════════════════════════════════════════════════════════════════
+       EVENT LOG - NEON PURPLE border (full width, properly visible)
+       Spans both columns at bottom for better readability
+       ═══════════════════════════════════════════════════════════════════════ */
```

**Impact**: Slightly taller (10 vs 8 lines), now full width for better visibility

---

### Change 6: Compose Method (Lines 1243-1254)

```diff
     def compose(self) -> ComposeResult:
         yield Header(show_clock=True)
         with Container(id="body"):
             with Vertical(id="left-column"):
                 yield OverviewPanel(id="overview")
                 yield ServiceTable()
             with Vertical(id="right-column"):
                 yield GPUCard(id="gpu")
                 yield DetailPanel()
-                yield Log(id="event-log", highlight=True)
+            with Container(id="event-log-container"):  /* ← NEW: own container */
+                yield Log(id="event-log", highlight=True)
         yield Footer()
```

**Impact**: Event log now in its own container that spans both columns (via CSS column-span: 2)

---

## Summary of Changes

| Component | Old Value | New Value | Reason |
|-----------|-----------|-----------|--------|
| **Grid columns** | `3fr 2fr` | `4fr 1fr` | Give service table 80% width instead of 60% |
| **Grid rows** | `auto 1fr` | `auto 1fr auto` | Add third row for full-width event log |
| **Overview height** | `5` | `7` | Proper space for 3-line content with padding |
| **GPU height** | `10` (fixed) | `auto` (5-12) | Auto-size: tiny when no GPU, expandable with GPU |
| **Detail height** | `1fr` (fills space) | `auto` (8-20) | **KEY FIX**: Only use space when needed |
| **Event log height** | `8` | `10` | Slightly more visible |
| **Event log position** | Right column | Own container (spans both) | Full-width for readability |

## The Root Cause

**Detail Panel with `height: 1fr`** was the PRIMARY bug.

- `1fr` means "fill all available space"
- When nothing was selected, detail panel showed "Select a provider" but consumed 15-20 lines
- This created the **MASSIVE EMPTY YELLOW VOID**
- Fix: `height: auto` means "only use space you need"

## Validation

```bash
# 1. Verify Python syntax
python3 -m py_compile scripts/ai-dashboard

# 2. Run dashboard and verify:
./scripts/ai-dashboard

# Expected behavior:
✓ Service table is now DOMINANT (60-70% of screen)
✓ Detail panel is small (~8 lines) when nothing selected
✓ Detail panel expands (15-20 lines) when service selected
✓ GPU card is tiny (~5 lines) when no GPU detected
✓ Event log spans full width at bottom
✓ No empty yellow void!
```

## Lines Changed

- **CSS Comments**: ~30 lines updated
- **CSS Rules**: 6 sections modified
- **Python compose()**: 3 lines modified
- **Total**: ~40 lines changed out of 1373 lines (2.9% of file)
