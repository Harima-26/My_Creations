import sys
import os

# Add the inferred site-packages path where dependencies were installed
site_packages = r"C:\Users\SMILE\AppData\Roaming\Python\Python314\site-packages"
if site_packages not in sys.path:
    sys.path.append(site_packages)
    print(f"Added {site_packages} to sys.path")

try:
    from streamlit.web import cli as stcli
except ImportError as e:
    print(f"Could not import streamlit: {e}")
    print("sys.path:")
    print(sys.path)
    sys.exit(1)

if __name__ == "__main__":
    sys.argv = ["streamlit", "run", "app.py", "--server.headless=true"]
    sys.exit(stcli.main())
