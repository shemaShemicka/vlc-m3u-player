import asyncio
import aiohttp
import re
from pathlib import Path

INPUT_FILE = "MacDataBase.txt"
OUTPUT_M3U = "playlist.m3u"

async def fetch_channels(session, portal, mac):
    url = f"{portal.strip()}/action.php?type=itv&action=get_all_channels"
    headers = {
        "User-Agent": "Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG200 sb.711 Safari/533.3",
        "X-User-MAC": mac.strip(),
        "Cookie": f"mac={mac.strip()}"
    }
    try:
        async with session.get(url, headers=headers, timeout=15) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("js", []), portal
    except:
        return [], portal
    return [], portal

async def main():
    if not Path(INPUT_FILE).exists(): return
    
    entries = []
    with open(INPUT_FILE, "r") as f:
        for line in f:
            if "|" in line:
                # Го чистиме форматот http://url|MAC
                clean_line = re.sub(r"\", "", line).strip()
                parts = clean_line.split("|")
                if len(parts) == 2:
                    entries.append((parts[0], parts[1]))

    async with aiohttp.ClientSession() as session:
        tasks = [fetch_channels(session, p, m) for p, m in entries]
        results = await asyncio.gather(*tasks)

    with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for channels, portal in results:
            for ch in channels:
                name = ch.get("name", "Unknown")
                cmd = ch.get("cmd", "")
                # Чистење на стрим линкот
                stream = re.sub(r"^(ffmpeg|ffrt)\s+", "", cmd).strip()
                if stream:
                    f.write(f'#EXTINF:-1 group-title="{portal}", {name}\n{stream}\n')

if __name__ == "__main__":
    asyncio.run(main())
