from flask import Flask, Response
app = Flask(__name__)

@app.route('/', methods=['POST'])
def main():
    return Response(status=200)

if __name__ == "__main__":
    app.run(debug=True, port=12345, host="0.0.0.0")