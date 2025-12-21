"""
KrouAI Bakong Payment Backend
Handles KHQR payment generation and verification
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from bakong_khqr import KHQR
from supabase import create_client, Client
from dotenv import load_dotenv
import os
import hashlib
import time

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app, origins=["http://127.0.0.1:5500", "https://krouai.com", "https://*.github.io"])

# Initialize Bakong KHQR
BAKONG_TOKEN = os.getenv('BAKONG_TOKEN')
BAKONG_ACCOUNT = os.getenv('BAKONG_ACCOUNT')
khqr = KHQR(BAKONG_TOKEN)

# Initialize Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Credit packages
CREDIT_PACKAGES = {
    '20': {'credits': 20, 'price_khr': 2000, 'price_usd': 0.50},
    '50': {'credits': 50, 'price_khr': 4500, 'price_usd': 1.10},
    '100': {'credits': 100, 'price_khr': 8000, 'price_usd': 2.00},
}


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'service': 'KrouAI Bakong Payment'})


@app.route('/api/create-payment', methods=['POST'])
def create_payment():
    """
    Create a new KHQR payment QR code
    
    Request body:
    {
        "user_id": "user-uuid-from-supabase",
        "package": "20" | "50" | "100",
        "currency": "KHR" | "USD"
    }
    """
    try:
        data = request.json
        user_id = data.get('user_id')
        package_id = data.get('package', '20')
        currency = data.get('currency', 'KHR')
        
        if not user_id:
            return jsonify({'error': 'user_id is required'}), 400
        
        if package_id not in CREDIT_PACKAGES:
            return jsonify({'error': 'Invalid package'}), 400
        
        package = CREDIT_PACKAGES[package_id]
        amount = package['price_khr'] if currency == 'KHR' else package['price_usd']
        
        # Generate unique bill number
        timestamp = int(time.time())
        bill_number = f"KROU{timestamp}"
        
        # Create KHQR
        qr_string = khqr.create_qr(
            bank_account=BAKONG_ACCOUNT,
            merchant_name='KrouAI',
            merchant_city='Phnom Penh',
            amount=amount,
            currency=currency,
            store_label='KrouAI Credits',
            phone_number='',
            bill_number=bill_number,
            terminal_label=f'{package["credits"]} Credits',
            static=False  # Dynamic QR (one-time use)
        )
        
        # Generate MD5 hash for tracking
        md5_hash = khqr.generate_md5(qr_string)
        
        # Generate deeplink for mobile
        deeplink = khqr.generate_deeplink(
            qr_string,
            callback=f"https://krouai.com/?payment_success=true&bill={bill_number}",
            appIconUrl="https://krouai.com/logo.png",
            appName="KrouAI"
        )
        
        # Store pending payment in Supabase
        supabase.table('pending_payments').insert({
            'user_id': user_id,
            'bill_number': bill_number,
            'md5_hash': md5_hash,
            'credits': package['credits'],
            'amount': amount,
            'currency': currency,
            'status': 'pending',
            'qr_string': qr_string
        }).execute()
        
        return jsonify({
            'success': True,
            'qr_string': qr_string,
            'md5_hash': md5_hash,
            'deeplink': deeplink,
            'bill_number': bill_number,
            'credits': package['credits'],
            'amount': amount,
            'currency': currency
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/check-payment', methods=['POST'])
def check_payment():
    """
    Check if a payment has been completed
    
    Request body:
    {
        "md5_hash": "hash-from-create-payment"
    }
    """
    try:
        data = request.json
        md5_hash = data.get('md5_hash')
        
        if not md5_hash:
            return jsonify({'error': 'md5_hash is required'}), 400
        
        # Check payment status with Bakong
        status = khqr.check_payment(md5_hash)
        
        if status == 'PAID':
            # Get pending payment from database
            result = supabase.table('pending_payments').select('*').eq('md5_hash', md5_hash).single().execute()
            
            if result.data and result.data['status'] == 'pending':
                payment = result.data
                user_id = payment['user_id']
                credits_to_add = payment['credits']
                
                # Update user credits
                user_credits = supabase.table('user_credits').select('credits').eq('user_id', user_id).single().execute()
                
                if user_credits.data:
                    new_credits = user_credits.data['credits'] + credits_to_add
                    supabase.table('user_credits').update({'credits': new_credits}).eq('user_id', user_id).execute()
                else:
                    # Create new record
                    supabase.table('user_credits').insert({
                        'user_id': user_id,
                        'credits': credits_to_add,
                        'unlocked_books': []
                    }).execute()
                
                # Mark payment as completed
                supabase.table('pending_payments').update({'status': 'completed'}).eq('md5_hash', md5_hash).execute()
                
                return jsonify({
                    'status': 'PAID',
                    'credits_added': credits_to_add,
                    'message': f'Successfully added {credits_to_add} credits!'
                })
            else:
                return jsonify({'status': 'PAID', 'message': 'Already processed'})
        
        return jsonify({'status': status})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/payment-info', methods=['POST'])
def get_payment_info():
    """
    Get detailed payment information
    
    Request body:
    {
        "md5_hash": "hash-from-create-payment"
    }
    """
    try:
        data = request.json
        md5_hash = data.get('md5_hash')
        
        if not md5_hash:
            return jsonify({'error': 'md5_hash is required'}), 400
        
        # Get payment info from Bakong
        payment_info = khqr.get_payment(md5_hash)
        
        return jsonify({
            'success': True,
            'payment': payment_info
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.getenv('FLASK_ENV') == 'development')

