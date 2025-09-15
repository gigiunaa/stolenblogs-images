import requests
from bs4 import BeautifulSoup

url = "https://www.example.com/blog-post"
resp = requests.get(url)
resp.raise_for_status()

soup = BeautifulSoup(resp.text, "html.parser")
image_urls = []

for img in soup.find_all("img"):
    src = img.get("src")
    if src and src.startswith("http"):
        image_urls.append(src)

print("სურათები:", image_urls)
