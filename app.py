import asyncio
import os
import traceback

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from playwright.async_api import async_playwright

app = FastAPI()

os.system("playwright install chromium")


# ---------------- LIVE LOG STORAGE ----------------
logs = []


def log(msg):
    print(msg)
    logs.append(msg)


# ---------------- UI ----------------
@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <html>
    <head>
        <title>Live Scraper Debug</title>
    </head>
    <body style="font-family:Arial;padding:20px;background:#111;color:#0f0;">

        <h2>LIVE SCRAPER CMD MODE</h2>

        <form action="/scrape" method="post">
            <input name="url" style="width:500px"><br><br>
            <input name="name"><br><br>
            <input name="episodes" type="number"><br><br>
            <button>START SCRAPING</button>
        </form>

        <hr>
        <h3>Live Logs:</h3>
        <pre id="logbox" style="background:#000;padding:10px;height:400px;overflow:auto;"></pre>

        <script>
            async function fetchLogs(){
                let r = await fetch('/logs');
                let d = await r.json();
                document.getElementById('logbox').innerText = d.logs.join("\\n");
            }
            setInterval(fetchLogs, 2000);
        </script>

    </body>
    </html>
    """


@app.get("/logs")
async def get_logs():
    return {"logs": logs}


# ---------------- SCRAPER ----------------
async def scrape_episode(page, ep_url):
    log(f"➡ Opening: {ep_url}")

    await page.goto(ep_url, wait_until="networkidle", timeout=60000)
    await page.wait_for_timeout(5000)

    data = {
        "Episode": "",
        "Title": "",
        "Details": []
    }

    try:
        title = await page.title()
        data["Title"] = title
        log(f"✔ Title: {title}")
    except:
        pass

    try:
        await page.wait_for_selector("body", timeout=20000)
    except:
        pass

    try:
        log("🔎 Looking for server buttons...")

        await page.wait_for_timeout(5000)

        buttons = await page.query_selector_all("li")

        log(f"✔ Found {len(buttons)} buttons")

        for i, btn in enumerate(buttons):
            try:
                name = (await btn.inner_text()).strip()
                if not name:
                    continue

                log(f"▶ Clicking server: {name}")

                await btn.click()
                await page.wait_for_timeout(5000)

                iframe = await page.query_selector("iframe")
                src = await iframe.get_attribute("src") if iframe else None

                if src:
                    log(f"✔ Found link: {src}")

                    data["Details"].append({
                        "Server": name,
                        "Url": src
                    })

            except Exception as e:
                log(f"✖ Error server: {str(e)}")

    except Exception as e:
        log(f"✖ Scrape error: {str(e)}")

    return data


async def scrape_all(url, name, episodes):
    slug = url.split("/watch/")[1].split("/")[0]

    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox"]
        )

        page = await browser.new_page()

        for ep in range(1, episodes + 1):
            ep_url = f"https://anikoto.cz/watch/{slug}/ep-{ep}"

            data = await scrape_episode(page, ep_url)

            data["Episode"] = f"1x{ep}"
            data["Title"] = f"{name} 1x{ep}"

            results.append(data)

        await browser.close()

    return results


# ---------------- ROUTE ----------------
@app.api_route("/scrape", methods=["POST"])
async def scrape(request: Request):
    try:
        form = await request.form()

        url = form.get("url")
        name = form.get("name")
        episodes = int(form.get("episodes"))

        logs.clear()
        log("🚀 STARTING SCRAPER...")
        log(f"📌 URL: {url}")
        log(f"📌 Episodes: {episodes}")

        data = await scrape_all(url, name, episodes)

        log("✅ DONE")

        return JSONResponse(data)

    except Exception as e:
        log("❌ ERROR OCCURRED")
        log(str(e))

        return JSONResponse({
            "error": str(e),
            "trace": traceback.format_exc()
        })


# ---------------- RENDER FIX ----------------
if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
