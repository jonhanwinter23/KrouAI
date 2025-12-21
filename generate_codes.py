"""
Generate 1000 unique unlock codes for KrouAI
Run this once to create codes, then upload to GitHub
"""

import json
import random
import string
from datetime import datetime

def generate_code(prefix='KR'):
    """Generate a unique code"""
    chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'  # No confusing chars (0,O,1,I,L)
    suffix = ''.join(random.choice(chars) for _ in range(6))
    return f"{prefix}{suffix}"

def generate_codes(count=1000, prefix='KR'):
    """Generate multiple unique codes"""
    codes = set()
    while len(codes) < count:
        codes.add(generate_code(prefix))
    return sorted(list(codes))

if __name__ == '__main__':
    print("🎟️ Generating 1000 unique codes...")
    
    codes = generate_codes(1000, 'KR')
    
    # Save as simple list for the app
    with open('App/valid_codes.json', 'w') as f:
        json.dump(codes, f, indent=2)
    
    # Save detailed version for your records
    detailed = [{
        'code': code,
        'index': i + 1,
        'given_to': '',  # You fill this in
        'date_given': '',
        'notes': ''
    } for i, code in enumerate(codes)]
    
    with open('codes_master_list.json', 'w') as f:
        json.dump(detailed, f, indent=2)
    
    # Also save as CSV for easy viewing in Excel/Sheets
    with open('codes_master_list.csv', 'w') as f:
        f.write('Index,Code,Given To,Date Given,Notes\n')
        for i, code in enumerate(codes):
            f.write(f'{i+1},{code},,,\n')
    
    print(f"✅ Generated {len(codes)} codes!")
    print(f"\n📁 Files created:")
    print(f"   App/valid_codes.json  - For the website (upload this)")
    print(f"   codes_master_list.json - Your records (keep private)")
    print(f"   codes_master_list.csv  - Open in Excel/Sheets to track")
    print(f"\n📋 Sample codes:")
    for code in codes[:10]:
        print(f"   {code}")
    print(f"   ... and {len(codes) - 10} more")







