import asyncio
import os
import traceback

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from playwright.async_api import async_playwright

app = FastAPI()

# ---------------- AUTO FIX PLAYWRIGHT BROWSER ----------------
# This fixes "Executable doesn't exist" on Render
os.system("playwright install chromium")


# ---------------- HOME PAGE ----------------
@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <html>
    <head>
        <title>Anime Scraper Tool</title>
    </head>
    <body style="font-family:Arial;padding:20px;">
        <h2>Anime Episode Scraper</h2>

        <form action="/scrape" method="post">
            <p>Episode 1 URL:</p>
            <input name="url" style="width:500px" required />

            <p>Series Name:</p>
            <input name="name" style="width:300px" required />

            <p>Total Episodes:</p>
            <input name="episodes" type="number" required />

            <br><br>
            <button type="submit">Scrape</button>
        </form>
    </body>
    </html>
    """


# ---------------- SCRAPER FUNCTION ----------------
async def scrape_all(url: str, name: str, episodes: int):
    slug = url.split("/watch/")[1].split("/")[0]

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )

        page = await browser.new_page()
        results = []

        for ep in range(1, episodes + 1):
            ep_url = f"https://anikoto.cz/watch/{slug}/ep-{ep}"

            try:
                await page.goto(ep_url, wait_until="domcontentloaded", timeout=60000)

                results.append({
                    "episode": ep,
                    "url": ep_url
                })

            except Exception as e:
                results.append({
                    "episode": ep,
                    "error": str(e)
                })

        await browser.close()
        return results


# ---------------- SCRAPE ROUTE (FIXED GET + POST) ----------------
@app.api_route("/scrape", methods=["GET", "POST"])
async def scrape(request: Request):
    try:
        # If opened directly in browser
        if request.method == "GET":
            return {
                "status": "error",
                "message": "Open homepage (/) and use the form"
            }

        form = await request.form()

        url = form.get("url")
        name = form.get("name")
        episodes = int(form.get("episodes"))

        data = await scrape_all(url, name, episodes)

        return JSONResponse({
            "status": "success",
            "name": name,
            "total_episodes": episodes,
            "data": data
        })

    except Exception as e:
        return JSONResponse({
            "status": "error",
            "message": str(e),
            "trace": traceback.format_exc()
        })


# ---------------- RENDER START FIX ----------------
if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
