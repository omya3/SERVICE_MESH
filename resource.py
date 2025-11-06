from flask import Flask, jsonify


app = Flask(__name__)


@app.route('/content', methods=['GET'])
def send_content():
    return jsonify({"message": "Hello from Service 2!"}), 200

if __name__ == "__main__":
    print("Service 2: Running...")
    app.run(host="0.0.0.0", port=5001)
 # type: ignore