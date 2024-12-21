from flask import Flask, request, jsonify
from file_handler import FileHandler

app = Flask(__name__)
file_handler = FileHandler()

# Web Page
@app.route('/')
def index():
    return "Welcome to the Distributed Storage System!"

@app.route('/store', methods=['POST'])
def store_endpoint():
    file_bytes = request.get_data()
    print("Received file length from get_data():", len(file_bytes))
    
    file_id = file_handler.store_file(file_bytes)
    # TODO: return http response
    return jsonify({"file_id": file_id})

@app.route('/retrieve', methods=['GET'])
def retrieve_endpoint():
    file_id = request.args.get('file_id')
    file_data = file_handler.retrieve_file(file_id)
    return file_data

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4000)