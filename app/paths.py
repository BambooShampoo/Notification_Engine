# paths.py
"""Create a paths.py (or add to config.py) with a BASE_DIR that resolves correctly whether running as a script or as a frozen exe: use os.path.dirname(sys.executable) when sys.
frozen is True, otherwise os.path.dirname(os.path.abspath(__file__)). 
Build DATA_DIR, DB_PATH, and the .env path off this BASE_DIR."""

