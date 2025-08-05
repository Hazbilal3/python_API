from flask import Flask, request, jsonify
from verify import load_data, parse_gps, check_match

app = Flask(__name__)
data = load_data()

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
    gps_str = row['Last GPS location']
    gps = parse_gps(gps_str)

    status, distance, expected_coords = check_match(gps, address)
    return jsonify({
        'Barcode': barcode,
        'Address': address,
        'GPS Location': gps,
        'Expected Location': expected_coords,
        'Distance (km)': distance,
        'Status': status
    })

@app.route('/verify_all', methods=['GET'])
def verify_all():
    results = []
    for _, row in data.iterrows():
        barcode = row['Barcode']
        address = row['Address']
        gps_str = row['Last GPS location']
        gps = parse_gps(gps_str)
        status, distance, expected_coords = check_match(gps, address)
        results.append({
            'Barcode': barcode,
            'Address': address,
            'GPS Location': gps,
            'Expected Location': expected_coords,
            'Distance (km)': distance,
            'Status': status
        })
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)
