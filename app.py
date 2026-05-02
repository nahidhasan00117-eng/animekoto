import asyncio
import os
import traceback

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from playwright.async_api import async_playwright

app = FastAPI()

os.system("playwright install chromium")


# ---------------- UI ----------------
@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <html>
    <body style="font-family:Arial;padding:20px;">
        <h2>Anime Full Scraper (Server Links)</h2>

        <form action="/scrape" method="post">
            <input name="url" placeholder="Episode 1 URL" style="width:500px"><br><br>
            <input name="name" placeholder="Name"><br><br>
            <input name="episodes" type="number" placeholder="Episodes"><br><br>
            <button>Scrape</button>
        </form>
    </body>
    </html>
    """


# ---------------- SCRAPER CORE ----------------
async def scrape_episode(page, ep_url):
    await page.goto(ep_url, wait_until="domcontentloaded", timeout=60000)

    await asyncio.sleep(2)

    episode_data = {
        "Episode": "",
        "Title": "",
        "Details": []
    }

    # Episode title
    try:
        title = await page.title()
        episode_data["Title"] = title
    except:
        episode_data["Title"] = "Unknown"

    # Detect server blocks
    try:
        server_sections = await page.query_selector_all(".servers .type")

        for section in server_sections:

            label = await section.query_selector("label")
            label_text = await label.inner_text() if label else "SUB"
            category = "DUB" if "DUB" in label_text.upper() else "SUB"

            buttons = await section.query_selector_all("li:not(.download-icon)")

            for btn in buttons:
                server_name = (await btn.inner_text()).strip()

                await btn.click()
                await asyncio.sleep(2)

                iframe = await page.query_selector("#player iframe")
                src = await iframe.get_attribute("src") if iframe else None

                if src:
                    episode_data["Details"].append({
                        "Category": category,
                        "Server": server_name,
                        "Url": src.split("?")[0]
                    })

    except Exception:
        pass

    return episode_data


# ---------------- MAIN SCRAPER ----------------
async def scrape_all(url, name, episodes):
    slug = url.split("/watch/")[1].split("/")[0]

    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )

        page = await browser.new_page()

        for ep in range(1, episodes + 1):
            ep_url = f"https://anikoto.cz/watch/{slug}/ep-{ep}"

            try:
                data = await scrape_episode(page, ep_url)

                data["Episode"] = f"1x{ep}"
                data["Title"] = f"{name} 1x{ep}"

                results.append(data)

            except Exception as e:
                results.append({
                    "Episode": f"1x{ep}",
                    "error": str(e)
                })

        await browser.close()

    return results


# ---------------- ROUTE ----------------
@app.api_route("/scrape", methods=["GET", "POST"])
async def scrape(request: Request):
    try:
        if request.method == "GET":
            return {"error": "Use form on homepage"}

        form = await request.form()

        url = form.get("url")
        name = form.get("name")
        episodes = int(form.get("episodes"))

        data = await scrape_all(url, name, episodes)

        return JSONResponse(data)

    except Exception as e:
        return JSONResponse({
            "error": str(e),
            "trace": traceback.format_exc()
        })


# ---------------- RENDER FIX ----------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
