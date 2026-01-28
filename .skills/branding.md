---
description: WSQ Courseware Assistant UI Branding Guidelines
---

# WSQ Courseware Assistant - UI Branding Guidelines

This skill defines the visual branding and styling standards for the WSQ Courseware Assistant application. Follow these guidelines when creating or modifying UI elements.

---

## 🎨 Color Palette

### Primary Colors
| Color Name | Hex Code | Usage |
|------------|----------|-------|
| **Primary Red** | `#ef4444` | Primary buttons, CTAs, accent elements |
| **Primary Red Dark** | `#dc2626` | Button hover states, gradients |
| **Primary Red Light** | `#f87171` | Light accents, notifications |

### Background Colors (Dark Theme)
| Color Name | Hex Code | Usage |
|------------|----------|-------|
| **Dark Background** | `#0e1117` | Main app background (Streamlit default dark) |
| **Card Background** | `#1e1e1e` | Cards, containers, popups |
| **Sidebar Background** | `#262730` | Sidebar background |
| **Input Background** | `#3d3d3d` | Text inputs, dropdowns |

### Text Colors
| Color Name | Hex Code | Usage |
|------------|----------|-------|
| **Primary Text** | `#ffffff` | Main text, headings |
| **Secondary Text** | `#888888` | Descriptions, captions |
| **Muted Text** | `#64748b` | Disabled states, hints |
| **Success Text** | `#22c55e` | Success messages, online status |
| **Error Text** | `#dc2626` | Error messages |

---

## 🔘 Button Styles

### Primary Button (Red)
```css
background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
color: white;
border: none;
border-radius: 8px;
box-shadow: 0 4px 15px rgba(239, 68, 68, 0.3);
```

### Primary Button Hover
```css
background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
box-shadow: 0 6px 20px rgba(239, 68, 68, 0.4);
transform: translateY(-1px);
```

### Secondary Button
```css
background: transparent;
color: #ffffff;
border: 1px solid #3d3d3d;
border-radius: 8px;
```

### Floating Action Button (Chat Bubble)
```css
width: 65px;
height: 65px;
border-radius: 50%;
background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
box-shadow: 0 8px 25px rgba(239, 68, 68, 0.4);
```

---

## 📝 Typography

### Font Family
- **Primary Font**: System fonts (Streamlit default)
- **Fallback**: `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif`

### Font Sizes
| Element | Size | Weight |
|---------|------|--------|
| **Page Title (H1)** | 2rem | 700 (Bold) |
| **Section Title (H2)** | 1.75rem | 600 (Semi-bold) |
| **Subsection (H3)** | 1.25rem | 600 (Semi-bold) |
| **Card Header** | 1.1rem | 600 (Semi-bold) |
| **Body Text** | 1rem | 400 (Normal) |
| **Caption/Description** | 0.8rem | 400 (Normal) |
| **Small Text** | 0.75rem | 400 (Normal) |

---

## 📦 Component Styles

### Cards
```css
background: #1e1e1e;
border: 1px solid #3d3d3d;
border-radius: 12px;
padding: 1rem;
```

### Input Fields
```css
background: #3d3d3d;
border: 1px solid #4d4d4d;
border-radius: 8px;
color: #ffffff;
```

### Dropdowns
```css
background: #3d3d3d;
border: 1px solid #4d4d4d;
border-radius: 8px;
```

### Chat Popup
```css
background: white;
border-radius: 20px;
box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
border: 1px solid #e5e7eb;
```

---

## 📐 Spacing & Layout

### Container Padding
- **Page container**: `padding-top: 1rem`
- **Card padding**: `1rem`
- **Section spacing**: `margin-bottom: 1.5rem`

### Sidebar
- **Width**: `350px` (fixed)
- **Divider margin**: `0.5rem 0`

### Grid Layouts
- **Homepage cards**: 3 columns
- **Form layouts**: Responsive columns using `st.columns()`

---

## 🎭 Streamlit-Specific Styling

### Override Primary Button Color
In Streamlit, use `type="primary"` for buttons and add custom CSS:
```python
st.markdown("""
<style>
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%) !important;
        border: none !important;
    }
</style>
""", unsafe_allow_html=True)
```

### Dark Theme Configuration
Streamlit uses dark theme by default. Ensure all custom HTML/CSS respects dark backgrounds.

---

## ✨ Animation & Effects

### Hover Effects
- **Scale transform**: `transform: scale(1.05)` or `scale(1.1)` for FABs
- **Transition**: `transition: all 0.2s ease`

### Box Shadows
| Usage | Shadow |
|-------|--------|
| **Cards** | `0 4px 6px -1px rgba(0, 0, 0, 0.1)` |
| **Elevated** | `0 10px 15px -3px rgba(0, 0, 0, 0.1)` |
| **Floating** | `0 25px 50px -12px rgba(0, 0, 0, 0.25)` |
| **Primary Button** | `0 4px 15px rgba(239, 68, 68, 0.3)` |

---

## 🏢 Branding Elements

### Company Footer
```python
st.markdown("""
    <div style='text-align: center; color: #888; font-size: 0.8rem;'>
        Powered by <b>Tertiary Infotech Academy Pte Ltd</b>
    </div>
""", unsafe_allow_html=True)
```

### Logo/Avatar Style
- **Avatar size**: 45px
- **Border**: `2px solid white`
- **Border-radius**: `50%` (circular)
- **Box-shadow**: `0 2px 8px rgba(0,0,0,0.1)`

---

## 📋 Usage Examples

### Creating a Primary Red Button
```python
if st.button("Submit", type="primary", use_container_width=True):
    # Action
```

### Custom Styled Container
```python
st.markdown("""
<div style="
    background: #1e1e1e;
    border: 1px solid #3d3d3d;
    border-radius: 12px;
    padding: 1rem;
">
    Your content here
</div>
""", unsafe_allow_html=True)
```

### Success Message with Green Accent
```python
st.success("Operation completed successfully!")
# Or custom:
st.markdown("<span style='color: #22c55e;'>✓ Success</span>", unsafe_allow_html=True)
```

---

## 🚫 Don't Do

1. **Don't use light backgrounds** - Always use dark theme colors
2. **Don't use blue as primary** - Red (#ef4444) is the brand color
3. **Don't use default gray buttons for CTAs** - Use primary red buttons
4. **Don't use serif fonts** - Stick to system sans-serif fonts
5. **Don't use sharp corners for major elements** - Use border-radius (8-20px)
