from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/content')
def content():
    return jsonify({"message": "Hello from Service2!"})

if __name__ == "__main__":
    app.run("0.0.0.0", 5001)
