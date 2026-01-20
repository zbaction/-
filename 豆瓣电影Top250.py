import requests
from bs4 import BeautifulSoup
import csv
import time
import re
from collections import Counter
from pathlib import Path
from datetime import datetime
import random

def fetch_top250_page(start):
    url = f"https://movie.douban.com/top250?start={start}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    r = requests.get(url, headers=headers, timeout=15)
    r.raise_for_status()
    return r.text

def parse_top250(html):
    soup = BeautifulSoup(html, "html.parser")
    items = soup.select(".grid_view li")
    movies = []
    for li in items:
        title = li.select_one(".title").text.strip()
        score = li.select_one(".rating_num").text.strip()
        info = li.select_one(".bd p").text.strip().split("\n")[0].strip()
        p = li.select_one(".bd p").text.strip().split("\n")[1].strip()
        parts = [x.strip() for x in p.split("/") if x.strip()]
        year = parts[0] if len(parts) > 0 else ""
        country = parts[1] if len(parts) > 1 else ""
        genre = " / ".join(parts[2:]) if len(parts) > 2 else ""
        movies.append({
            "title": title,
            "score": score,
            "info": info,
            "year": year,
            "country": country,
            "genre": genre
        })
    return movies

def visualize_movies(movies):
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("未安装 matplotlib，跳过可视化。可执行：pip install matplotlib")
        return

    points = []
    countries = Counter()
    crime_scores = []

    for m in movies:
        year_text = str(m.get("year", "")).strip()
        year_match = re.search(r"\d{4}", year_text)
        if not year_match:
            continue
        year = int(year_match.group(0))

        try:
            score = float(str(m.get("score", "")).strip())
        except ValueError:
            continue

        points.append((year, score))

        country_text = str(m.get("country", "")).strip()
        if country_text:
            for c in re.split(r"[ /]+", country_text):
                c = c.strip()
                if c:
                    countries[c] += 1

        genre_text = str(m.get("genre", "")).strip()
        if "犯罪" in genre_text:
            crime_scores.append(score)

    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS"]
    plt.rcParams["axes.unicode_minus"] = False

    output_files = []

    def safe_savefig(path):
        try:
            plt.savefig(path, dpi=160, bbox_inches="tight")
            return Path(path)
        except PermissionError:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            fallback = Path(f"{Path(path).stem}_{ts}{Path(path).suffix}")
            plt.savefig(fallback, dpi=160, bbox_inches="tight")
            return fallback

    if points:
        year_to_scores = {}
        for y, s in points:
            year_to_scores.setdefault(y, []).append(s)

        years_sorted = sorted(year_to_scores.keys())
        mean_scores = [sum(year_to_scores[y]) / len(year_to_scores[y]) for y in years_sorted]

        xs = [y for y, _ in points]
        ys = [s for _, s in points]

        plt.figure(figsize=(10.5, 5))
        sc = plt.scatter(xs, ys, c=ys, cmap="viridis", s=22, alpha=0.55, linewidths=0)
        plt.plot(years_sorted, mean_scores, color="#202124", linewidth=2.2, marker="o", markersize=4)
        plt.title("评分随年份变化（散点 + 年均线）")
        plt.xlabel("年份")
        plt.ylabel("评分")
        plt.grid(True, alpha=0.2)
        plt.colorbar(sc, label="评分")
        out = Path("douban_score_by_year.png")
        plt.tight_layout()
        out = safe_savefig(out)
        plt.close()
        output_files.append(str(out))

    if countries:
        items = countries.most_common()
        top_n = 8
        top_items = items[:top_n]
        other_count = sum(v for _, v in items[top_n:])

        labels = [k for k, _ in top_items]
        values = [v for _, v in top_items]
        if other_count:
            labels.append("其他")
            values.append(other_count)

        colors = list(plt.cm.Set3.colors) + list(plt.cm.tab20.colors)
        colors = colors[:len(values)]

        plt.figure(figsize=(9.5, 6))
        wedges, texts, autotexts = plt.pie(
            values,
            labels=labels,
            autopct="%1.1f%%",
            startangle=90,
            counterclock=False,
            colors=colors,
            wedgeprops={"width": 0.45, "edgecolor": "white"},
            pctdistance=0.78
        )
        plt.title("不同国家/地区电影占比（Top8 + 其他）")
        plt.axis("equal")
        out = Path("douban_country_share.png")
        plt.tight_layout()
        out = safe_savefig(out)
        plt.close()
        output_files.append(str(out))

    if crime_scores:
        plt.figure(figsize=(8.5, 5))
        vp = plt.violinplot([crime_scores], showmeans=True, showmedians=True, showextrema=False)
        for body in vp["bodies"]:
            body.set_facecolor("#8ecae6")
            body.set_edgecolor("#023047")
            body.set_alpha(0.65)
        if "cmeans" in vp:
            vp["cmeans"].set_color("#fb8500")
            vp["cmeans"].set_linewidth(2)
        if "cmedians" in vp:
            vp["cmedians"].set_color("#ff006e")
            vp["cmedians"].set_linewidth(2)

        jitter_x = [1 + (random.random() - 0.5) * 0.18 for _ in crime_scores]
        plt.scatter(jitter_x, crime_scores, c=crime_scores, cmap="plasma", s=18, alpha=0.6, linewidths=0)
        plt.title("犯罪类型电影评分分布（小提琴 + 散点）")
        plt.xticks([1], ["犯罪"])
        plt.ylabel("评分")
        plt.grid(True, axis="y", alpha=0.2)
        out = Path("douban_crime_score_dist.png")
        plt.tight_layout()
        out = safe_savefig(out)
        plt.close()
        output_files.append(str(out))
    else:
        print("未找到包含“犯罪”类型的电影，跳过犯罪类型评分分布图。")

    if output_files:
        print("可视化图片已保存：")
        for p in output_files:
            print("-", p)

def write_csv(movies, path):
    path = Path(path)
    try:
        with path.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["title","score","info","year","country","genre"])
            writer.writeheader()
            writer.writerows(movies)
        return path
    except PermissionError:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        fallback = Path(f"{path.stem}_{ts}{path.suffix}")
        with fallback.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["title","score","info","year","country","genre"])
            writer.writeheader()
            writer.writerows(movies)
        print(f"无法写入 {path}（可能被Excel占用），已改写到：{fallback}")
        return fallback

def main():
    all_movies = []
    for start in range(0, 250, 25):
        html = fetch_top250_page(start)
        movies = parse_top250(html)
        all_movies += movies
        time.sleep(1)

    csv_path = write_csv(all_movies, "douban_top250.csv")

    print("豆瓣 Top250 爬取完成!")
    print("CSV 已保存：", csv_path)
    visualize_movies(all_movies)

if __name__ == "__main__":
    main()
