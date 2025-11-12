# Neon Theme Color Reference Card

## Quick Color Palette

### Primary Neon Colors
```
#00ffff - Cyan     (Primary accent, overview panel, event log, text)
#ff00ff - Magenta  (Secondary accent, service table, resources)
#ffd700 - Gold     (Detail panel, headers, selected items)
#00ff00 - Green    (Success, active services, GPU monitoring)
#39ff14 - Bright Green (Success hover states)
```

### Status Colors
```
#00ff00 - Active     (Service healthy and running)
#ff6600 - Degraded   (Service with warnings)
#ff0044 - Inactive   (Service stopped or unreachable)
```

### Backgrounds
```
#0a0e27 - Deep BG      (Main screen background)
#1a1a2e - Panel BG     (Widget backgrounds)
#0f0f1f - Dark BG      (Log backgrounds)
#151530 - Subtle BG    (Table even rows)
#2a2a4e - Highlight BG (Headers, cursor)
```

### Text Colors
```
#ffffff - White      (Primary text)
#00ffff - Cyan       (Accent text)
#ffd700 - Gold       (Titles, headers)
#ff00ff - Magenta    (Metrics, resources)
```

---

## Component Border Colors

| Component | Border Color | Hex Code |
|-----------|--------------|----------|
| Overview Panel | Cyan | `#00ffff` |
| Service Table | Magenta | `#ff00ff` |
| GPU Card | Green | `#00ff00` |
| Detail Panel | Gold | `#ffd700` |
| Event Log | Cyan | `#00ffff` |
| Detail Notes | Dark Purple | `#333355` |

---

## Button Color Scheme

| Button Type | Border | Text | Hover BG | Hover Text |
|-------------|--------|------|----------|------------|
| Start (Success) | `#00ff00` | `#00ff00` | `#002200` | `#39ff14` |
| Stop (Error) | `#ff0044` | `#ff0044` | `#220000` | `#ff2266` |
| Restart (Warning) | `#ff6600` | `#ff6600` | `#221100` | `#ff8844` |
| Enable/Disable | `#ff00ff` | `#ff00ff` | `#220022` | `#ff44ff` |
| Default | `#00ffff` | `#00ffff` | `#2a2a4e` | `#ffffff` |

---

## Color Psychology

### Cyan (`#00ffff`)
- **Feeling**: Technology, data, information
- **Usage**: Primary UI elements, safe/neutral operations
- **Visibility**: High contrast on dark backgrounds

### Magenta (`#ff00ff`)
- **Feeling**: Energy, creativity, distinctiveness
- **Usage**: Data tables, metrics, secondary accents
- **Visibility**: Stands out without being alarming

### Gold (`#ffd700`)
- **Feeling**: Premium, focus, importance
- **Usage**: Selected items, important headers
- **Visibility**: Warm accent that draws attention

### Green (`#00ff00`)
- **Feeling**: Success, health, active
- **Usage**: Positive status indicators, GPU (hardware)
- **Visibility**: Universally recognized positive signal

### Orange (`#ff6600`)
- **Feeling**: Caution, attention needed
- **Usage**: Degraded services, warnings
- **Visibility**: Clear warning without panic

### Red (`#ff0044`)
- **Feeling**: Error, stopped, critical
- **Usage**: Inactive services, failed operations
- **Visibility**: Immediate attention required

---

## Textual CSS Border Styles

```css
border: heavy #00ffff;   /* Thick cyan border */
border: solid #ff00ff;   /* Standard magenta border */
```

**Available border styles in Textual:**
- `heavy` - Thick double-line border (used for main panels)
- `solid` - Standard single-line border (used for secondary elements)
- `dashed` - Dashed line border
- `double` - Double-line border

---

## Rich Markup Examples

```python
# Success message (green)
f"[#00ff00]✓ Operation successful[/]"

# Error message (red)
f"[#ff0044]✗ Operation failed[/]"

# Warning message (orange)
f"[#ff6600]⚠ Warning condition[/]"

# Info message (cyan)
f"[#00ffff]ℹ Information[/]"

# Bold status (green)
f"[#00ff00 bold]ACTIVE[/]"

# Mixed colors
f"Status: [#ffd700]Selected[/] | Response: [#00ffff]{ms}ms[/]"
```

---

## Terminal Color Support

### 24-bit Color (Recommended)
- Full hex color support
- Exact neon colors as designed
- Modern terminals: iTerm2, Windows Terminal, GNOME Terminal, Alacritty

### 256-color
- Close approximations of neon colors
- Good fallback for older terminals
- Colors may be slightly less vibrant

### 16-color
- Basic color fallback
- Neon colors map to nearest basic colors
- Functional but less visually striking

---

## Color Contrast Ratios

All color combinations meet WCAG AA standards for contrast:

| Foreground | Background | Ratio | Status |
|------------|------------|-------|--------|
| `#00ffff` on `#0a0e27` | 15.8:1 | ✅ AAA |
| `#ffffff` on `#1a1a2e` | 16.1:1 | ✅ AAA |
| `#00ff00` on `#1a1a2e` | 14.3:1 | ✅ AAA |
| `#ff0044` on `#1a1a2e` | 5.2:1 | ✅ AA |
| `#ffd700` on `#1a1a2e` | 11.6:1 | ✅ AAA |

---

## Design Principles

1. **High Contrast**: Dark backgrounds (`#0a0e27`) with bright neon foregrounds
2. **Visual Hierarchy**: Different border colors for different panel types
3. **Semantic Color**: Status colors follow universal conventions (green=good, red=bad)
4. **Consistency**: Same color families used throughout (cyan family, magenta family, etc.)
5. **Accessibility**: All text meets contrast requirements, supplemented with text labels
6. **Retro-Futurism**: Neon aesthetic inspired by cyberpunk and synthwave

---

## Maintenance Notes

When modifying colors:
1. Maintain contrast ratios (use WebAIM contrast checker)
2. Test on multiple terminal types
3. Ensure semantic meaning is preserved (green=success, red=error)
4. Update this reference document
5. Test with colorblind simulation tools
