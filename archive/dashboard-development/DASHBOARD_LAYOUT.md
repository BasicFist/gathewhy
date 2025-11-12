# AI Dashboard Layout - Redesigned

## Layout Strategy

**Service Table DOMINATES** - The service table is now the primary focus (60-70% of screen space).

### Before vs After

#### BEFORE (Broken)
```
┌────────────────────┬────────────────┐  Column ratio: 3:2 (60%:40%)
│ Overview (5 lines) │ GPU (10 lines) │
│ HOT PINK           │ LASER GREEN    │
├────────────────────┼────────────────┤
│                    │                │
│ Service Table      │ Detail Panel   │
│ ELECTRIC CYAN      │ BLAZING YELLOW │  ← HUGE WASTE OF SPACE
│ (cramped)          │ (height: 1fr)  │     Detail panel empty but
│                    │ EMPTY VOID!!!  │     taking 30% of screen!
│                    │                │
│                    ├────────────────┤
│                    │ Event Log (8)  │
│                    │ NEON PURPLE    │
└────────────────────┴────────────────┘

Problems:
✗ Service table cramped (only ~40% of left column)
✗ Detail panel EMPTY but consuming massive space (height: 1fr)
✗ GPU card showing "No GPU detected" but taking 10 lines
✗ Event log tiny and stuck in corner
```

#### AFTER (Optimized)
```
┌─────────────────────────────────┬──────────┐  Column ratio: 4:1 (80%:20%)
│ Overview (7 lines - compact)    │ GPU Card │
│ HOT PINK                        │ (auto)   │  ← Auto-sized: 5 lines min
│                                 │ GREEN    │     12 lines max
├─────────────────────────────────┼──────────┤
│                                 │          │
│                                 │ Detail   │  ← Auto-sized: 8 lines min
│   SERVICE TABLE                 │ Panel    │     20 lines max
│   (DOMINANT - 60-70% height)    │ (auto)   │     Only takes space when
│   ELECTRIC CYAN                 │ YELLOW   │     content is present
│                                 │          │
│                                 │          │
├─────────────────────────────────┴──────────┤
│ Event Log (10 lines, full width)           │  ← Full width for better
│ NEON PURPLE                                 │     readability
└─────────────────────────────────────────────┘

Improvements:
✓ Service table gets 80% horizontal space + 60-70% vertical space
✓ Detail panel auto-sized: no wasted space when empty
✓ GPU card auto-sized: tiny when no GPU detected
✓ Event log full-width: better readability
✓ Overview compact: just a status bar (7 lines)
```

## CSS Changes Summary

### Grid Structure
```css
Container#body {
    grid-columns: 4fr 1fr;     /* was: 3fr 2fr */
    grid-rows: auto 1fr auto;  /* was: auto 1fr */
}

#event-log-container {
    column-span: 2;            /* NEW: spans both columns */
}
```

### Panel Sizing

#### Overview Panel (HOT PINK)
```css
height: 7;  /* was: 5 - slightly more room for 3-line content */
```

#### Service Table (ELECTRIC CYAN)
```css
height: 1fr;  /* unchanged - fills available space */
/* Now has MORE space due to grid column change (4fr vs 3fr) */
```

#### GPU Card (LASER GREEN)
```css
height: auto;       /* was: 10 - now auto-sizes */
min-height: 5;      /* NEW: tiny when no GPU */
max-height: 12;     /* NEW: cap at 12 lines */
```

#### Detail Panel (BLAZING YELLOW)
```css
height: auto;       /* was: 1fr - KEY FIX! */
min-height: 8;      /* NEW: reasonable minimum */
max-height: 20;     /* NEW: prevent bloat */
```

#### Event Log (NEON PURPLE)
```css
height: 10;  /* was: 8 - slightly more visible */
/* Now spans full width (column-span: 2) */
```

## Layout Behavior

### Service Table Dominance
- **Horizontal**: 80% of width (4fr out of 5fr total)
- **Vertical**: Fills available space between overview and event log
- **Result**: 60-70% of total screen real estate

### Conditional Panels
- **GPU Card**: Auto-sizes based on content
  - No GPU detected: ~5 lines (just border + message)
  - GPU detected: 8-12 lines (metrics + per-GPU breakdown)

- **Detail Panel**: Auto-sizes based on selection
  - Nothing selected: ~8 lines (just "Select a provider" message)
  - Service selected: 15-20 lines (full metrics + control buttons)

### Event Log
- **Position**: Bottom of screen, spans both columns
- **Visibility**: Full width for better readability
- **Height**: Fixed at 10 lines (reasonable for scrolling)

## Space Distribution

### Terminal Size: 120x40 (typical)

#### Before (Broken)
- Header: 1 line
- Overview: 5 lines
- Service Table: ~18 lines (cramped)
- GPU Card: 10 lines (wasted)
- Detail Panel: ~15 lines (EMPTY)
- Event Log: 8 lines (squeezed)
- Footer: 1 line

**Service Table**: ~18 lines = 45% of content area (BAD)

#### After (Optimized)
- Header: 1 line
- Overview: 7 lines
- Service Table: ~24 lines (dominant)
- GPU Card: 5 lines (no GPU)
- Detail Panel: 8 lines (nothing selected)
- Event Log: 10 lines (full width)
- Footer: 1 line

**Service Table**: ~24 lines = 60% of content area (GOOD!)

## Key Insights

1. **Auto-sizing is KEY**: Using `height: auto` with min/max prevents wasted space
2. **Grid columns matter**: 4:1 ratio gives service table the dominance it deserves
3. **Full-width event log**: Better readability and visual balance
4. **Compact overview**: It's a status bar, not a feature showcase
5. **Conditional expansion**: Panels only take space when they have content

## Color Coding (Neon Theme)

- **HOT PINK** (#FF10F0): Overview Panel
- **ELECTRIC CYAN** (#00F0FF): Service Table ← DOMINANT
- **LASER GREEN** (#39FF14): GPU Card
- **BLAZING YELLOW** (#FFFF00): Detail Panel
- **NEON PURPLE** (#BF00FF): Event Log

## Future Improvements

- Consider hiding GPU card entirely when no GPU detected (not just auto-sizing)
- Consider collapsing detail panel to 3 lines when nothing selected
- Add toggle to hide/show right column entirely for ultra-wide service table view
- Add keyboard shortcut to toggle between "compact" and "detailed" layouts
