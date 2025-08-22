from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import google.generativeai as genai
import json
import uuid
from datetime import datetime
import sqlite3
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from functools import wraps
import requests
from bs4 import BeautifulSoup
import urllib.parse

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
CORS(app)

# Database initialization
def init_db():
    conn = sqlite3.connect('debate_coach.db')
    c = conn.cursor()

    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id TEXT PRIMARY KEY, username TEXT UNIQUE, email TEXT UNIQUE,
                  password_hash TEXT, created_at TIMESTAMP)''')

    # Debates table
    c.execute('''CREATE TABLE IF NOT EXISTS debates
                 (id TEXT PRIMARY KEY, user_id TEXT, topic TEXT, position TEXT,
                  arguments TEXT, feedback TEXT, score INTEGER, created_at TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')

    # Chat sessions table
    c.execute('''CREATE TABLE IF NOT EXISTS chat_sessions
                 (id TEXT PRIMARY KEY, user_id TEXT, messages TEXT,
                  created_at TIMESTAMP, updated_at TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')

    conn.commit()
    conn.close()

# AI Configuration
class DebateAI:
    def __init__(self):
        # Configure Gemini API
        self.api_key = "AIzaSyCgAsam0cez74MgCBB-grTUuJZNFO57P6A"
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None
        self.serpapi_key = os.environ.get('SERPAPI_KEY')  # For web search

    def search_web_facts(self, query, num_results=3):
        """Search the web for factual information to support arguments"""
        try:
            if self.serpapi_key:
                # Using SerpAPI for reliable search results
                url = "https://serpapi.com/search"
                params = {
                    "engine": "google",
                    "q": query,
                    "api_key": self.serpapi_key,
                    "num": num_results
                }
                response = requests.get(url, params=params)
                results = response.json()

                facts = []
                if "organic_results" in results:
                    for result in results["organic_results"][:num_results]:
                        facts.append({
                            "title": result.get("title", ""),
                            "snippet": result.get("snippet", ""),
                            "source": result.get("link", "")
                        })
                return facts
            else:
                # Fallback: Basic web scraping (less reliable)
                search_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                response = requests.get(search_url, headers=headers, timeout=5)

                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    snippets = soup.find_all('span', class_='aCOpRe')
                    facts = []
                    for snippet in snippets[:num_results]:
                        if snippet.text:
                            facts.append({
                                "title": "Search Result",
                                "snippet": snippet.text,
                                "source": "Google Search"
                            })
                    return facts

        except Exception as e:
            print(f"Web search error: {e}")

        return []

    def start_debate(self, topic, user_position):
        """Initialize debate and determine AI position"""
        ai_position = "against" if user_position == "for" else "for"

        ai_message = f"Let's initiate this debate on '{topic}'. Your stance is {user_position}, and mine is {ai_position}. I'll be taking the {ai_position} position. Please present your opening argument, and I'll provide detailed feedback on your debate performance after each message."

        return {
            "ai_position": ai_position,
            "ai_message": ai_message
        }

    def analyze_debate_message(self, topic, user_position, user_message, message_context, message_count):
        """Analyze user's debate message in context and provide detailed feedback with perfect answer"""

        # Search for relevant facts to support analysis
        search_query = f"{topic} evidence statistics facts research"
        web_facts = self.search_web_facts(search_query)

        fact_context = ""
        if web_facts:
            fact_context = "Recent web research findings:\n"
            for fact in web_facts:
                fact_context += f"- {fact['snippet']}\n"

        prompt = f"""
        You are an expert debate coach analyzing a debate message. Here's the context:

        Debate Topic: {topic}
        User's Position: {user_position}
        Message #{message_count}
        User's Message: {user_message}
        Previous Context: {message_context[-3:] if message_context else 'This is the opening statement'}

        {fact_context}

        Analyze this message and provide detailed feedback in the following JSON format:
        {{
            "score": [1-10 score based on argument quality, evidence, structure, persuasiveness],
            "strengths": ["specific positive elements in this argument"],
            "improvements": ["specific actionable improvements"],
            "counterarguments": ["actual counterarguments opponents would make"],
            "evidence": ["specific types of evidence that would strengthen this exact argument"],
            "overall_feedback": "comprehensive coaching feedback paragraph",
            "perfect_answer": "A complete, well-structured argument that demonstrates what they should have said - include specific facts, evidence, and persuasive language. Make this a full argument, not a description."
        }}

        For the perfect_answer: Write an actual debate argument that addresses the same point but with superior structure, evidence, and persuasiveness. Include specific facts where possible.
        """

        try:
            if self.model:
                # More explicit instruction for JSON format
                json_prompt = prompt + """

                IMPORTANT: Return ONLY a valid JSON object with no additional text, markdown formatting, or explanations. The response must start with { and end with }.
                """

                response = self.model.generate_content(json_prompt)
                result_text = response.text.strip()

                # Clean up the response to ensure it's valid JSON
                if result_text.startswith('```json'):
                    result_text = result_text.replace('```json', '').replace('```', '').strip()
                elif result_text.startswith('```'):
                    result_text = result_text.replace('```', '').strip()

                try:
                    result = json.loads(result_text)
                except json.JSONDecodeError:
                    # If JSON parsing fails, create a structured response
                    print(f"JSON parsing failed for: {result_text[:200]}...")
                    result = {
                        "score": 7,
                        "strengths": ["Clear argument presentation", "Relevant to the topic"],
                        "improvements": ["Add more specific evidence", "Address counterarguments"],
                        "counterarguments": ["Opponents may argue differently", "Alternative perspectives exist"],
                        "evidence": ["Statistical data needed", "Expert opinions would help"],
                        "overall_feedback": f"Your argument on {topic} shows good understanding. Consider strengthening with more evidence.",
                        "perfect_answer": f"A stronger argument would include specific examples and data to support your {user_position} position on {topic}."
                    }

                # Enhance perfect answer with web facts if available
                if web_facts and 'perfect_answer' in result:
                    enhanced_answer = result['perfect_answer']
                    relevant_fact = web_facts[0]['snippet'] if web_facts else ""
                    if relevant_fact and len(relevant_fact) > 20:
                        enhanced_answer += f" According to recent research, {relevant_fact}"
                    result['perfect_answer'] = enhanced_answer

                return result
            else:
                # This will not be used since we have a valid API key
                raise Exception("Gemini API not configured")

        except Exception as e:
            print(f"Gemini API error: {e}")
            # Remove placeholder responses - force real API usage
            raise Exception(f"API Error: {e}. Please check your Gemini API key configuration.")

    def generate_ai_response(self, topic, ai_position, user_message, message_context):
        """Generate AI's counter-response in the debate with web-researched facts"""

        # Search for facts supporting the AI's position
        search_query = f"{topic} {ai_position} arguments evidence research"
        web_facts = self.search_web_facts(search_query)

        fact_context = ""
        if web_facts:
            fact_context = "Use these recent facts in your response:\n"
            for fact in web_facts:
                fact_context += f"- {fact['snippet']}\n"

        try:
            if self.model:
                prompt = f"""
                You are debating the topic: {topic}
                Your position: {ai_position}
                User just said: {user_message}
                Previous context: {message_context[-2:] if message_context else 'Opening'}

                {fact_context}

                Provide a thoughtful counter-response that:
                1. Acknowledges their point respectfully
                2. Presents a strong {ai_position} argument with specific evidence
                3. Uses facts from the research provided when relevant
                4. Challenges their reasoning while maintaining a coaching tone
                5. Asks a thought-provoking question to advance the debate

                Keep response conversational but substantive (150-250 words).
                """

                response = self.model.generate_content(prompt)
                return response.text
            else:
                # This will not be used since we have a valid API key
                raise Exception("Gemini API not configured")

        except Exception as e:
            print(f"Gemini AI response error: {e}")
            # Remove placeholder responses - force real API usage
            raise Exception(f"API Error: {e}. Please check your Gemini API key configuration.")

    def generate_practice_question(self, topic, difficulty="medium"):
        """Generate practice debate questions"""
        prompt = f"""
        Generate a debate practice question for the topic: {topic}
        Difficulty: {difficulty}

        Include:
        1. A specific question or motion
        2. Key points to consider
        3. Potential research areas
        4. Time limit suggestion
        """

        # Mock response
        return {
            "question": f"Should {topic} be regulated more strictly?",
            "key_points": ["Economic impact", "Social implications", "Ethical considerations"],
            "research_areas": ["Current policies", "Case studies", "Expert opinions"],
            "time_limit": "5 minutes preparation, 3 minutes presentation"
        }

debate_ai = DebateAI()

# Authentication decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        try:
            token = token.split(' ')[1]  # Remove 'Bearer ' prefix
            # Accept demo token for testing
            if token == 'demo-session-token':
                current_user = 'demo-user'
            else:
                data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
                current_user = data['user_id']
        except:
            return jsonify({'message': 'Token is invalid'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not all([username, email, password]):
        return jsonify({'error': 'Missing required fields'}), 400

    user_id = str(uuid.uuid4())
    password_hash = generate_password_hash(password)

    try:
        conn = sqlite3.connect('debate_coach.db')
        c = conn.cursor()
        c.execute('INSERT INTO users VALUES (?, ?, ?, ?, ?)',
                 (user_id, username, email, password_hash, datetime.now()))
        conn.commit()
        conn.close()

        token = jwt.encode({'user_id': user_id}, app.config['SECRET_KEY'], algorithm='HS256')
        return jsonify({'token': token, 'user_id': user_id, 'username': username})

    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username or email already exists'}), 400

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    conn = sqlite3.connect('debate_coach.db')
    c = conn.cursor()
    c.execute('SELECT id, username, password_hash FROM users WHERE username = ?', (username,))
    user = c.fetchone()
    conn.close()

    if user and check_password_hash(user[2], password):
        token = jwt.encode({'user_id': user[0]}, app.config['SECRET_KEY'], algorithm='HS256')
        return jsonify({'token': token, 'user_id': user[0], 'username': user[1]})

    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/debate/start', methods=['POST'])
def start_debate():
    data = request.get_json()
    topic = data.get('topic')
    position = data.get('position')

    if not all([topic, position]):
        return jsonify({'error': 'Missing required fields'}), 400

    # Store in session
    session['topic'] = topic
    session['position'] = position

    # Initialize debate with AI
    result = debate_ai.start_debate(topic, position)

    # Store debate session in database
    debate_id = str(uuid.uuid4())
    current_user = 'demo-user'  # Demo user for testing
    conn = sqlite3.connect('debate_coach.db')
    c = conn.cursor()
    c.execute('INSERT INTO debates VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
             (debate_id, current_user, topic, position,
              json.dumps([]), json.dumps([]), 0, datetime.now()))
    conn.commit()
    conn.close()

    return jsonify({
        'debate_id': debate_id,
        'ai_position': result['ai_position'],
        'ai_message': result['ai_message']
    })

@app.route('/api/debate/analyze', methods=['POST'])
def analyze_debate():
    data = request.get_json()
    topic = data.get('topic')
    position = data.get('position')
    argument = data.get('argument')

    if not all([topic, position, argument]):
        return jsonify({'error': 'Missing required fields'}), 400

    # Get AI feedback
    feedback = debate_ai.analyze_debate_message(topic, position, argument, [], 1)

    # Save to database
    debate_id = str(uuid.uuid4())
    current_user = 'demo-user'  # Demo user for testing
    conn = sqlite3.connect('debate_coach.db')
    c = conn.cursor()
    c.execute('INSERT INTO debates VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
             (debate_id, current_user, topic, position, argument,
              json.dumps(feedback), feedback.get('score', 0), datetime.now()))
    conn.commit()
    conn.close()

    return jsonify({'debate_id': debate_id, 'feedback': feedback})@app.route('/api/practice/question', methods=['POST'])
@token_required
def get_practice_question(current_user):
    data = request.get_json()
    topic = data.get('topic', 'general debate')
    difficulty = data.get('difficulty', 'medium')

    question = debate_ai.generate_practice_question(topic, difficulty)
    return jsonify(question)

@app.route('/api/debates/history', methods=['GET'])
@token_required
def get_debate_history(current_user):
    conn = sqlite3.connect('debate_coach.db')
    c = conn.cursor()
    c.execute('SELECT * FROM debates WHERE user_id = ? ORDER BY created_at DESC', (current_user,))
    debates = c.fetchall()
    conn.close()

    debate_list = []
    for debate in debates:
        debate_list.append({
            'id': debate[0],
            'topic': debate[2],
            'position': debate[3],
            'argument': debate[4],
            'feedback': json.loads(debate[5]),
            'score': debate[6],
            'created_at': debate[7]
        })

    return jsonify(debate_list)

# Store active debate sessions
active_debates = {}

# Real-time chat with AI
@socketio.on('connect')
def handle_connect(auth):
    print(f'Client connected with auth: {auth}')
    print(f'Session: {session}')

@socketio.on('debate_message')
def handle_debate_message(data):
    print(f"=== SOCKET.IO DEBUG: Received debate_message ===")
    print(f"Data: {data}")

    user_message = data['message']
    topic = data['topic']
    user_position = data['position']
    message_count = data.get('message_count', 1)
    user_id = data.get('user_id', 'anonymous')

    # Get or create debate session
    session_key = f"{user_id}_{topic}"
    if session_key not in active_debates:
        active_debates[session_key] = {
            'topic': topic,
            'user_position': user_position,
            'ai_position': 'against' if user_position == 'for' else 'for',
            'messages': []
        }

    debate_session = active_debates[session_key]
    debate_session['messages'].append({
        'sender': 'user',
        'message': user_message,
        'count': message_count
    })

    # Get AI analysis of the user's message
    feedback = debate_ai.analyze_debate_message(
        topic,
        user_position,
        user_message,
        debate_session['messages'],
        message_count
    )

    # Generate AI's response
    ai_response = debate_ai.generate_ai_response(
        topic,
        debate_session['ai_position'],
        user_message,
        debate_session['messages']
    )

    # Add AI response to session
    debate_session['messages'].append({
        'sender': 'ai',
        'message': ai_response,
        'count': message_count
    })

    # Send feedback and AI response to client
    print(f"=== SOCKET.IO DEBUG: Sending responses ===")
    print(f"Sending feedback: {feedback}")
    print(f"Sending AI response: {ai_response}")
    emit('debate_feedback', {'feedback': feedback})
    emit('ai_response', {'message': ai_response})
    print(f"=== SOCKET.IO DEBUG: Responses sent ===")

@socketio.on('chat_message')
def handle_chat_message(data):
    # Legacy handler for backward compatibility
    user_message = data['message']
    user_id = data.get('user_id')

    # Professional response logic
    responses = {
        'hello': "Welcome! I'm your AI debate coach. Please set a debate topic first to begin our structured debate session.",
        'help': "To start, please choose a debate topic and your position using the topic setup form above.",
        'topic': "Please use the debate setup form to choose your topic and position, then we can begin our structured debate with real-time feedback.",
    }

    # Professional keyword matching
    ai_response = "Please set up a debate topic first using the form above. Once we have a topic and your position, we can begin our debate with detailed AI feedback and analysis."
    user_lower = user_message.lower()

    for keyword, response in responses.items():
        if keyword in user_lower:
            ai_response = response
            break

    # Emit response back to client
    emit('ai_response', {'message': ai_response})

# Health check endpoint
@app.route('/api/health')
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    init_db()
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)