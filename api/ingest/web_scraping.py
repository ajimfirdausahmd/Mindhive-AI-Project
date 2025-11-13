import re
import csv
import time
import json
import  os
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]    
DATA_DIR = BASE_DIR / "data"
SAVE_PATH = DATA_DIR / "drinkware.jsonl"

os.makedirs(DATA_DIR, exist_ok=True)


BASE = "https://shop.zuscoffee.com"
COLLECTION = "/collections/drinkware"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ZUS-Scraper/1.0; +https://example.com/bot)"}



def get_html(url):
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.text

def collect_product_links(collection_url):
    html = get_html(collection_url)
    soup = BeautifulSoup(html, "html.parser")
    links = set()

    for a in soup.select('a[href^="/products/"]'):
        href = a.get("href")
        if href and "/products/" in href:
            
            path = urlparse(href).path
            links.add(urljoin(BASE, path))
    return sorted(links)

PRICE_RE = re.compile(r"RM\s?([\d.,]+)")

def extract_price(soup):
    
    node = soup.find(string=lambda s: isinstance(s, str) and "Sale price" in s)
    if node:
        m = PRICE_RE.search(node)
        if m:
            return float(m.group(1).replace(",", ""))
    
    all_text = soup.get_text(" ", strip=True)
    m = PRICE_RE.search(all_text)
    return float(m.group(1).replace(",", "")) if m else None

def extract_variants_block(soup):
  
    txt = " ".join(
        t.strip() for t in soup.find_all(string=True) if isinstance(t, str)
    )


    pairs = re.findall(r"([A-Za-z][A-Za-z\s/]+?)\s*-\s*RM\s*([\d.,]+)", txt)
    variants = []
    for name, rm in pairs:
        price = float(rm.replace(",", ""))
        # Basic sanity check to avoid capturing random sentences
        if 1 <= len(name) <= 40 and price > 0:
            variants.append({"name": name.strip(), "price_rm": price})
    # Deduplicate by name
    uniq = {}
    for v in variants:
        uniq[v["name"]] = v
    return list(uniq.values())

def extract_list_after_heading(soup, heading_text):
    h = soup.find(string=lambda s: isinstance(s, str) and heading_text.lower() in s.lower())
    if not h:
        return []
    container = h.parent
    for _ in range(5):
        if container.find_all("li"):
            break
        container = container.parent
    items = [li.get_text(" ", strip=True) for li in container.find_all("li")]
    return [i for i in items if 2 <= len(i) <= 200]

def extract_main_image(soup):
    for img in soup.select("img[src]"):
        alt = (img.get("alt") or "").lower()
        src = img["src"]
        if not src.startswith("http"):
            src = urljoin(BASE, src)
        if any(k in alt for k in ["logo", "icon"]) or ("svg" in src):
            continue
        return src
    return None

def scrape_product(url):
    html = get_html(url)
    soup = BeautifulSoup(html, "html.parser")
    title_el = soup.select_one("h1") or soup.select_one("h1.product__title")
    title = title_el.get_text(strip=True) if title_el else None

    price_rm = extract_price(soup)
    variants = extract_variants_block(soup)

    
    short_desc = None
   
    p = soup.find("p")
    if p:
        short_desc = p.get_text(" ", strip=True)

    measurements = extract_list_after_heading(soup, "Measurements")
    materials   = extract_list_after_heading(soup, "Materials")

    image = extract_main_image(soup)

    return {
        "title": title,
        "price_rm": price_rm,
        "variants": variants,            
        "short_description": short_desc,
        "measurements": measurements,    
        "materials": materials,          
        "image": image,
        "url": url,
    }

def save_jsonl(rows, path=SAVE_PATH):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    collection_url = urljoin(BASE, COLLECTION)
    product_links = collect_product_links(collection_url)
    print(f"Found {len(product_links)} product URLs")
    rows = []
    for i, url in enumerate(product_links, 1):
        try:
            data = scrape_product(url)
            rows.append(data)
            print(f"[{i}/{len(product_links)}] {data['title']}")
        except Exception as e:
            print(f"Error on {url}: {e}")
        time.sleep(0.7) 
    save_jsonl(rows)
    print("Saved to {SAVE_PATH}")
