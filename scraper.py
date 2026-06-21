import json
import re
from datetime import datetime
from urllib.parse import urlparse
import urllib.request
import xml.etree.ElementTree as ET

OUTPUT_FILE = "news_data.json"

KEYWORDS_NDRANGHETA = [
    "ndrangheta", "ndranghet", "mafia calabra", "cosca",
    "reggio calabria", "vibo valentia", "catanzaro", "cosenza",
    "calabria", "aspromonte", "locride",
    "arresto", "arresti", "ordinanza", "custodia cautelare",
    "scarcerazione", "scarcerato", "fine pena",
    "cocaina", "hashish", "droga",
    "omicidio", "agguato", "spari", "killer", "attentato",
    "auto in fiamme", "incendio", "gambizzato",
    "sequestro", "blitz", "operazione",
    "carabinieri", "guardia di finanza", "dda",
    "procura", "antimafia"
]

KEYWORDS_HIGH_PRIORITY = [
    "scarcerato", "fine pena", "boss fuori",
    "omicidio", "agguato", "spari", "killer", "attentato",
    "auto in fiamme", "gambizzato",
    "maxi-sequestro", "tonnellate", "maxi-operazione", "blitz"
]

RSS_FEEDS = [
    "https://www.antimafiaduemila.com/feed/rss",
    "https://www.ansa.it/sito/section_news/cronaca/cronaca_rss.xml"
]

def is_calabria_related(text):
    text_lower = text.lower()
    for keyword in KEYWORDS_NDRANGHETA:
        if keyword in text_lower:
            return True
    return False

def calculate_priority(text):
    text_lower = text.lower()
    score = 0
    for keyword in KEYWORDS_HIGH_PRIORITY:
        if keyword in text_lower:
            score = score + 10
    return score

def categorize_news(text):
    text_lower = text.lower()
    categories = []
    if "arresto" in text_lower or "arresti" in text_lower or "ordinanza" in text_lower:
        categories.append("arresti")
    if "scarcerazione" in text_lower or "scarcerato" in text_lower or "fine pena" in text_lower:
        categories.append("scarcerazioni")
    if "cocaina" in text_lower or "hashish" in text_lower or "droga" in text_lower:
        categories.append("droga")
    if "omicidio" in text_lower or "agguato" in text_lower or "spari" in text_lower or "attentato" in text_lower or "incendio" in text_lower:
        categories.append("sangue")
    if len(categories) == 0:
        categories.append("generico")
    return categories

def parse_rss_feed(feed_url):
    try:
        print("Leggendo: " + feed_url)
        headers = {"User-Agent": "Mozilla/5.0"}
        req = urllib.request.Request(feed_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            xml_content = response.read()
        root = ET.fromstring(xml_content)
        items = root.findall(".//item")
        news_list = []
        for item in items[:20]:
            title_elem = item.find("title")
            link_elem = item.find("link")
            desc_elem = item.find("description")
            date_elem = item.find("pubDate")
            title = title_elem.text if title_elem is not None else ""
            link = link_elem.text if link_elem is not None else ""
            description = desc_elem.text if desc_elem is not None else ""
            pub_date = date_elem.text if date_elem is not None else ""
            description = re.sub("<[^<]+?>", "", description)
            news_list.append({
                "title": title,
                "link": link,
                "description": description,
                "pub_date": pub_date,
                "source": urlparse(feed_url).netloc
            })
        return news_list
    except Exception as e:
        print("Errore con " + feed_url + ": " + str(e))
        return []

def fetch_all_news():
    all_news = []
    for feed_url in RSS_FEEDS:
        news = parse_rss_feed(feed_url)
        for n in news:
            all_news.append(n)
    return all_news

def process_news(raw_news):
    processed = []
    for item in raw_news:
        full_text = item["title"] + " " + item["description"]
        if is_calabria_related(full_text):
            priority = calculate_priority(full_text)
            categories = categorize_news(full_text)
            summary = item["description"]
            if len(summary) > 300:
                summary = summary[:300] + "..."
            news_item = {
                "title": item["title"],
                "summary": summary,
                "link": item["link"],
                "published": item["pub_date"],
                "source": item["source"],
                "priority": priority,
                "categories": categories,
                "is_ndrangheta": True,
                "is_high_priority": priority >= 20
            }
            processed.append(news_item)
    return processed

def save_to_json(news_data):
    news_data.sort(key=lambda x: x["priority"], reverse=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        data = {
            "last_update": datetime.now().isoformat(),
            "total_news": len(news_data),
            "news": news_data
        }
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("Salvate " + str(len(news_data)) + " notizie")

def main():
    print("Avvio scraper notizie...")
    raw_news = fetch_all_news()
    print("Trovate " + str(len(raw_news)) + " notizie grezze")
    processed_news = process_news(raw_news)
    print("Notizie filtrate: " + str(len(processed_news)))
    save_to_json(processed_news)
    print("Completato!")

if __name__ == "__main__":
    main()
