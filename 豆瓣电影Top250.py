import requests
from bs4 import BeautifulSoup
import csv
import time

def fetch_top250_page(start):
    url = f"https://movie.douban.com/top250?start={start}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    r = requests.get(url, headers=headers)
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
        movies.append({
            "title": title,
            "score": score,
            "info": info
        })
    return movies

all_movies = []
for start in range(0, 250, 25):
    html = fetch_top250_page(start)
    movies = parse_top250(html)
    all_movies += movies
    time.sleep(1)

with open("douban_top250.csv", "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["title","score","info"])
    writer.writeheader()
    writer.writerows(all_movies)

print("豆瓣 Top250 爬取完成!")
