from flask import Flask, jsonify
import requests

app = Flask(__name__)

@app.route('/request-content')
def get_content_from_service2():
    url = "http://service2:5001/content"  # Use service name in Docker Compose
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return jsonify({"content": response.text})
        else:
            return jsonify({"error": f"Failed to fetch content. Status code: {response.status_code}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
