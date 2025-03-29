from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
from datetime import datetime
from enum import Enum

app = Flask(__name__)

# Configure Gemini - replace with your actual API key
GEMINI_API_KEY = "AIzaSyAEB81H4V45ruTP0VwPrqHt5A_66wkUzpQ"

class AgentType(Enum):
    GENERALIST = "general"
    TECHNICAL = "technical"
    CREATIVE = "creative"
    ANALYTICAL = "analytical"

try:
    genai.configure(api_key=GEMINI_API_KEY)
    
    # Initialize multiple specialized agents
    agents = {
        AgentType.GENERALIST: genai.GenerativeModel('gemini-1.5-flash'),
        AgentType.TECHNICAL: genai.GenerativeModel('gemini-1.5-pro'),
        AgentType.CREATIVE: genai.GenerativeModel('gemini-1.5-flash'),
        AgentType.ANALYTICAL: genai.GenerativeModel('gemini-1.5-pro')
    }
    
    # Configure specialized system instructions
    agent_personas = {
        AgentType.TECHNICAL: "You are a technical expert specializing in programming, systems design, and technology. "
                            "Provide detailed, accurate technical answers with code examples when appropriate.",
        AgentType.CREATIVE: "You are a creative writer and artist. Provide imaginative, engaging responses with "
                          "storytelling elements and creative suggestions.",
        AgentType.ANALYTICAL: "You are a data analyst and critical thinker. Provide structured, logical responses "
                             "with pros/cons analysis and data-driven insights."
    }
    
    print("✅ Multi-agent system initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize agents: {e}")
    agents = None

chat_history = []

def route_to_agent(user_message):
    """Determine which agent should handle the message"""
    technical_keywords = ['code', 'programming', 'algorithm', 'python', 'java', 'debug']
    creative_keywords = ['story', 'poem', 'creative', 'write', 'art', 'imagine']
    analytical_keywords = ['analyze', 'compare', 'statistics', 'data', 'research']
    
    message_lower = user_message.lower()
    
    if any(keyword in message_lower for keyword in technical_keywords):
        return AgentType.TECHNICAL
    elif any(keyword in message_lower for keyword in creative_keywords):
        return AgentType.CREATIVE
    elif any(keyword in message_lower for keyword in analytical_keywords):
        return AgentType.ANALYTICAL
    else:
        return AgentType.GENERALIST

@app.route('/')
def home():
    return render_template('mainpage.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    if not agents:
        return jsonify({'error': 'AI service unavailable'}), 503
    
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Empty message'}), 400
        
        # Determine which agent to use
        selected_agent = route_to_agent(user_message)
        agent = agents[selected_agent]
        
        # Prepare the prompt with persona if specialized agent
        prompt = user_message
        if selected_agent in agent_personas:
            prompt = f"{agent_personas[selected_agent]}\n\nUser: {user_message}"
        
        # Get AI response
        response = agent.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7 if selected_agent == AgentType.CREATIVE else 0.3,
                max_output_tokens=2048
            )
        )
        
        timestamp = datetime.now().strftime("%H:%M")
        bot_response = response.text
        
        # Store conversation with agent type
        chat_history.append({
            'user': user_message,
            'bot': bot_response,
            'time': timestamp,
            'agent': selected_agent.value
        })
        
        return jsonify({
            'response': bot_response,
            'time': timestamp,
            'agent': selected_agent.value
        })
        
    except Exception as e:
        print(f"Chat error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    return jsonify(chat_history)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)