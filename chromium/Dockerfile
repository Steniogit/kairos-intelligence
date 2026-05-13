FROM mcr.microsoft.com/playwright:v1.44.0-jammy
WORKDIR /app
RUN apt-get update && apt-get install -y python3-pip && pip3 install playwright crawl4ai && playwright install chromium && apt-get clean
CMD ["tail", "-f", "/dev/null"]
