"""
Hello Kitty BubbleTea TUI - Theme System
========================================

Implements the kawaii design principles and Hello Kitty color palette
from the design guide for a warm, cute, and accessible terminal interface.
"""

from typing import Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class ColorProfile(Enum):
    """Terminal color profile support levels."""
    MONOCHROME = "1-bit"
    ANSI_16 = "ansi-16"
    ANSI_256 = "ansi-256"
    TRUECOLOR = "truecolor"


@dataclass
class ColorToken:
    """Represents a color token with fallbacks for different profiles."""
    name: str
    hex: str
    ansi_256: int
    ansi_16: str
    usage: str


class HelloKittyTheme:
    """Hello Kitty themed color system with kawaii design principles."""
    
    def __init__(self):
        self.colors = self._initialize_colors()
        self.borders = self._get_border_styles()
        self.typography = self._get_typography_tokens()
        
    def _initialize_colors(self) -> Dict[str, ColorToken]:
        """Initialize the Hello Kitty-inspired color palette."""
        return {
            # Core Hello Kitty colors
            "hk_contour": ColorToken(
                name="Eerie Black",
                hex="#1E181A",
                ansi_256=236,
                ansi_16="black",
                usage="Text and borders for high-contrast legibility"
            ),
            "hk_primary": ColorToken(
                name="Spanish Crimson", 
                hex="#ED164F",
                ansi_256=197,
                ansi_16="bright_red",
                usage="Primary accent for actions and active states"
            ),
            "hk_accent": ColorToken(
                name="Vivid Yellow",
                hex="#FFE700", 
                ansi_256=226,
                ansi_16="yellow",
                usage="Secondary accent for highlights and labels"
            ),
            "hk_secondary": ColorToken(
                name="Hello Kitty Blue",
                hex="#0054AE",
                ansi_256=25,
                ansi_16="blue", 
                usage="Secondary accent for info or alternative emphasis"
            ),
            
            # Background colors
            "hk_bg": ColorToken(
                name="Pure White",
                hex="#FFFFFF",
                ansi_256=15,
                ansi_16="white",
                usage="Base background for light theme surfaces"
            ),
            "hk_text": ColorToken(
                name="Text Black",
                hex="#1E181A", 
                ansi_256=236,
                ansi_16="black",
                usage="Default text color on light backgrounds"
            ),
            
            # Kawaii pastel palette
            "pastel_pink": ColorToken(
                name="Soft Pink",
                hex="#F8BBD0",
                ansi_256=225,
                ansi_16="white",
                usage="Gentle accent for subtle headers and badges"
            ),
            "pastel_mint": ColorToken(
                name="Mint Green", 
                hex="#B2E3C6",
                ansi_256=157,
                ansi_16="cyan",
                usage="Soft highlight for alternate row striping"
            ),
            "pastel_sky": ColorToken(
                name="Sky Blue",
                hex="#B3E5FC", 
                ansi_256=159,
                ansi_16="cyan",
                usage="Calm accent for info callouts"
            ),
            "pastel_butter": ColorToken(
                name="Butter Yellow",
                hex="#FFF6C2",
                ansi_256=230,
                ansi_16="white", 
                usage="Warm light for popover backgrounds"
            ),
            "pastel_lilac": ColorToken(
                name="Lavender",
                hex="#D6C8FF",
                ansi_256=189,
                ansi_16="magenta",
                usage="Dreamy accent for secondary labels"
            ),
            
            # Bubble tea specific colors
            "taro_purple": ColorToken(
                name="Taro Purple",
                hex="#9B59B6",
                ansi_256=135,
                ansi_16="magenta",
                usage="Taro milk tea color representation"
            ),
            "matcha_green": ColorToken(
                name="Matcha Green",
                hex="#27AE60", 
                ansi_256=34,
                ansi_16="green",
                usage="Matcha milk tea color representation"
            ),
            "thai_orange": ColorToken(
                name="Thai Tea Orange",
                hex="#E67E22",
                ansi_256=208,
                ansi_16="bright_yellow",
                usage="Thai tea color representation"
            ),
            "brown_sugar": ColorToken(
                name="Brown Sugar",
                hex="#8B4513",
                ansi_256=130,
                ansi_16="yellow",
                usage="Brown sugar milk tea color representation"
            ),
            "milk_cream": ColorToken(
                name="Milk Cream",
                hex="#F5F5DC",
                ansi_256=230,
                ansi_16="white",
                usage="Classic milk tea cream color"
            )
        }
    
    def _get_border_styles(self) -> Dict[str, str]:
        """Get kawaii-friendly border styles."""
        return {
            "rounded": "╭─╮│╰───╯",  # Rounded corners for cards and badges
            "normal": "┌─┐│└─┘",     # Clean minimal lines for subtle separators
            "thick": "╔═╗║╚═╝",      # High-visibility for section headers
            "double": "╔═╗║╠═╣║╚═╝",  # Formal boundaries for hero panels
            "kawaii_heart": "♥─────♥"  # Special kawaii accent border
        }
    
    def _get_typography_tokens(self) -> Dict[str, Dict[str, str]]:
        """Get typography styling tokens for kawaii design."""
        return {
            "title": {
                "color": "hk_primary",
                "weight": "bold",
                "size": "large"
            },
            "subtitle": {
                "color": "hk_secondary", 
                "weight": "normal",
                "size": "medium"
            },
            "body": {
                "color": "hk_text",
                "weight": "normal",
                "size": "normal"
            },
            "accent": {
                "color": "hk_accent",
                "weight": "bold",
                "size": "normal"
            },
            "muted": {
                "color": "pastel_lilac",
                "weight": "normal", 
                "size": "small"
            }
        }
    
    def get_color(self, token_name: str, profile: ColorProfile = ColorProfile.TRUECOLOR) -> str:
        """Get color value for a token in the specified profile."""
        if token_name not in self.colors:
            return self.colors["hk_text"].hex
        
        color_token = self.colors[token_name]
        
        if profile == ColorProfile.TRUECOLOR:
            return color_token.hex
        elif profile == ColorProfile.ANSI_256:
            return f"color({color_token.ansi_256})"
        elif profile == ColorProfile.ANSI_16:
            return color_token.ansi_16
        else:  # MONOCHROME
            # Return black or white based on context
            if token_name.endswith("_bg"):
                return "white"
            return "black"
    
    def get_kawaii_sparkle(self) -> str:
        """Get a kawaii sparkle character."""
        return "✦"
    
    def get_kawaii_heart(self) -> str:
        """Get a kawaii heart character."""
        return "♥"
    
    def get_bubble_tea_icons(self) -> Dict[str, str]:
        """Get bubble tea drink and topping icons."""
        return {
            # Drinks
            "taro_milk_tea": "🟣",
            "matcha_milk_tea": "🟢", 
            "thai_tea": "🟠",
            "brown_sugar_milk": "🟤",
            "milk_tea": "🥛",
            "fruit_tea_mango": "🥭",
            "fruit_tea_strawberry": "🍓",
            "fruit_tea_grape": "🍇",
            "fruit_tea_apple": "🍎",
            
            # Toppings  
            "tapioca_pearls": "●",
            "golden_pearls": "◎",
            "popping_boba": "◉",
            "grass_jelly": "▮",
            "aloe_vera": "▯",
            "pudding": "▢",
            "red_bean": "●",
            "taro_balls": "◎",
            "cheese_foam": "~"
        }
    
    def get_component_style(self, component_type: str) -> Dict[str, str]:
        """Get styling for specific UI components following kawaii principles."""
        styles = {
            "button_primary": {
                "background": "hk_primary",
                "color": "hk_bg",
                "border": "rounded",
                "padding": "1 2"
            },
            "button_secondary": {
                "background": "pastel_pink",
                "color": "hk_text", 
                "border": "rounded",
                "padding": "1 2"
            },
            "card": {
                "background": "pastel_sky",
                "border": "rounded",
                "padding": "2",
                "margin": "1"
            },
            "badge": {
                "background": "pastel_butter",
                "border": "rounded", 
                "padding": "0 1"
            },
            "alert_info": {
                "background": "pastel_sky",
                "border": "thick",
                "padding": "1"
            },
            "alert_success": {
                "background": "pastel_mint",
                "border": "thick",
                "padding": "1"
            }
        }
        
        return styles.get(component_type, {})
    
    def apply_dark_theme_adaptation(self, is_dark_theme: bool) -> Dict[str, str]:
        """Apply dark theme adaptations using adaptive color principles."""
        if not is_dark_theme:
            return {}
            
        return {
            "hk_text": "#F2F2F2",  # Light text on dark background
            "hk_contour": "#BFBFBF",  # Softer contour for dark theme
            "hk_primary": "#FF5C8A",  # Brighter primary for dark theme
            "pastel_pink_bg": "#613743"  # Dark variant of pastel pink
        }
