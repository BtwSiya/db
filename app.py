from flask import Flask, request, jsonify
import ijson
import os

app = Flask(__name__)

STATIC_API_KEY = "toxic" 
DB_FILES = ['db.json']

@app.route('/api', methods=['GET'])
def lookup_data():
    api_key = request.args.get('key')
    query = request.args.get('query')
    
    # 1. Fast API Key Verification
    if api_key != STATIC_API_KEY:
        return jsonify({"error": "Invalid API Key. Access Denied."}), 401
    
    if not query:
        return jsonify({"error": "Missing 'query' parameter."}), 400

    query = str(query).strip()
    
    # 2. Advanced Streaming / Chunking Search
    # Ye massive files ko bina RAM full kiye line-by-line scan karega
    for db_file in DB_FILES:
        if not os.path.exists(db_file):
            continue
            
        try:
            with open(db_file, 'r', encoding='utf-8') as f:
                # 'item' syntax assumes your db.json is an array like [{}, {}, ...]
                records = ijson.items(f, 'item')
                
                for record in records:
                    # Match query against fb_id, phone, or email
                    if (query == str(record.get('fb_id', ''))) or \
                       (query == str(record.get('phone', ''))) or \
                       (query == str(record.get('email', ''))):
                        return jsonify(record), 200
                        
        except Exception as e:
            print(f"⚠️ Error reading {db_file}: {e}")
            
    # Agar kisi bhi file me data na mile
    return jsonify({"error": "No matching record found."}), 404

if __name__ == '__main__':
    # Production me host='0.0.0.0' rakhein
    app.run(host='0.0.0.0', port=5000, debug=True)

