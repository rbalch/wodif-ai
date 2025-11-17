FROM mcr.microsoft.com/playwright:latest as dev

# Set timezone to US Eastern
ENV TZ=America/New_York
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install essentials and development tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip \
    python-is-python3 \
    tzdata

RUN pip install playwright ollama requests
RUN playwright install --with-deps

WORKDIR /workspace
