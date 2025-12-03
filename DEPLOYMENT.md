# Deployment Guide

Your application is ready for deployment!

## Files Prepared
- **`ncr_app.py`**: Main application file.
- **`requirements.txt`**: Dependencies (`streamlit`, `pandas`, `plotly`).
- **`README.md`**: Project documentation.

## Steps to Deploy to Streamlit Cloud

1.  **Push to GitHub**:
    - Initialize a git repository: `git init`
    - Add files: `git add .`
    - Commit: `git commit -m "Initial commit"`
    - Create a new repository on GitHub.
    - Push your code:
      ```bash
      git remote add origin <your-repo-url>
      git push -u origin main
      ```

2.  **Deploy on Streamlit Cloud**:
    - Go to [share.streamlit.io](https://share.streamlit.io/).
    - Click **"New app"**.
    - Select your GitHub repository.
    - Verify settings:
        - **Main file path**: `ncr_app.py`
    - Click **"Deploy!"**.

## Troubleshooting
- If the build fails, check the logs on Streamlit Cloud.
- Ensure `requirements.txt` is in the root directory.
