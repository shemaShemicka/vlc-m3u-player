import asyncio
import aiohttp
import re
import json
from pathlib import Path

INPUT_FILE = "MacDataBase.txt"
OUTPUT_M3U = "playlist.m3u"

async def fetch_channels(session, portal, mac):
    # Ги чистиме URL-то и MAC-от од празни места
    p_url = portal.strip().rstrip('/')
    m_addr = mac.strip()
    
    target = f"{p_url}/action.php?type=itv&action=get_all_channels"
    headers = {
        "User-Agent": "Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG200 sb.711 Safari/533.3",
        "X-User-MAC": m_addr,
        "Cookie": f"mac={m_addr}"
    }
    
    try:
        async with session.get(target, headers=headers, timeout=15) as response:
            if response.status == 200:
                text_data = await response.text()
                data = json.loads(text_data)
                return data.get("js", []), portal
    except Exception:
        return [], portal
    return [], portal

async def main():
    input_path = Path(INPUT_FILE)
    if not input_path.exists():
        print(f"Грешка: {INPUT_FILE} не е пронајден!")
        return
    
    entries = []
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if "|" in line:
                # Овој Regex го трга и секаков текст пред http
                match = re.search(r"(https?://[^|]+)\|([0-9A-Fa-f:]+)", line)
                if match:
                    entries.append((match.group(1), match.group(2)))

    if not entries:
        print("Не се пронајдени валидни портали во листата.")
        return

    async with aiohttp.ClientSession() as session:
        tasks = [fetch_channels(session, p, m) for p, m in entries]
        results = await asyncio.gather(*tasks)

    with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        channel_count = 0
        for channels, portal in results:
            if not channels: continue
            for ch in channels:
                name = ch.get("name", "Unknown")
                cmd = ch.get("cmd", "")
                # Чистење на стрим линкот од вишоци
                stream = cmd.replace("ffrt ", "").replace("ffmpeg ", "").strip()
                if stream:
                    f.write(f'#EXTINF:-1 group-title="{portal}", {name}\n{stream}\n')
                    channel_count += 1
        
        print(f"Завршено! Генерирани се {channel_count} канали.")

if __name__ == "__main__":
    asyncio.run(main())
