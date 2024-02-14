FROM python:3.11-slim-bookworm

# Update and install dependencies
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        software-properties-common gnupg2 curl\
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set environment variable if needed
# ENV OPENAI_API_KEY="{OpenAI-API-Key}"

# Install Python packages
RUN pip install --upgrade pip
RUN pip install pyautogen[teachable,lmm,retrievechat,mathchat,blendsearch] autogenra
RUN pip install numpy pandas matplotlib seaborn scikit-learn requests urllib3 nltk pillow pytest beautifulsoup4 pytest-playwright
RUN playwright install
RUN playwright install-deps

# Start Command
CMD ["/bin/bash"]