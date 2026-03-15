# Use a standard Python slim image
FROM python:3.10-slim

# Install system dependencies if any are needed (e.g. for beautifulsoup/lxml)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Hugging Face Spaces specific setting: create a user with UID 1000
RUN useradd -m -u 1000 user

# Switch to the new user and set home directory and path
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Set the working directory inside the container
WORKDIR $HOME/app

# Copy the requirements file first to leverage Docker cache
COPY --chown=user:user requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY --chown=user:user . .

# Make sure the startup script is executable
RUN chmod +x run.sh

# Expose the standard Hugging Face Spaces port
EXPOSE 7860

# Command to run both backend and frontend via the shell script
CMD ["/bin/bash", "-c", "./run.sh"]
