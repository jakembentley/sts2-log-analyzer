"""Color palette, fonts, and layout constants."""

# Window
WIN_WIDTH = 1280
WIN_HEIGHT = 800
WIN_MIN_WIDTH = 1000
WIN_MIN_HEIGHT = 600

SIDEBAR_WIDTH = 200

# Colors — dark theme
BG_DARK    = "#1a1a2e"
BG_PANEL   = "#16213e"
BG_CARD    = "#0f3460"
BG_HOVER   = "#1a4a80"
ACCENT     = "#e94560"
ACCENT2    = "#4cc9f0"
TEXT       = "#e0e0e0"
TEXT_DIM   = "#888888"
TEXT_WIN   = "#4ade80"
TEXT_LOSS  = "#f87171"
TEXT_GOLD  = "#fbbf24"

# Fonts
FONT_TITLE   = ("Segoe UI", 22, "bold")
FONT_HEADING = ("Segoe UI", 14, "bold")
FONT_BODY    = ("Segoe UI", 12)
FONT_SMALL   = ("Segoe UI", 10)
FONT_MONO    = ("Consolas", 11)

# matplotlib figure background — matches dark theme
MPL_BG      = "#16213e"
MPL_FG      = "#e0e0e0"
MPL_GRID    = "#2a2a4a"
MPL_BAR     = "#4cc9f0"
MPL_BAR2    = "#e94560"

# Outcome colors
OUTCOME_COLOR = {
    "WIN": TEXT_WIN,
    "LOSS": TEXT_LOSS,
    "UNKNOWN": TEXT_DIM,
}
