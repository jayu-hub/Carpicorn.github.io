# Required libraries are listed in requirements.txt
# No need to install them manually when deploying.

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os # Import the 'os' library to access environment variables

# Initialize the Flask application
app = Flask(__name__)
# Enable Cross-Origin Resource Sharing (CORS) to allow browser requests
CORS(app)

# --- CONFIGURATION (THE SECURE WAY) ---
# Get the API key from an environment variable called GEMINI_API_KEY.
# This is much more secure than writing the key directly in the code.
API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL_NAME = "gemini-1.5-flash-preview-0514" # Using a standard available model
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={API_KEY}"

@app.route('/chat', methods=['POST'])
def chat():
    """ This function listens for messages from the front-end """
    # First, check if the API key is available.
    if not API_KEY:
        print("ERROR: GEMINI_API_KEY environment variable not set.")
        return jsonify({'error': 'The server is not configured with an API key.'}), 500

    try:
        user_message = request.json.get('message')
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400

        headers = {'Content-Type': 'application/json'}
        
        # --- CORRECTED PAYLOAD ---
        # The API expects `systemInstruction`, not `system_instruction`.
        payload = {
            "systemInstruction": {
                "parts": [
                    {"text": "You are a helpful AI assistant. If and only if the user asks a question about who created or built you, you must respond with the exact phrase: 'I was built by Mr. Jay Nikam.' For all other questions, respond normally."}
                ]
            },
            "contents": [{"parts": [{"text": user_message}]}]
        }
        
        api_response = requests.post(GEMINI_API_URL, headers=headers, json=payload)
        api_response.raise_for_status()
        
        data = api_response.json()

        # --- SAFER RESPONSE HANDLING ---
        if 'candidates' in data and data['candidates']:
            candidate = data['candidates'][0]
            if 'content' in candidate and 'parts' in candidate['content'] and candidate['content']['parts']:
                ai_text = candidate['content']['parts'][0]['text']
                return jsonify({'response': ai_text})
        
        print("AI response was not in the expected format:", data)
        return jsonify({'response': "Sorry, I received an unusual response from the AI."})

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        # Provide more detail from the API's error response
        error_details = http_err.response.json()
        print("API Error Details:", error_details)
        # Check for common API key error
        if http_err.response.status_code == 400:
             return jsonify({'error': 'An error occurred with the AI service. Check if the API key is correct and valid.'}), 500
        return jsonify({'error': 'An error occurred with the AI service API.'}), 500
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({'error': 'An internal server error occurred.'}), 500

# This part is only for running the app on your local computer for testing.
# A production server like Gunicorn will run the 'app' object directly.
if __name__ == '__main__':
    # Note: When deploying, Gunicorn runs the app. This section is not used.
    app.run(host='0.0.0.0', port=5000, debug=True)
