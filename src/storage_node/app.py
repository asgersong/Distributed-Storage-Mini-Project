from flask import Flask, request, send_file
import os

app = Flask(__name__)

storage_dir = "./data"
if not os.path.exists(storage_dir):
    os.makedirs(storage_dir)

@app.route('/upload_fragment', methods=['POST'])
def upload_fragment():
    file_id = request.args.get('file_id')
    frag_idx = request.args.get('frag_idx')
    fragment = request.data
    path = os.path.join(storage_dir, f"{file_id}_{frag_idx}")
    with open(path, "wb") as f:
        f.write(fragment)
    return "OK"

@app.route('/get_fragment', methods=['GET'])
def get_fragment():
    file_id = request.args.get('file_id')
    frag_idx = request.args.get('frag_idx')
    path = os.path.join(storage_dir, f"{file_id}_{frag_idx}")
    if os.path.exists(path):
        return send_file(path, as_attachment=False)
    else:
        return "Not Found", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)