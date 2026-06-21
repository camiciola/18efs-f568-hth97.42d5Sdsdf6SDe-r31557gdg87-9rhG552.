import json
import re
from datetime import datetime
from urllib.parse import urlparse
import urllib.request
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

OUTPUT_FILE = "news_data.json"

KEYWORDS_NDRANGHETA = [
    "ndrangheta", "ndranghet", "mafia", "cosca", "boss",
    "reggio calabria", "vibo valentia", "catanzaro", "cosenza",
    "calabria", "aspromonte", "locride", "crotonese", "lametino",
    "arresto", "arresti", "ordinanza", "custodia cautelare",
    "scarcerazione", "scarcerato", "fine pena",
    "cocaina", "hashish", "droga", "narcotraffico",
    "omicidio", "agguato", "spari", "killer", "attentato",
    "auto in fiamme", "incendio doloso", "gambizzato",
    "sequestro", "blitz", "operazione", "maxi-operazione",
    "carabinieri", "guardia di finanza", "dda", "ros",
    "procura", "antimafia", "latitante", "ergastolo"
]

KEYWORDS_HIGH_PRIORITY = [
    "scarcerato", "fine pena", "boss fuori", "libertà",
    "omicidio", "agguato", "spari", "killer", "attentato",
    "auto in fiamme", "gambizzato",
    "maxi-sequestro", "tonnellate", "maxi-operazione", "blitz",
    "ergastolo", "arresto"
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
    if "arresto" in text_lower or "arresti" in text_lower or "ordinanza" in text_lower or "custodia" in text_lower:
        categories.append("arresti")
    if "scarcerazione" in text_lower or "scarcerato" in text_lower or "fine pena" in text_lower:
        categories.append("scarcerazioni")
    if "cocaina" in text_lower or "hashish" in text_lower or "droga" in text_lower or "narcotraffico" in text_lower:
        categories.append("droga")
    if "omicidio" in text_lower or "agguato" in text_lower or "spari" in text_lower or "attentato" in text_lower or "incendio" in text_lower or "gambizzato" in text_lower:
        categories.append("sangue")
    if len(categories) == 0:
        categories.append("generico")
    return categories

def clean_title(title):
    title = re.sub(r'\d{2}\s\d{2}\s\d{2}\s-\s\d{2}:\d{2}', '', title)
    title = re.sub(r'\d{4}-\d{2}-\d{2}', '', title)
    return title.strip()

def scrape_generic_html(url, source_name, article_selector="article", title_selector="h2,h3,a", link_selector="a"):
    try:
        print("Scraping " + source_name + "...")
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read()
        soup = BeautifulSoup(html, "html.parser")
        news_list = []
        articles = soup.select(article_selector)[:30]
        if not articles:
            articles = soup.find_all(["div", "section"], class_=re.compile("article|post|news|item"), limit=30)
        for article in articles:
            title_elem = article.select_one(title_selector)
            link_elem = article.find("a", href=True)
            desc_elem = article.find(["p", "div"], class_=re.compile("summary|excerpt|description|text"))
            if title_elem:
                title = clean_title(title_elem.get_text(strip=True))
                link = ""
                if link_elem:
                    link = link_elem["href"]
                    if not link.startswith("http"):
                        link = url.rstrip("/") + "/" + link.lstrip("/")
                description = ""
                if desc_elem:
                    description = desc_elem.get_text(strip=True)
                if title and len(title) > 15:
                    news_list.append({
                        "title": title,
                        "link": link,
                        "description": description,
                        "pub_date": "",
                        "source": source_name
                    })
        print("Trovate " + str(len(news_list)) + " notizie da " + source_name)
        return news_list
    except Exception as e:
        print("Errore scraping " + source_name + ": " + str(e))
        return []

def scrape_rss(feed_url, source_name):
    try:
        print("Leggendo RSS: " + source_name)
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        req = urllib.request.Request(feed_url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            xml_content = response.read()
        root = ET.fromstring(xml_content)
        items = root.findall(".//item")
        if len(items) == 0:
            items = root.findall(".//{http://www.w3.org/2005/Atom}entry")
        news_list = []
        for item in items[:30]:
            title_elem = item.find("title")
            link_elem = item.find("link")
            desc_elem = item.find("description")
            date_elem = item.find("pubDate")
            if title_elem is None:
                title_elem = item.find("{http://www.w3.org/2005/Atom}title")
            if link_elem is None:
                link_elem = item.find("{http://www.w3.org/2005/Atom}link")
            if desc_elem is None:
                desc_elem = item.find("{http://www.w3.org/2005/Atom}summary")
            if date_elem is None:
                date_elem = item.find("{http://www.w3.org/2005/Atom}published")
            title = clean_title(title_elem.text if title_elem is not None else "")
            link = ""
            if link_elem is not None:
                if link_elem.text:
                    link = link_elem.text
                elif link_elem.get("href"):
                    link = link_elem.get("href")
            description = desc_elem.text if desc_elem is not None else ""
            pub_date = date_elem.text if date_elem is not None else ""
            if title and len(title) > 10:
                description = re.sub("<[^<]+?>", "", description)
                news_list.append({
                    "title": title,
                    "link": link,
                    "description": description[:300],
                    "pub_date": pub_date,
                    "source": source_name
                })
        print("Trovate " + str(len(news_list)) + " notizie da " + source_name)
        return news_list
    except Exception as e:
        print("Errore RSS " + source_name + ": " + str(e))
        return []

def fetch_all_news():
    all_news = []
    
    # Giornali calabresi e antimafia
    all_news.extend(scrape_generic_html("https://www.antimafiaduemila.com", "antimafiaduemila.com"))
    all_news.extend(scrape_generic_html("https://www.lacnews24.it", "lacnews24.it"))
    all_news.extend(scrape_generic_html("https://www.strettoweb.com", "strettoweb.com"))
    all_news.extend(scrape_generic_html("https://calabria7.it", "calabria7.it"))
    all_news.extend(scrape_generic_html("https://www.quotidianodelsud.it", "quotidianodelsud.it"))
    all_news.extend(scrape_generic_html("https://www.retenews24.it", "retenews24.it"))
    
    # Grandi giornali nazionali (RSS)
    all_news.extend(scrape_rss("https://www.ansa.it/sito/ansait_rss.xml", "ansa.it"))
    all_news.extend(scrape_rss("https://rss.corriere.it/rss/home.xml", "corriere.it"))
    all_news.extend(scrape_rss("https://www.repubblica.it/rss/homepage/rss2.0.xml", "repubblica.it"))
    all_news.extend(scrape_rss("https://www.ilfattoquotidiano.it/feed/", "ilfattoquotidiano.it"))
    all_news.extend(scrape_rss("https://www.lastampa.it/rss/home.xml", "lastampa.it"))
    all_news.extend(scrape_rss("https://www.ilsole24ore.com/rss/italia.xml", "ilsole24ore.com"))
    
    # Fonti internazionali
    all_news.extend(scrape_rss("http://feeds.bbci.co.uk/news/world/rss.xml", "bbc.com"))
    all_news.extend(scrape_rss("https://rss.cnn.com/rss/edition.rss", "cnn.com"))
    
    return all_news

def process_news(raw_news):
    processed = []
    for item in raw_news:
        full_text = item["title"] + " " + item["description"]
        is_ndrangheta = is_calabria_related(full_text)
        priority = calculate_priority(full_text) if is_ndrangheta else 0
        categories = categorize_news(full_text) if is_ndrangheta else ["generale"]
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
            "is_ndrangheta": is_ndrangheta,
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
    print("=" * 50)
    raw_news = fetch_all_news()
    print("Trovate " + str(len(raw_news)) + " notizie grezze")
    print("=" * 50)
    processed_news = process_news(raw_news)
    ndrangheta_count = sum(1 for n in processed_news if n["is_ndrangheta"])
    print("Notizie Ndrangheta/Calabria: " + str(ndrangheta_count))
    print("Notizie generali: " + str(len(processed_news) - ndrangheta_count))
    print("=" * 50)
    save_to_json(processed_news)
    print("Completato!")

if __name__ == "__main__":
    main()
