import sqlite3
import time
import re
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from datetime import datetime

# Currency pattern
CURRENCY_PATTERN = re.compile(r"(₹|Rs\.?|USD|EUR|£|\$)\s?[\d,]+(\.\d{1,2})?", re.IGNORECASE)

# Chrome options
options = webdriver.ChromeOptions()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--window-size=1280,800")
options.add_argument("--disable-gpu")
#options.add_argument("--headless=new")

# ✅ Setup SQLite Database
DB_FILE = "scraper.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site TEXT,
            name TEXT,
            price TEXT,
            store TEXT,
            scraped_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_to_db(site, name, price, store):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO products (site, name, price, store, scraped_at)
        VALUES (?, ?, ?, ?, ?)
    """, (site, name, price, store, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def extract_store_google(div_text, price, search_words):
    after_price = div_text.split(price, 1)[-1]
    words = after_price.split()

    # Step 1: Original '&' logic
    for i, word in enumerate(words):
        if word.strip() == "&" and i > 0:
            return words[i - 1].strip()

    # Step 2: Remove product-related words
    ignore_words = set(search_words + ["refurbished", "new", "sealed", "version", "get", "buy"])
    candidate_words = [w for w in words if w.lower() not in ignore_words]

    # Step 3: If domain-like (.in, .com) exists, return that
    for word in candidate_words:
        if ".in" in word.lower() or ".com" in word.lower():
            return word.strip()

    # Step 4: First valid word(s)
    clean_candidates = [w for w in candidate_words if w[0].isalpha()]
    if clean_candidates:
        return " ".join(clean_candidates[:2])

    return "Unknown"

def scrape_with_universal_method(url, search_words, site_name, results_set):
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    print(f"\nOpening {site_name}: {url}")
    driver.get(url)
    time.sleep(random.uniform(5, 8))

    html = driver.page_source
    driver.quit()

    soup = BeautifulSoup(html, "html.parser")
    page_results = []

    for big_div in soup.find_all("div"):
        div_text = big_div.get_text("\n", strip=True)

        if not all(word in div_text.lower() for word in search_words):
            continue
        if not CURRENCY_PATTERN.search(div_text):
            continue

        lines = [line.strip() for line in div_text.split("\n") if line.strip()]
        name, price, store = None, None, None

        for line in lines:
            if not price and CURRENCY_PATTERN.search(line):
                price = CURRENCY_PATTERN.search(line).group()
            if all(w in line.lower() for w in search_words) and len(line) > len(" ".join(search_words)) + 3:
                name = line

       # Store logic
        if site_name == "Google Shopping" and price:
            store = extract_store_google(div_text, price, search_words)
        else:
            # For Amazon and Flipkart, use the site name as store name
            store = site_name.split()[0]  # "Amazon" or "Flipkart"

        if name and price:
            item = (site_name, name, price, store if store else "Unknown")

            if item not in results_set:
                results_set.add(item)
                page_results.append(item)
                # ✅ Save to DB
                save_to_db(item[0], item[1], item[2], item[3])

    return page_results

if __name__ == "__main__":
    init_db()  # ✅ Initialize DB once

    product = input("Enter product to search: ")
    search_query = product.replace(" ", "+")
    search_words = product.lower().split()

    # Multi-page URLs
    amazon_urls = [
        (f"https://www.amazon.in/s?k={search_query}&page={1}", "Amazon India")
        for i in range(1, 4)
    ]
    flipkart_urls = [
        (f"https://www.flipkart.com/search?q={search_query}&page={1}", "Flipkart")
        for i in range(1, 4)
    ]
    google_urls = [
        (f"https://www.google.com/search?tbm=shop&q={search_query}&start={1}", "Google Shopping")
        for i in range(0, 90, 30)
    ]

    urls = amazon_urls + flipkart_urls + google_urls
    all_results = set()

    for url, site_name in urls:
        scrape_with_universal_method(url, search_words, site_name, all_results)
        time.sleep(random.uniform(3, 6))

    print("\n✅ Data saved to scraper.db")

    '''# ✅ View last 20 rows from DB (instead of printing all)
    print("\n--- Last 20 entries from database ---")
    conn = sqlite3.connect(DB_FILE)
    rows = conn.execute("SELECT site, name, price, store FROM products ORDER BY id DESC LIMIT 20").fetchall()
    conn.close()
    for row in rows:
        print(row)'''
