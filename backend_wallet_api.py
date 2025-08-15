from dotenv import load_dotenv
load_dotenv()
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client

app = Flask(__name__)
CORS(app)

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/api/wallets', methods=['GET'])
def get_wallets():
    res = supabase.table('tracked_wallets').select('*').execute()
    if res.status_code == 200:
        return jsonify(res.data)
    return jsonify([]), 500

@app.route('/api/wallets', methods=['POST'])
def add_wallet():
    data = request.json
    address = data.get('address')
    chain = data.get('chain', 'Base')
    if not address:
        return jsonify({'success': False, 'error': 'Missing address'}), 400
    res = supabase.table('tracked_wallets').insert({'address': address, 'chain': chain}).execute()
    return jsonify({'success': res.status_code == 201})

@app.route('/api/wallets/<address>', methods=['DELETE'])
def delete_wallet(address):
    res = supabase.table('tracked_wallets').delete().eq('address', address).execute()
    return jsonify({'success': res.status_code == 200})

if __name__ == '__main__':
    app.run(port=5000, debug=True)
