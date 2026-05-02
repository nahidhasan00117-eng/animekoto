import asyncio
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, JSONResponse
from playwright.async_api import async_playwright

app = FastAPI()

# ---------------- UI PAGE ----------------
@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <html>
    <head>
        <title>Episode Scraper</title>
    </head>
    <body style="font-family:Arial; padding:20px;">
        <h2>Anime Episode Scraper</h2>

        <form action="/scrape" method="post">
            <p>Episode 1 Link:</p>
            <input name="url" style="width:500px" />

            <p>Series Name:</p>
            <input name="name" style="width:300px" />

            <p>Total Episodes:</p>
            <input name="episodes" type="number" />

            <br><br>
            <button type="submit">Scrape</button>
        </form>
    </body>
    </html>
    """

# ---------------- SCRAPER ----------------
async def scrape_all(url, name, episodes):
    slug = url.split("/watch/")[1].split("/")[0]

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox"]
        )

        page = await browser.new_page()
        results = []

        for ep in range(1, episodes + 1):
            ep_url = f"https://anikoto.cz/watch/{slug}/ep-{ep}"

            await page.goto(ep_url, wait_until="domcontentloaded")

            results.append({
                "episode": ep,
                "url": ep_url
            })

        await browser.close()
        return results

# ---------------- API ----------------
@app.post("/scrape")
async def scrape(url: str = Form(...), name: str = Form(...), episodes: int = Form(...)):
    data = await scrape_all(url, name, episodes)
    return JSONResponse({
        "name": name,
        "total": episodes,
        "data": data
    })
