from flask import Flask, render_template, request, send_file, jsonify
import markdown
import os
from trip_prep_final import TripPrepSystem

app = Flask(__name__)

# Initialize the system once
system = TripPrepSystem()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.json
        destination = data.get('destination')
        keywords = data.get('keywords', [])
        
        if not destination:
            return jsonify({'error': 'Destination is required'}), 400
            
        # Generate the report
        report_md = system.generate_report(destination, keywords)
        
        # Convert Markdown to HTML for display (optional, can be done in frontend too)
        # But we'll send the raw markdown to let the frontend handle it or just display it.
        # Let's send raw markdown and let frontend render it with marked.js for better control.
        
        return jsonify({'report': report_md})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
