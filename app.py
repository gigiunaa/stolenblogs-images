import os
import logging
import requests
from flask import Flask, request, jsonify
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

def clean_html(soup):
    # წაშლის <style>, <script>, <svg>, <noscript>
    for tag in soup(["style", "script", "svg", "noscript"]):
        tag.decompose()

    # base64 img → წაშალე
    for img in soup.find_all("img"):
        src = img.get("src", "")
        if src.startswith("data:image"):
            img.decompose()

    # ატრიბუტების გაწმენდა
    for tag in soup.find_all(True):
        if tag.name == "a":
            if "href" in tag.attrs:
                del tag.attrs["href"]

        elif tag.name == "img":
            src = tag.get("src")
            alt = tag.get("alt", "").strip() or "Image"
            tag.attrs = {"src": src, "alt": alt}

        else:
            for attr in list(tag.attrs.keys()):
                if attr not in ["src", "alt"]:
                    del tag.attrs[attr]

    # wrapper div-ების მოცილება
    for div in soup.find_all("div"):
        if not div.attrs and len(div.contents) == 1:
            div.unwrap()
        elif not div.attrs and not div.get_text(strip=True) and not div.find("img"):
            div.decompose()

    for div in soup.find_all("div"):
        div.unwrap()

    return soup

def extract_blog_content(html: str):
    soup = BeautifulSoup(html, "html.parser")

    # მთავარი article მოძებნე
    article = soup.find("article")
    if not article:
        for cls in ["blog-content", "post-content", "entry-content", "content", "article-body"]:
            article = soup.find("div", class_=cls)
            if article:
                break
    if not article:
        article = soup.body

    # არასასურველი selectors
    remove_selectors = [
        "ul.entry-meta",
        "div.entry-tags",
        "div.ct-share-box",
        "div.author-box",
        "nav.post-navigation",
        "div.wp-block-buttons",
        "aside",
        "header .entry-meta",
        "footer"
    ]
    for sel in remove_selectors:
        for tag in article.select(sel):
            tag.decompose()

    return clean_html(article)

@app.route("/scrape-blog", methods=["POST"])
def scrape_blog():
    try:
        data = request.get_json(force=True)
        url = data.get("url")
        if not url:
            return jsonify({"error": "Missing 'url' field"}), 400

        resp = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()

        article = extract_blog_content(resp.text)
        if not article:
            return jsonify({"error": "Could not extract blog content"}), 422

        # HTML ტექსტი
        clean_html_str = str(article).strip()

        # სურათების სია
        images = [img.get("src") for img in article.find_all("img") if img.get("src")]

        return jsonify({
            "html": clean_html_str,
            "images": images
        })

    except Exception as e:
        logging.exception("Error scraping blog")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
