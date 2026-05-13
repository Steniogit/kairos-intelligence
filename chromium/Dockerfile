FROM mcr.microsoft.com/playwright:v1.44.0-jammy

WORKDIR /app

RUN pip install playwright crawl4ai && playwright install chromium

CMD ["tail", "-f", "/dev/null"]
