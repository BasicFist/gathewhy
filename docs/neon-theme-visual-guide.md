# AI Dashboard Neon Theme Visual Guide

## Overview

The AI Dashboard has been enhanced with a modern **Neon Cyberpunk** theme, featuring vibrant colors, heavy borders for visual impact, and a dark background for maximum contrast and readability.

---

## Color Palette

### Primary Colors

| Color Name | Hex Code | RGB | Usage |
|-----------|----------|-----|-------|
| **Neon Cyan** | `#00ffff` | `(0, 255, 255)` | Primary accent, borders, text highlights |
| **Neon Magenta** | `#ff00ff` | `(255, 0, 255)` | Secondary accent, service table borders |
| **Neon Yellow/Gold** | `#ffd700` | `(255, 215, 0)` | Detail panel accent, headers |
| **Neon Green** | `#00ff00` | `(0, 255, 0)` | Success states, active services, GPU borders |
| **Bright Green** | `#39ff14` | `(57, 255, 20)` | Success hover states |

### Status Colors

| Status | Hex Code | RGB | Usage |
|--------|----------|-----|-------|
| **Active** | `#00ff00` | `(0, 255, 0)` | Service running and healthy |
| **Degraded** | `#ff6600` | `(255, 102, 0)` | Service with issues or warnings |
| **Inactive** | `#ff0044` | `(255, 0, 68)` | Service stopped or unreachable |

### Background Colors

| Element | Hex Code | RGB | Usage |
|---------|----------|-----|-------|
| **Deep Background** | `#0a0e27` | `(10, 14, 39)` | Main screen background |
| **Panel Background** | `#1a1a2e` | `(26, 26, 46)` | Panel and widget backgrounds |
| **Dark Background** | `#0f0f1f` | `(15, 15, 31)` | Log backgrounds |
| **Subtle Background** | `#151530` | `(21, 21, 48)` | Table even rows |
| **Highlight Background** | `#2a2a4e` | `(42, 42, 78)` | Table headers, cursor highlight |

### Text Colors

| Context | Hex Code | RGB | Usage |
|---------|----------|-----|-------|
| **Primary Text** | `#ffffff` | `(255, 255, 255)` | Main content text |
| **Accent Text** | `#00ffff` | `(0, 255, 255)` | Highlighted information |
| **Detail Text** | `#ffd700` | `(255, 215, 0)` | Selected service titles |
| **Resource Text** | `#ff00ff` | `(255, 0, 255)` | Resource usage metrics |

---

## Component Styling

### 1. Screen & Layout
- **Background**: Deep blue-black (`#0a0e27`)
- **Purpose**: Provides high contrast for neon colors

### 2. Header & Footer
- **Background**: `#1a1a2e`
- **Text Color**: Neon cyan (`#00ffff`)
- **Style**: Bold text
- **Purpose**: Frame the dashboard with consistent branding

### 3. Overview Panel
- **Border**: Heavy cyan (`#00ffff`)
- **Background**: `#1a1a2e`
- **Text Color**: White (`#ffffff`)
- **Purpose**: Quick summary with high visibility

### 4. Service Table
- **Border**: Heavy magenta (`#ff00ff`)
- **Background**: `#1a1a2e`
- **Text Color**: Cyan (`#00ffff`)
- **Header Background**: `#2a2a4e`
- **Header Text**: Gold (`#ffd700`), bold
- **Cursor/Selected Row**: `#2a2a4e` background, neon green (`#00ff00`) text
- **Zebra Striping**: Alternating `#1a1a2e` and `#151530`
- **Status Colors**:
  - Active: Neon green (`#00ff00`)
  - Degraded: Neon orange (`#ff6600`)
  - Inactive: Neon red (`#ff0044`)

### 5. GPU Card
- **Border**: Heavy neon green (`#00ff00`)
- **Background**: `#1a1a2e`
- **Text Color**: White (`#ffffff`)
- **Purpose**: GPU monitoring with distinctive green accent

### 6. Detail Panel
- **Border**: Heavy gold (`#ffd700`)
- **Background**: `#1a1a2e`
- **Text Color**: White (`#ffffff`)
- **Title**: Gold (`#ffd700`), bold
- **Status Info**: Cyan (`#00ffff`)
- **Resource Info**: Magenta (`#ff00ff`)
- **Metadata**: Cyan (`#00ffff`)
- **Notes Log**:
  - Border: `#333355`
  - Background: `#0f0f1f`
  - Text: Cyan (`#00ffff`)

### 7. Action Buttons
- **Base Style**:
  - Border: Solid cyan (`#00ffff`)
  - Background: `#1a1a2e`
  - Text: Cyan, bold

- **Success Button** (Start):
  - Border: Neon green (`#00ff00`)
  - Text: Neon green
  - Hover: Dark green background (`#002200`), bright green text (`#39ff14`)

- **Error Button** (Stop):
  - Border: Neon red (`#ff0044`)
  - Text: Neon red
  - Hover: Dark red background (`#220000`), lighter red text (`#ff2266`)

- **Warning Button** (Restart):
  - Border: Neon orange (`#ff6600`)
  - Text: Neon orange
  - Hover: Dark orange background (`#221100`), lighter orange text (`#ff8844`)

- **Primary Buttons** (Enable/Disable):
  - Border: Magenta (`#ff00ff`)
  - Text: Magenta
  - Hover: Dark magenta background (`#220022`), lighter magenta text (`#ff44ff`)

### 8. Event Log
- **Border**: Heavy cyan (`#00ffff`)
- **Background**: `#0f0f1f`
- **Text Color**: Cyan (`#00ffff`)
- **Success Messages**: Neon green (`#00ff00`)
- **Error Messages**: Neon red (`#ff0044`)

### 9. Scrollbars
- **Track Background**: `#1a1a2e`
- **Border**: Solid cyan (`#00ffff`)
- **Thumb**: Cyan (`#00ffff`)
- **Thumb Hover**: Magenta (`#ff00ff`)

---

## Visual Hierarchy

### Border Weight Strategy
Different panels use distinct border colors to create visual hierarchy:

1. **Cyan** (Overview Panel, Event Log): Primary information
2. **Magenta** (Service Table): Main data grid
3. **Green** (GPU Card): Hardware monitoring
4. **Gold** (Detail Panel): Selected item focus

All borders use `heavy` weight for maximum visual impact.

### Color-Coded Information
- **Status indicators**: Green (active), Orange (degraded), Red (inactive)
- **Button types**: Color-matched to action severity
- **Text highlights**: Cyan for data, Magenta for metrics, Gold for headers

---

## Accessibility Considerations

### Contrast Ratios
- **Dark backgrounds** (`#0a0e27`, `#1a1a2e`) provide high contrast with neon colors
- **Bright neon text** (`#00ffff`, `#00ff00`, `#ffd700`) ensures readability
- **Bold status text** improves visibility

### Color Blindness Support
- **Shape indicators**: Status shown via text ("ACTIVE", "INACTIVE") not just color
- **Multiple cues**: Border colors, text colors, and labels work together
- **High brightness**: Neon colors chosen for maximum visibility

### Terminal Compatibility
- Uses standard hex colors supported by modern terminals
- Heavy borders (`heavy`) provide clear visual separation
- Works well with both light and dark terminal themes
- Falls back gracefully on terminals with limited color support

---

## Before/After Comparison

### Before (Original Theme)
- Gray borders (`#3a3a3a`, `#333333`)
- No background colors (default terminal)
- Basic color names (`green`, `yellow`, `red`)
- Thin solid borders
- Minimal visual hierarchy

### After (Neon Theme)
- Vibrant neon borders (cyan, magenta, green, gold)
- Dark blue-black backgrounds for contrast
- Precise hex colors for consistent appearance
- Heavy borders for visual impact
- Clear color-coded hierarchy

---

## Implementation Notes

### CSS Styling
All styling is contained in the `CSS` class variable of `DashboardApp`.

Key Textual CSS features used:
- `border: heavy #color` - Thick neon borders
- `background: #color` - Dark panel backgrounds
- `color: #color` - Neon text colors
- `text-style: bold` - Emphasized text
- Pseudo-classes (`:hover`) for interactive feedback

### Rich Markup
Event log messages use Rich markup syntax:
```python
f"[#00ff00]✓ Success message[/]"
f"[#ff0044]✗ Error message[/]"
```

### Status Indicators
Status colors are applied using hex codes:
```python
status_style = {
    "active": "#00ff00 bold",
    "degraded": "#ff6600 bold",
    "inactive": "#ff0044 bold",
}
```

---

## Testing Notes

### Functional Testing
- ✅ Python syntax validation passed (`py_compile`)
- ✅ All imports successful
- ✅ Class definitions intact
- ✅ CSS parsing valid

### Visual Testing
Recommended testing scenarios:
1. **Active services**: Verify neon green status indicators
2. **Degraded services**: Verify neon orange warnings
3. **Inactive services**: Verify neon red alerts
4. **Row selection**: Verify cursor highlight with green text
5. **Button hover**: Verify hover state color transitions
6. **Event log**: Verify success/error message colors
7. **GPU monitoring**: Verify green border distinction

### Terminal Compatibility Testing
Test on various terminals:
- ✅ Modern terminals with 24-bit color support (recommended)
- ⚠️ Terminals with 256-color support (colors may vary slightly)
- ⚠️ Basic 16-color terminals (fallback to nearest colors)

---

## Usage

Run the enhanced dashboard:
```bash
python3 scripts/ai-dashboard
# or
./scripts/ai-dashboard
```

Key bindings remain unchanged:
- `r`: Manual refresh
- `q`: Quit
- `a`: Toggle auto-refresh
- `ctrl+l`: Clear event log

---

## Credits

**Theme**: Neon Cyberpunk
**Inspiration**: Blade Runner, Cyberpunk 2077, Tron
**Design Philosophy**: Maximum visibility, clear hierarchy, retro-futuristic aesthetics
