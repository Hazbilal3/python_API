from flask import Flask, request, jsonify, send_file
from verify import load_data, parse_gps, check_match
import pandas as pd

app = Flask(__name__)
data = load_data()
results_df = pd.DataFrame()  # Global placeholder for Excel download

@app.route('/')
def home():
    return "✅ Delivery Verification API is live."

@app.route('/verify', methods=['GET'])
def verify_one():
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
    global results_df
    results = []
    for _, row in data.iterrows():
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
            'Google Maps Link': f'<a href="{gmap_link}" target="_blank">Open in Maps</a>' if gmap_link else "N/A"
        })

    results_df = pd.DataFrame(results)

    # ✅ Show result as HTML table (in browser)
    return results_df.to_html(index=False, escape=False, justify="center", border=1)


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
