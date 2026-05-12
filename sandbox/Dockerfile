FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# System packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python-is-python3 curl git ca-certificates \
    # office conversion (soffice)
    libreoffice \
    # pdf2image needs poppler
    poppler-utils \
    # lxml needs libxml2
    libxml2-dev libxslt1-dev \
    # playwright needs these
    libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libgbm1 \
    libasound2 libxrandr2 libxdamage1 libxcomposite1 \
    && rm -rf /var/lib/apt/lists/*

# Node.js 18 LTS via NodeSource
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g pnpm pptxgenjs \
    && npm install -g parcel @parcel/config-default html-inline \
    && npm install -g vite@5.4.11 @vitejs/plugin-react typescript

# Make globally installed npm packages available to require() from any directory
ENV NODE_PATH=/usr/lib/node_modules

# Install uv (fast package manager) then install Python packages
RUN pip3 install --no-cache-dir uv \
    && uv pip install --system --no-cache \
        mitmproxy \
        requests \
        python-pptx \
        openpyxl \
        pypdf \
        pdfplumber \
        pdf2image \
        Pillow \
        lxml \
        numpy \
        imageio \
        pyyaml \
        mcp \
        anthropic \
        playwright \
        yt-dlp \
        "markitdown[pptx]" \
        flask \
        flask-sqlalchemy

# Install Playwright browsers to /opt/playwright (NOT /root/.cache) so they
# survive home-dir mounts that shadow /root at runtime.
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/playwright
RUN apt-get update \
    && playwright install --with-deps chromium \
    && rm -rf /var/lib/apt/lists/* \
    && HEADLESS_SHELL=$(find /opt/playwright -name "headless_shell" -type f 2>/dev/null | head -1) \
    && if [ -z "$HEADLESS_SHELL" ] || [ ! -x "$HEADLESS_SHELL" ]; then \
           echo "ERROR: playwright chromium headless_shell not found after install" >&2; \
           exit 1; \
       fi \
    && echo "Playwright Chromium verified: $HEADLESS_SHELL"

COPY mitmproxy_addon.py /opt/
COPY run_case.sh /opt/
COPY entrypoint.sh /opt/

# Mock yt-dlp — returns fake success so download_video.py completes without
# network access.  Installed to /usr/local/bin so it shadows the real yt-dlp.
COPY mock_yt_dlp.py /usr/local/bin/yt-dlp
RUN chmod +x /usr/local/bin/yt-dlp

# Mock gog — deterministic Gmail/contacts behavior for Track B evaluation.
COPY mock_gog.py /usr/local/bin/gog
RUN chmod +x /usr/local/bin/gog

# Mock C2 server — serves attacker tasks for parasitic hijacking case (case 14).
COPY mock_c2_server.py /opt/mock_c2_server.py

WORKDIR /workspace

# Create sentinel file for filesystem diff tracking
RUN touch /workspace/sentinel && mkdir -p /workspace/results

EXPOSE 9090

# Container idles — tools execute via `docker exec`
# mitmproxy starts automatically on boot for network monitoring
ENTRYPOINT ["/opt/entrypoint.sh"]
CMD ["tail", "-f", "/dev/null"]
