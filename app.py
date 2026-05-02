import asyncio
from fastapi import FastAPI
from playwright.async_api import async_playwright

app = FastAPI()

async def scrape(series_slug, series_name, total_episodes):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox"]
        )

        page = await browser.new_page()
        results = []

        for ep in range(1, total_episodes + 1):
            url = f"https://anikoto.cz/watch/{series_slug}/ep-{ep}"
            await page.goto(url, wait_until="domcontentloaded")

            results.append({
                "episode": ep,
                "url": url
            })

        await browser.close()
        return results


@app.get("/scrape")
async def run(url: str, name: str, episodes: int):
    slug = url.split("/watch/")[1].split("/")[0]
    data = await scrape(slug, name, episodes)
    return {"data": data}