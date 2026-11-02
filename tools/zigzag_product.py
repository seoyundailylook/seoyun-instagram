#!/usr/bin/env python3
"""Check Zigzag product pages: name, shop, brand/shop type, price, stock.

Usage: python3 tools/zigzag_product.py <product id or URL> [...]
Needs zigzag.kr in the environment's allowed domains.
"""
import json, re, sys, time, urllib.request

UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148"

def fetch(pid, tries=4):
    for i in range(tries):
        req = urllib.request.Request(f"https://zigzag.kr/catalog/products/{pid}", headers={"User-Agent": UA})
        html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
        m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
        if m:
            break
        time.sleep(3 * (i + 1))
    else:
        raise RuntimeError(f"no product data after {tries} tries ({len(html)} bytes)")
    qs = json.loads(m.group(1))["props"]["pageProps"]["dehydratedState"]["queries"]
    data = next(q["state"]["data"] for q in qs if q.get("queryKey", [None])[0] == "getPdpBaseInfo")
    p, shop = data["product"], data["shop"]
    price = (p.get("product_price") or {}).get("final_discount_info") or {}
    colors = [c.get("name") or c.get("title") for c in ((p.get("color_swatch_carousel") or {}).get("item_list") or [])] \
        if isinstance(p.get("color_swatch_carousel"), dict) else []
    return {
        "id": pid, "name": p["name"], "shop": shop.get("name"),
        "type": "브랜드" if p.get("is_brand") else "쇼핑몰",
        "status": p.get("sales_status"), "display": p.get("display_status"),
        "purchasable": p.get("is_purchasable"),
        "price": price.get("discount_price"), "discount_rate": price.get("discount_rate"),
        "colors": [c for c in colors if c],
        "url": f"https://zigzag.kr/catalog/products/{pid}",
    }

if __name__ == "__main__":
    for arg in sys.argv[1:]:
        pid = re.search(r"(\d{6,})", arg).group(1)
        try:
            print(json.dumps(fetch(pid), ensure_ascii=False))
        except Exception as e:
            print(json.dumps({"id": pid, "error": str(e)[:200]}, ensure_ascii=False))
