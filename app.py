# app.py

from flask import Flask, request, jsonify, send_file
from verify import load_data, parse_gps, check_match
import pandas as pd
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Use this to track current file used for verification
current_data_file = None
results_df = pd.DataFrame()

@app.route('/')
def home():
    return "✅ Delivery Verification API is live."

@app.route('/upload_file', methods=['POST'])
def upload_file():
    global current_data_file
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        filename = file.filename
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        current_data_file = filepath
        return jsonify({'message': f'File {filename} uploaded successfully and ready for verification.'})

@app.route('/verify', methods=['GET'])
def verify_one():
    global current_data_file
    if not current_data_file:
        return jsonify({'error': 'No uploaded file found. Please upload one using /upload_file'}), 400

    data = load_data(current_data_file)
    barcode = request.args.get('barcode')
    if not barcode:
        return jsonify({'error': 'Barcode is required'}), 400

    row = data[data['Barcode'] == barcode.strip()]
    if row.empty:
        return jsonify({'error': 'Barcode not found'}), 404

    row = row.iloc[0]
    address = row['Address']
    gps = parse_gps(row['Last GPS location'])

    status, distance, expected, gmap_link = check_match(gps, address)
    return jsonify({
        'Barcode': barcode,
        'Address': address,
        'GPS Location': gps,
        'Expected Location': expected,
        'Distance (km)': distance,
        'Status': status,
        'Google Maps Link': gmap_link
    })

@app.route('/verify_all', methods=['GET'])
def verify_all():
    global current_data_file, results_df
    if not current_data_file:
        return jsonify({'error': 'No uploaded file found. Please upload one using /upload_file'}), 400

    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 25))
        if page < 1 or per_page < 1:
            raise ValueError
    except ValueError:
        return jsonify({'error': 'Invalid page or per_page parameter'}), 400

    data = load_data(current_data_file)
    total_items = len(data)
    total_pages = (total_items + per_page - 1) // per_page

    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_data = data.iloc[start_idx:end_idx]

    results = []
    for _, row in paginated_data.iterrows():
        barcode = row['Barcode']
        address = row['Address']
        gps = parse_gps(row['Last GPS location'])
        status, distance, expected, gmap_link = check_match(gps, address)
        results.append({
            'Barcode': barcode,
            'Address': address,
            'GPS Location': gps,
            'Expected Location': expected,
            'Distance (km)': distance,
            'Status': status,
            'Google Maps Link': gmap_link or "N/A"
        })

    # Save full results_df for optional download (just for current page)
    results_df = pd.DataFrame(results)

    return jsonify({
        'page': page,
        'per_page': per_page,
        'total_items': total_items,
        'total_pages': total_pages,
        'results': results
    })

@app.route('/download_excel', methods=['GET'])
def download_excel():
    global results_df
    if results_df.empty:
        return jsonify({'error': 'No verification results found. Please call /verify_all first.'}), 400
    excel_path = "verification_results.xlsx"
    results_df.to_excel(excel_path, index=False)
    return send_file(excel_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
