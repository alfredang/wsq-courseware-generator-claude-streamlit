Clear all Streamlit cache, kill ALL running Streamlit processes, and start a fresh Streamlit instance using the uv .venv environment.

Steps:
1. Clear Streamlit cache by removing the `.streamlit/cache` directory if it exists
2. Kill ALL running `streamlit` processes using `pkill -f streamlit` (ensures no orphan instances)
3. Wait 1 second for processes to terminate
4. Start `uv run streamlit run app.py` in the background (this ensures the .venv environment and all dependencies are used)
5. Wait 3 seconds for the app to initialize
6. Auto-open the browser at http://localhost:7860 using `open http://localhost:7860` (macOS)
7. Confirm the app is running and show the URL: http://localhost:7860
