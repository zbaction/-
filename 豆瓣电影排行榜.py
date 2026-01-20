import time
import csv
import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
    "Referer": "https://movie.douban.com/chart",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
}

def fetch_count(type_id=10, interval_id="100:90"):
    url = "https://movie.douban.com/j/chart/top_list_count"
    params = {
        "type": type_id,
        "interval_id": interval_id
    }
    r = requests.get(url, params=params, headers=HEADERS, timeout=15)
    r.raise_for_status()
    # 返回形如：{"total": 523}
    return r.json()["total"]

def fetch_list(type_id=10, start=0, limit=20, interval_id="100:90"):
    url = "https://movie.douban.com/j/chart/top_list"
    params = {
        "type": type_id,
        "interval_id": interval_id,
        "action": "",
        "start": start,
        "limit": limit
    }
    r = requests.get(url, params=params, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.json()

def crawl_to_csv(type_id=10, interval_id="100:90", limit=20, out_csv="douban_chart.csv"):
    total = fetch_count(type_id=type_id, interval_id=interval_id)
    print("total =", total)

    all_rows = []
    for start in range(0, total, limit):
        data = fetch_list(type_id=type_id, start=start, limit=limit, interval_id=interval_id)

        # 防止中途被限制导致返回空
        if not data:
            print("返回空数据，可能触发限制，start =", start)
            break

        for item in data:
            all_rows.append({
                "rank": item.get("rank"),
                "title": item.get("title"),
                "score": item.get("score"),
                "vote_count": item.get("vote_count"),
                "release_date": item.get("release_date"),
                "regions": ",".join(item.get("regions") or []),
                "types": ",".join(item.get("types") or []),
                "actors": item.get("actors"),
                "url": item.get("url"),
                "cover_url": item.get("cover_url"),
            })

        print(f"已抓取：{len(all_rows)}/{total}")
        time.sleep(1)

    if not all_rows:
        print("没有抓到数据")
        return

    with open(out_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=all_rows[0].keys())
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"保存完成：{out_csv}，共 {len(all_rows)} 条")

if __name__ == "__main__":
    crawl_to_csv(type_id=10, interval_id="100:90", limit=20, out_csv="douban_chart_xuanyi.csv")
