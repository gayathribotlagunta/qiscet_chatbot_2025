import os
import time
import json
from flask import Flask, render_template, request, jsonify
from google import genai
from google.genai.errors import APIError
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# --- CONFIGURATION & DATA ---

# Read the API key from the environment variable named 'BOT_API_KEY'
API_KEY = os.getenv("BOT_API_KEY")

# Check if the API key was successfully loaded
if not API_KEY:
    raise ValueError("The 'BOT_API_KEY' environment variable is not set. Cannot initialize Gemini Client.")

# Initialize the Gemini Client
# The `genai.configure()` method is not supported in your library version.
# Instead, we will pass the API key to the model instance directly.
client = genai.Client(api_key=API_KEY)


app = Flask(__name__)
app.config['ENV'] = 'development'
app.config['DEBUG'] = True


# --- UTILITY DATA ---

# Function to load transportation data from a local file
def load_transport_data(file_path):
    """Loads transportation data from a local file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Transportation data file not found at: {file_path}")

# Use a relative path to the data file
current_dir = os.path.dirname(os.path.abspath(__file__))
bus_data_path = os.path.join(current_dir, 'data', 'bus_data.txt')

# Load the data using the constructed path
TRANSPORT_DATA = load_transport_data(bus_data_path)

# 2. IoT Simulation Logic (for campus status)
def get_campus_status():
    """Simulates real-time campus metrics based on the time of day."""
    current_hour = datetime.now().hour

    # Simulate based on time
    if 9 <= current_hour < 16: # Peak academic hours
        ai_lab_occupancy = "High (85% occupied)"
        library_zone = "Moderately Busy"
        server_health = "Degraded (High Load)"
        wifi_status = "Operational (Moderate Speed)"
        power_source = "Main Grid"
    elif 16 <= current_hour < 20: # Evening/Lab hours
        ai_lab_occupancy = "Moderate (50% occupied)"
        library_zone = "Quiet Zone"
        server_health = "Operational (Normal)"
        wifi_status = "Operational (Fast Speed)"
        power_source = "Main Grid"
    else: # Night/Off-hours
        ai_lab_occupancy = "Low (5% occupied/Closed)"
        library_zone = "Closed"
        server_health = "Operational (Low Load)"
        wifi_status = "Operational (Low Speed)"
        power_source = "Main Grid"

    # Format the data into a dictionary suitable for JSON and text injection
    status_data = {
        "AI Lab 301 Occupancy": ai_lab_occupancy,
        "Library Quiet Zone": library_zone,
        "Main Server Health": server_health,
        "Campus Wi-Fi Status": wifi_status,
        "Power Supply": power_source
    }
    
    # Create the text injection for the AI prompt
    status_text = "\n\n# 💡 CURRENT CAMPUS STATUS (Use ONLY for live status queries)\n"
    status_text += json.dumps(status_data, indent=2) + "\n"

    return status_data, status_text

# --- FLASK ROUTES ---

@app.route('/')
def index():
    """Renders the main chat interface HTML page."""
    return render_template('index.html')

@app.route('/status')
def status():
    """API endpoint to return the current IoT campus status as JSON."""
    status_data, _ = get_campus_status()
    return jsonify(status_data)

@app.route('/chat', methods=['POST'])
def chat():
    """API endpoint to handle chat messages and call the Gemini API securely."""
    # Check if the client was initialized successfully
    if client is None:
        print("TERMINAL ERROR: Gemini Client failed to initialize. Cannot process chat.")
        return jsonify({"error": "An unexpected server error occurred. Please check the terminal for details."}), 500

    try:
        data = request.get_json()
        user_message = data.get('message', '')
        history = data.get('history', [])

        # 1. Get current campus status
        _, status_text = get_campus_status()

        # 2. Construct the system prompt with all current context
        system_prompt = f"""
        You are QIS Bot, the official AI Admissions Counselor for QIS College of Engineering and Technology (QISCET), Ongole.
        Your mission is to provide concise, accurate, and helpful information to prospective students.
        
        CRITICAL INSTRUCTIONS:
        1. **Be Concise:** Keep answers brief (2-3 sentences max) and professional.
        2. **Use Search Tool:** Use the Google Search tool for current, general information (like admissions, specific courses, fees, and job placements).
        3. **Use Embedded Data:** Use the provided TRANSPORTATION DATA and CAMPUS STATUS below to answer specific questions.
        4. **Maintain Persona:** Maintain a friendly, supportive tone.
        
        ---
        
        # 📚 QISCET KEY FACTS
        - Location: Vengamukkapalem, Ongole, Prakasam District, Andhra Pradesh.
        - Affiliation: Jawaharlal Nehru Technological University (JNTUK), Kakinada.
        - Programs: B.Tech (CSE, ECE, EEE, Mechanical, Civil, IT, AI & ML, Data Science), M.Tech, MBA, MCA.
        
        ---
        
        # 🚌 TRANSPORTATION DATA (Use ONLY for bus/route/driver queries)
        {TRANSPORT_DATA}
        
        ---
        
        {status_text}
        
        """
        
        # 3. Add the new user message to the history list
        full_history = []
        for message in history:
            full_history.append({
                "role": message["role"],
                "parts": [{"text": message["text"]}]
            })
            
        full_history.append({
            "role": "user",
            "parts": [{"text": user_message}]
        })

        # 4. Call the Gemini API
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=full_history,
            config={
                'system_instruction': system_prompt,
                'tools': [{"google_search": {}}]
            }
        )

        # 5. Extract text and sources with safety checks
        response_text = ""
        sources = []
        
        if response.candidates and response.candidates[0].content:
            response_text = response.candidates[0].content.parts[0].text
            
            # Robust check for grounding metadata
            grounding_metadata = getattr(response.candidates[0], 'grounding_metadata', None)
            
            if grounding_metadata and getattr(grounding_metadata, 'grounding_attributions', None):
                sources = [
                    {'uri': attr.web.uri, 'title': attr.web.title}
                    for attr in grounding_metadata.grounding_attributions
                    if getattr(attr, 'web', None) and attr.web.uri and attr.web.title
                ]
        
        if not response_text:
            raise Exception("API returned an empty text response.")

        return jsonify({
            "response": response_text,
            "sources": sources
        })

    except APIError as e:
        print(f"TERMINAL ERROR: Gemini API call failed: {e}")
        # Return a user-friendly error message
        return jsonify({"error": f"The Gemini AI service is currently unavailable. (API Error: {str(e)[:50]}...)"}), 500
    except Exception as e:
        # This catches all other Python errors
        print(f"TERMINAL ERROR: Unhandled Python error in /chat route: {e}")
        return jsonify({"error": "An unexpected server error occurred. Please check the terminal for details."}), 500

if __name__ == '__main__':
    # Flask development server starter
    app.run(host='0.0.0.0', port=8080)