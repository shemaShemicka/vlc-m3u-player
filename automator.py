async def fetch_channels(session, portal, mac):
    p_url = portal.strip().rstrip('/')
    m_addr = mac.strip()
    
    # Листа на можни патеки за Stalker портали
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
                    data = await response.json()
                    channels = data.get("js", [])
                    if channels:
                        return channels, portal
        except:
            continue
    return [], portal
