import os
import base64
import requests
from flask import Flask, request, jsonify
import openai

app = Flask(__name__)

# Env variables (Render Dashboard → Environment)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
WIX_API_KEY = os.environ.get("WIX_API_KEY")
WIX_FOLDER_ID = os.environ.get("WIX_FOLDER_ID")

openai.api_key = OPENAI_API_KEY


@app.route("/process-images", methods=["POST"])
def process_images():
    try:
        data = request.get_json(force=True)
        images = data.get("images", [])
        if not images:
            return jsonify({"error": "Missing 'images' array"}), 400

        restyled_urls = []

        for idx, src_url in enumerate(images):
            # 1. OpenAI image restyle
            result = openai.images.generate(
                model="gpt-image-1",
                prompt="Restyle this image into Gegidze brand style (blue #1663FF, white text strips, modern clean look)",
                size="1024x1024",
                image=[src_url]
            )

            img_b64 = result.data[0].b64_json
            img_bytes = base64.b64decode(img_b64)

            # 2. Upload to Wix Media Manager
            upload_resp = requests.post(
                "https://www.wixapis.com/media/v1/files/import",
                headers={
                    "Authorization": WIX_API_KEY,
                    "Content-Type": "application/json"
                },
                json={
                    "fileName": f"blog_image_{idx+1}.png",
                    "content": f"data:image/png;base64,{img_b64}",
                    "parentFolderId": WIX_FOLDER_ID
                }
            )
            upload_resp.raise_for_status()
            wix_url = upload_resp.json()["file"]["media"]["url"]
            restyled_urls.append(wix_url)

        return jsonify({"restyled_images": restyled_urls})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
