import json
import re
from datetime import datetime
from urllib.parse import urlparse
import urllib.request
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

OUTPUT_FILE = "news_data.json"

# BLACKLIST: parole che indicano notizie NON rilevanti
BLACKLIST_WORDS = [
    "oroscopo", "meteo", "caldo", "bollino rosso", "temperature",
    "gossip", "vip", "celebrità", "reality", "trono", "udienze",
    "sanremo", "festival", "canzone", "classifica", "serie a",
    "serie b", "calcio", "partita", "juventus", "milan", "inter",
    "napoli calcio", "roma calcio", "lazio calcio",
    "ricetta", "cucina", "ristorante", "chef",
    "moda", "sfilata", "collezione"
]

# KEYWORD NDRANGHETA SPECIFICHE (non generiche "mafia")
KEYWORDS_NDRANGHETA_SPECIFIC = [
    "ndrangheta", "ndranghet", "'ndrangheta", "'ndrine", "ndrina",
    "cosca calabra", "boss calabra", "mafia calabra",
    "piromalli", "molè", "nirta", "pesce", "vottari", "cordì",
    "mantella", "bonavota", "grande aracri", "città di 'ndrangheta",
    "locri", "siderno", "rosarno", "san luca", "platì", "africo",
    "aspromonte", "locride", "crotonese", "reggino"
]

# KEYWORD CALABRIA (solo se combinate con contesto criminale)
KEYWORDS_CALABRIA = [
    "calabria", "reggio calabria", "cosenza", "catanzaro",
    "vibo valentia", "crotone", "lametino"
]

# KEYWORD CRIMINALI (da combinare con Calabria per 'Ndrangheta)
KEYWORDS_CRIME = [
    "arresto", "arresti", "ordinanza", "custodia cautelare", "fermo",
    "scarcerazione", "scarcerato", "fine pena", "domiciliari",
    "cocaina", "hashish", "droga", "narcotraffico", "spaccio",
    "omicidio", "agguato", "spari", "killer", "attentato", "gambizzato",
    "auto in fiamme", "incendio doloso", "auto bruciata",
    "sequestro", "blitz", "operazione", "maxi-operazione", "retata",
    "carabinieri", "guardia di finanza", "dda", "ros", "scop",
    "procura", "antimafia", "ergastolo", "condanna",
    "riciclaggio", "usura", "estorsione", "pizzo",
    "traffico internazionale", "clan", "famiglia criminale",
    "latitante", "mafia", "cosa nostra", "camorra", "sacra corona unita"
]

# KEYWORD ALTA PRIORITÀ
KEYWORDS_HIGH_PRIORITY = [
    "scarcerato", "fine pena", "boss fuori", "libertà",
    "omicidio", "agguato", "spari", "killer", "attentato",
    "auto in fiamme", "gambizzato",
    "maxi-sequestro", "tonnellate", "maxi-operazione", "blitz",
    "ergastolo"
]

# KEYWORD MONDO RILEVANTE
KEYWORDS_MONDO = [
    "guerra", "attacco", "missili", "bombe", "esercito",
    "trump", "biden", "putin", "zelensky", "meloni", "macron",
    "nato", "ue", "unione europea", "onu",
    "terremoto", "uragano", "alluvione", "catastrofe",
    "elezioni", "voto", "referendum",
    "nucleare", "atomica", "terrorismo", "isis", "al-qaeda",
    "migranti", "rifugiati", "sbarchi",
    "ucraina", "russia", "usa", "stati uniti", "cina", "israele",
    "palestina", "medio oriente", "africa"
]

def is_blacklisted(text):
    text_lower = text.lower()
    for word in BLACKLIST_WORDS:
        if word in text_lower:
            return True
    return False

def is_ndrangheta_specific(text):
    """Notizia SPECIFICA di 'Ndrangheta (non mafia generica)"""
    text_lower = text.lower()
    # Deve contenere almeno una keyword specifica 'ndrangheta
    has_ndrangheta = any(k in text_lower for k in KEYWORDS_NDRANGHETA_SPECIFIC)
    if has_ndrangheta:
        return True
    # OPPURE: Calabria + contesto criminale
    has_calabria = any(k in text_lower for k in KEYWORDS_CALABRIA)
    has_crime = any(k in text_lower for k in KEYWORDS_CRIME)
    if has_calabria and has_crime:
        return True
    return False

def is_crime_italy(text):
    """Notizia di criminalità italiana (camorra, cosa nostra, ecc.)"""
    text_lower = text.lower()
    crime_keywords = ["mafia", "cosa nostra", "camorra", "sacra corona",
                      "arresto", "arresti", "omicidio", "agguato",
                      "droga", "cocaina", "sequestro", "blitz",
                      "carabinieri", "procura", "antimafia", "ergastolo",
                      "latitante", "boss", "clan"]
    return any(k in text_lower for k in crime_keywords)

def is_news_italy_relevant(text):
    """Notizia italiana rilevante (politica, cronaca importante)"""
    text_lower = text.lower()
    italy_keywords = ["meloni", "governo", "parlamento", "legge",
                      "roma", "italia", "presidente", "ministro",
                      "pd", "lega", "fratelli d'italia", "m5s", "forza italia",
                      "sciopero", "sindacato", "economia", "pil", "inflazione",
                      "terremoto", "alluvione", "maltempo"]
    return any(k in text_lower for k in italy_keywords)

def is_news_world_relevant(text):
    """Notizia mondiale rilevante"""
    text_lower = text.lower()
    return any(k in text_lower for k in KEYWORDS_MONDO)

def calculate_priority(text):
    text_lower = text.lower()
    score = 0
    for keyword in KEYWORDS_HIGH_PRIORITY:
        if keyword in text_lower:
            score = score + 10
    return score

def categorize_news(text, section):
    text_lower = text.lower()
    categories = []
    if section == "ndrangheta":
        if "arresto" in text_lower or "arresti" in text_lower or "ordinanza" in text_lower or "custodia" in text_lower or "fermo" in text_lower or "operazione" in text_lower or "blitz" in text_lower:
            categories.append("arresti")
        if "scarcerazione" in text_lower or "scarcerato" in text_lower or "fine pena" in text_lower or "domiciliari" in text_lower:
            categories.append("scarcerazioni")
        if "cocaina" in text_lower or "hashish" in text_lower or "droga" in text_lower or "narcotraffico" in text_lower or "spaccio" in text_lower:
            categories.append("droga")
        if "omicidio" in text_lower or "agguato" in text_lower or "spari" in text_lower or "attentato" in text_lower or "incendio" in text_lower or "gambizzato" in text_lower or "auto in fiamme" in text_lower:
            categories.append("sangue")
        if len(categories) == 0:
            categories.append("generico")
    elif section == "mondo":
        if "guerra" in text_lower or "attacco" in text_lower or "missili" in text_lower or "bombe" in text_lower:
            categories.append("guerre")
        if "elezioni" in text_lower or "voto" in text_lower or "referendum" in text_lower:
            categories.append("politica")
        if "trump" in text_lower or "biden" in text_lower or "putin" in text_lower or "zelensky" in text_lower or "meloni" in text_lower or "macron" in text_lower:
            categories.append("leader")
        if "ucraina" in text_lower or "russia" in text_lower:
            categories.append("ucraina-russia")
        if "israele" in text_lower or "palestina" in text_lower:
            categories.append("medio-oriente")
        if "usa" in text_lower or "stati uniti" in text_lower or "cina" in text_lower:
            categories.append("superpotenze")
        if len(categories) == 0:
            categories.append("mondo")
    elif section == "italia":
        if "governo" in text_lower or "parlamento" in text_lower or "legge" in text_lower:
            categories.append("politica")
        if "economia" in text_lower or "pil" in text_lower or "inflazione" in text_lower:
            categories.append("economia")
        if "sciopero" in text_lower or "sindacato" in text_lower:
            categories.append("lavoro")
        if len(categories) == 0:
            categories.append("italia")
    return categories

def clean_title(title):
    title = re.sub(r'\d{2}\s\d{2}\s\d{2}\s-\s\d{2}:\d{2}', '', title)
    title = re.sub(r'\d{4}-\d{2}-\d{2}', '', title)
    title = re.sub(r'^-\d{2}:\d{2}', '', title)
    return title.strip()

def scrape_generic_html(url, source_name, article_selector="article"):
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
            title_elem = article.find(["h1", "h2", "h3", "a"])
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
        print("  Trovate " + str(len(news_list)) + " notizie da " + source_name)
        return news_list
    except Exception as e:
        print("  Errore scraping " + source_name + ": " + str(e))
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
        print("  Trovate " + str(len(news_list)) + " notizie da " + source_name)
        return news_list
    except Exception as e:
        print("  Errore RSS " + source_name + ": " + str(e))
        return []

def fetch_all_news():
    all_news = []
    all_news.extend(scrape_generic_html("https://www.antimafiaduemila.com", "antimafiaduemila.com"))
    all_news.extend(scrape_generic_html("https://www.lacnews24.it", "lacnews24.it"))
    all_news.extend(scrape_generic_html("https://www.strettoweb.com", "strettoweb.com"))
    all_news.extend(scrape_generic_html("https://www.quotidianodelsud.it", "quotidianodelsud.it"))
    all_news.extend(scrape_rss("https://www.ilfattoquotidiano.it/feed/", "ilfattoquotidiano.it"))
    all_news.extend(scrape_rss("https://www.ilsole24ore.com/rss/italia.xml", "ilsole24ore.com"))
    all_news.extend(scrape_rss("http://feeds.bbci.co.uk/news/world/rss.xml", "bbc.com"))
    return all_news

def classify_news(item):
    """Classifica una notizia in UNA SOLA sezione"""
    full_text = (item["title"] + " " + item["description"]).lower()
    
    # Blacklist: notizie irrilevanti
    if is_blacklisted(full_text):
        return None, [], 0
    
    # 1. NDRANGHETA (priorità massima, controllo più stringente)
    if is_ndrangheta_specific(full_text):
        priority = calculate_priority(full_text)
        categories = categorize_news(full_text, "ndrangheta")
        return "ndrangheta", categories, priority
    
    # 2. CRIMINALITÀ ITALIANA (camorra, cosa nostra, ecc.)
    if is_crime_italy(full_text):
        priority = calculate_priority(full_text)
        categories = ["crime_italy"]
        return "crime_italy", categories, priority
    
    # 3. MONDO (notizie internazionali rilevanti)
    if is_news_world_relevant(full_text):
        categories = categorize_news(full_text, "mondo")
        return "mondo", categories, 0
    
    # 4. ITALIA (notizie italiane rilevanti)
    if is_news_italy_relevant(full_text):
        categories = categorize_news(full_text, "italia")
        return "italia", categories, 0
    
    # Non classificata - scartare
    return None, [], 0

def process_news(raw_news):
    processed = []
    seen_titles = set()
    
    for item in raw_news:
        # Evita duplicati (stesso titolo)
        title_key = item["title"][:50].lower()
        if title_key in seen_titles:
            continue
        
        section, categories, priority = classify_news(item)
        
        if section is None:
            continue
        
        seen_titles.add(title_key)
        
        summary = item["description"]
        if len(summary) > 300:
            summary = summary[:300] + "..."
        if not summary:
            summary = "Clicca per leggere l'articolo completo"
        
        news_item = {
            "title": item["title"],
            "summary": summary,
            "link": item["link"],
            "published": item["pub_date"],
            "source": item["source"],
            "section": section,
            "priority": priority,
            "categories": categories,
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
    
    ndrangheta_count = sum(1 for n in processed_news if n["section"] == "ndrangheta")
    crime_italy_count = sum(1 for n in processed_news if n["section"] == "crime_italy")
    mondo_count = sum(1 for n in processed_news if n["section"] == "mondo")
    italia_count = sum(1 for n in processed_news if n["section"] == "italia")
    
    print("Notizie 'Ndrangheta: " + str(ndrangheta_count))
    print("Notizie criminalità italiana: " + str(crime_italy_count))
    print("Notizie mondo: " + str(mondo_count))
    print("Notizie italia: " + str(italia_count))
    print("=" * 50)
    save_to_json(processed_news)
    print("Completato!")

if __name__ == "__main__":
    main()
