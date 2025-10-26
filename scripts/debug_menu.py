#!/usr/bin/env python3
"""Debug test for menu text formatting."""
items = ["Services", "Performance", "Actions", "Help"]
for idx, item in enumerate(items):
    print(f"Test {idx}: '{item}'")
    # Fixed: Simplified menu text generation to avoid nested f-string issues
    items_str = ", ".join([f'"{i}"' for i in items])
    menu_text = f"Menu: [{items_str}] - Currently: 1"
    print(f"Result: {menu_text}")
    expected = "Menu: {'Services': 'Services', 'Performance': 'Performance', 'Actions': 'Actions', 'Help': 'Help'}[1] - Currently: 1"
    print(f"Expected: {expected}")
