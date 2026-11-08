"""
Firestarter - Time Passage Engine & Temporal Fast-Forward
Implements Section 4.2 Time Passage Engine ('T' key).
"""

from typing import List, Dict, Any, Callable

class TimeSkipOption:
    def __init__(self, label: str, hours: float, description: str):
        self.label = label
        self.hours = hours
        self.description = description

TIME_SKIP_OPTIONS: List[TimeSkipOption] = [
    TimeSkipOption("1 Hour", 1.0, "Short rest. Ambient fire coals settle."),
    TimeSkipOption("6 Hours", 6.0, "Night pass. Morning mist rises, ground dampens."),
    TimeSkipOption("24 Hours (1 Day)", 24.0, "Full day-night cycle. Noticeable surface drying on racks."),
    TimeSkipOption("7 Days (1 Week)", 168.0, "Weekly weathering. Dirt logs absorb ground moisture."),
    TimeSkipOption("30 Days (1 Month)", 720.0, "Monthly progression. Wood begins seasoning."),
    TimeSkipOption("60 Days (Cure Period)", 1440.0, "Ideal curing duration. Tarped logs reach ~12% EMC."),
    TimeSkipOption("90 Days (1 Season)", 2160.0, "Full seasonal transition. Ground logs decay to punk wood.")
]

class TimeEngine:
    def __init__(self):
        self.is_menu_open = False
        self.selected_option_index = 2 # default 1 Day
        self.total_days_elapsed = 0.0

    def toggle_menu(self) -> bool:
        self.is_menu_open = not self.is_menu_open
        return self.is_menu_open

    def next_option(self):
        self.selected_option_index = (self.selected_option_index + 1) % len(TIME_SKIP_OPTIONS)

    def prev_option(self):
        self.selected_option_index = (self.selected_option_index - 1) % len(TIME_SKIP_OPTIONS)

    def execute_selected_skip(self, on_skip_callback: Callable[[float], None]) -> Dict[str, Any]:
        """Advances simulation by selected time skip option."""
        opt = TIME_SKIP_OPTIONS[self.selected_option_index]
        days = opt.hours / 24.0
        self.total_days_elapsed += days
        
        # Invoke callback to advance weather, racks, ecosystem, and combustion bodies
        on_skip_callback(opt.hours)
        
        self.is_menu_open = False
        return {
            "label": opt.label,
            "hours": opt.hours,
            "days": days,
            "message": f"Advanced time by {opt.label}. {opt.description}"
        }
