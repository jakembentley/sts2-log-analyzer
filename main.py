"""STS2 Log Analyzer — entry point."""
import sys
import os

# Ensure project root is on sys.path when running directly
sys.path.insert(0, os.path.dirname(__file__))

from gui.app import App

if __name__ == "__main__":
    app = App()
    app._schedule_live_check()
    app.mainloop()
