# Hugging Face Spaces Deployment Guide

This project is configured to be deployed as a **Docker Space** on Hugging Face. Since Hugging Face Spaces expose a single port (`7860`), both the Flask backend and the Streamlit frontend have been configured to run simultaneously inside a single Docker container.

## How to Deploy

1.  **Create a New Space**:
    - Go to [Hugging Face Spaces](https://huggingface.co/spaces) and click **Create new Space**.
    - Choose a name for your Space.
    - Select **Docker** as the Space SDK.
    - Choose the **Blank** Docker template.
    - Set the Space hardware (the free tier might be slow for heavy embedding models, so keep an eye on memory usage).
    - Choose visibility (Public or Private) and click **Create Space**.

2.  **Upload Files**:
    - Upload all the files from this repository directly into the Hugging Face Space repository.
    - You can do this via the web UI (Add file > Upload files) or by cloning the Space repository via Git and pushing your local code.
    - Make sure the `Dockerfile` and `run.sh` are in the root directory.

3.  **Set Secrets (Environment Variables)**:
    - Go to your Space's **Settings** tab.
    - Scroll down to the **Variables and secrets** section.
    - Add the following **Secrets** (do not add them as public variables if they contain sensitive keys):
        - `GOOGLE_API_KEY`: Your Google Gemini API Key.
        - `MONGO_URI`: Your MongoDB connection string.
        - `SECRET_KEY`: A strong random string for Flask sessions.
        - `DB_NAME`: The name of your MongoDB database (e.g. `gitlab_rag`).

4.  **Build and Run**:
    - Once the files are uploaded and secrets are set, Hugging Face will automatically start building the Docker image.
    - You can click on the **Logs** button to monitor the build process.
    - Once the build is successful, the Space will switch to **Running**, and your Streamlit app will load in the preview window!

## How It Works Under the Hood
- The `Dockerfile` creates a non-root user (UID 1000) which is explicitly required by Hugging Face Spaces.
- It copies the `requirements.txt` and installs the dependencies.
- It copies the rest of your application code and exposes port `7860`.
- The `Dockerfile` hands over execution to `run.sh`.
- The `run.sh` script starts the Flask server in the background on port `5000` and then starts the Streamlit frontend in the foreground on the required Hugging Face port `7860`. The two services communicate internally.
