import asyncio
import aiohttp
import re
import json
from pathlib import Path

INPUT_FILE = "MacDataBase.txt"
OUTPUT_M3U = "playlist.m3u"

async def fetch_channels(session, portal, mac):
    # Чистење на URL и MAC
    p_url = portal.strip().rstrip('/')
    # Тргање на "/c" од крајот на URL-то ако постои
    p_url = re.sub(r'/c$', '', p_url)
    m_addr = mac.strip()
    
    # Листа на можни патеки за Stalker/Ministra API
    paths = [
        "/portal.php?type=itv&action=get_all_channels",
        "/stalker_portal/server/load.php?type=itv&action=get_all_channels",
        "/server/load.php?type=itv&action=get_all_channels"
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG200 sb.711 Safari/533.3",
        "X-User-MAC": m_addr,
        "Cookie": f"mac={m_addr}"
    }

    for path in paths:
        target = f"{p_url}{path}"
        try:
            async with session.get(target, headers=headers, timeout=10) as response:
                if response.status == 200:
                    text_data = await response.text()
                    data = json.loads(text_data)
                    channels = data.get("js", [])
                    if channels and isinstance(channels, list):
                        return channels, portal
        except:
            continue
    return [], portal

async def main():
    input_path = Path(INPUT_FILE)
    if not input_path.exists():
        print(f"Грешка: {INPUT_FILE} не е најден!")
        # Креираме празен фајл за да не падне GitHub Action
        with open(OUTPUT_M3U, "w") as f: f.write("#EXTM3U\n")
        return
    
    entries = []
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if "|" in line:
                # Екстракција на URL и MAC од твојот специфичен формат
                match = re.search(r"(https?://[^|]+)\|([0-9A-Fa-f:]+)", line)
                if match:
                    entries.append((match.group(1), match.group(2)))

    print(f"Пронајдени {len(entries)} портали во базата.")

    async with aiohttp.ClientSession() as session:
        tasks = [fetch_channels(session, p, m) for p, m in entries]
        results = await asyncio.gather(*tasks)

    # Секогаш го креираме фајлот за да избегнеме 'pathspec' грешка
    with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        channel_count = 0
        for channels, portal in results:
            if not channels: continue
            for ch in channels:
                name = ch.get("name", "Unknown")
                cmd = ch.get("cmd", "")
                # Чистење на стрим линкот
                stream = cmd.replace("ffrt ", "").replace("ffmpeg ", "").strip()
                if stream:
                    f.write(f'#EXTINF:-1 group-title="{portal}", {name}\n{stream}\n')
                    channel_count += 1
        
        # Ако нема канали, додаваме еден тест за да знаеш дека скриптата работи
        if channel_count == 0:
            f.write("#EXTINF:-1, СИСТЕМОТ РАБОТИ НО НЕМА АКТИВНИ КАНАЛИ\nhttp://google.com\n")
        
        print(f"Завршено! Пронајдени се {channel_count} канали.")

if __name__ == "__main__":
    asyncio.run(main())
