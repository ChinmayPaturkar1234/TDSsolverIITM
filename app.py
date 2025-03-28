import os
import logging
from flask import Flask, render_template, request, jsonify
from api import process_request

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "tds-solver-secret-key")

@app.route('/')
def index():
    """Render the main index page."""
    return render_template('index.html')

@app.route('/api/', methods=['POST'])
def api():
    """API endpoint to handle TDS course questions."""
    try:
        logger.debug("Received API request")
        # Extract question and file from request
        question = request.form.get('question')
        
        # Check if files were uploaded
        files = request.files.getlist('file') if 'file' in request.files else []
        
        logger.debug(f"Question: {question}")
        logger.debug(f"Files count: {len(files)}")
        
        if not question:
            return jsonify({"error": "No question provided"}), 400

        # Process the request
        answer = process_request(question, files)
        
        logger.debug(f"Generated answer: {answer}")
        return jsonify({"answer": answer})
    
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return jsonify({"error": f"Error processing request: {str(e)}"}), 500

# Error handlers
@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": "Bad request"}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Internal server error"}), 500
