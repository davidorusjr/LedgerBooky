"""
main.py

This is the entry point of the Ledger Booky application.

Running this file:
    1. Creates the main application window (App, defined in ui.py).
    2. Loads inventory.csv and sales.csv automatically (handled inside
       the InventoryStore and SalesStore classes).
    3. Starts the Tkinter event loop, which keeps the window open and
       responding to clicks until the user closes it.

To run the program, open a terminal in this folder and type:
    python main.py
"""

from ui import App


def main() -> None:
    """Create and run the LedgerBooky application."""
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
