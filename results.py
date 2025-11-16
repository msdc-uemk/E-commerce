# results.py
import sqlite3
import pandas as pd
import webbrowser
import os
from datetime import datetime
import re

DB_PATH = "scraper.db"
OUT_HTML = "scraper_results.html"


def load_data(search_term=""):
    if not os.path.exists(DB_PATH):
        print("⚠️ Database not found.")
        return pd.DataFrame()

    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT id, site, name, price, store, scraped_at FROM products ORDER BY id DESC",
        conn,
    )
    conn.close()

    # Filter by search term
    if search_term:
        df = df[df["name"].str.lower().str.contains(search_term.lower())]

    df.insert(0, "No", range(1, len(df) + 1))
    return df


def get_price_value(price_str):
    """Extract numeric price value for sorting"""
    if not price_str:
        return 0
    match = re.search(r"[\d,]+(\.\d+)?", str(price_str))
    if match:
        try:
            return float(match.group(0).replace(",", ""))
        except:
            return 0
    return 0


def build_html(df, search_term=""):
    df["price_value"] = df["price"].apply(get_price_value)

    html_table = df.to_html(
        index=False,
        escape=False,
        classes="table table-striped table-bordered",
        border=0,
    )

    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>🛒 Web Scraper Results Dashboard</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
  <script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
  <link href="https://cdn.datatables.net/1.13.6/css/jquery.dataTables.min.css" rel="stylesheet">

  <style>
    body {{
      background-color: #111;
      color: #eee;
      font-family: 'Segoe UI', sans-serif;
    }}
    h1 {{
      color: #ffc107;
      font-weight: 700;
    }}
    .table-container {{
      background-color: #f9f9f9;
      color: #111;
      border-radius: 10px;
      padding: 20px;
    }}
  </style>
</head>
<body>
  <div class="container mt-4">
    <div class="text-center mb-4">
      <h1>🛒 Web Scraper Results Dashboard</h1>
      <p class="text-secondary">Showing results for <b>{search_term if search_term else "all products"}</b></p>
      <p><small>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</small></p>
    </div>

    <div class="mb-3 text-center">
      <button id="lowHigh" class="btn btn-success btn-sm me-2">Sort by Price: Low → High</button>
      <button id="highLow" class="btn btn-danger btn-sm">Sort by Price: High → Low</button>
    </div>

    <div class="table-container">
      {html_table}
    </div>
  </div>

  <script>
    $(document).ready(function() {{
      var table = $('table').DataTable({{
        pageLength: 15,
        order: [],
        columnDefs: [
          {{
            targets: -1, // last column = price_value
            visible: false,
            searchable: false,
            type: 'num'
          }}
        ]
      }});

      // Sort buttons
      $('#lowHigh').on('click', function() {{
        table.order([table.columns().count() - 1, 'asc']).draw();
      }});
      $('#highLow').on('click', function() {{
        table.order([table.columns().count() - 1, 'desc']).draw();
      }});
    }});
  </script>
</body>
</html>
"""

    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ HTML report saved: {OUT_HTML}")


def open_html():
    webbrowser.open(f"file://{os.path.abspath(OUT_HTML)}")
    print("🌐 Opening in browser...")


if __name__ == "__main__":
    search_term = input("🔍 Enter product name to filter (e.g., iphone): ").strip()
    df = load_data(search_term)
    if df.empty:
        print("⚠️ No data found.")
    else:
        build_html(df, search_term)
        open_html()
