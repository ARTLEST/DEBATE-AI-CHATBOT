# 🎯 Debate Coach AI

A comprehensive AI-powered debate training platform that helps users improve their argumentation skills through real-time analysis, feedback, and interactive coaching.
NOTE - USE YYOUR OWN API KEY IN .ENV FILE AND .ENV EXAMPLE FILE

## Features

- **🎯 Debate Setup**: Choose your topic and position to start a structured debate
- **🤖 AI Debate Partner**: AI takes the opposing position and engages in real debate
- **📊 Real-time Analysis**: Get detailed feedback on every message you send including:
  - Score out of 10
  - Strengths identification
  - Areas for improvement
  - Potential counterarguments
  - Suggested evidence
  - Overall feedback
  - Perfect answer suggestions
- **💬 Contextual Coaching**: AI understands the full debate context and your position
- **🔄 Refresh & Reset**: Start new debates anytime with the refresh button
- **🔐 User Authentication**: Secure login and registration system
- **📈 Progress Tracking**: Monitor your debate skills improvement over time
- **📱 Responsive Design**: Modern, mobile-friendly interface with smooth transitions

## How It Works

### 1. **Setup Phase**

- Enter your debate topic (e.g., "Should AI replace human teachers?")
- Select your position (For/Pro or Against/Con)
- Click "Start Debate" to begin

### 2. **Debate Phase**

- AI announces the topic and positions: _"Let's initiate this debate on [topic]. Your stance is [for/against], and mine is [opposite]. Please present your opening argument."_
- Send button is only enabled after topic setup
- Layout switches to single-column for focused debate experience

### 3. **Real-time Feedback**

After each message, you receive:

- **Detailed Analysis**: Comprehensive breakdown of your argument
- **Performance Score**: 1-10 rating based on debate criteria
- **Strategic Guidance**: What to improve and what you did well
- **AI Counter-Response**: Thoughtful opposing argument

### 4. **Reset & Continue**

- Use the 🔄 refresh icon to start a new debate
- All messages and feedback are cleared
- Topic setup reappears for new debate session

## Quick Start

### Option 1: Local Development

1. **Clone and Navigate**

   ```bash
   cd "d:\download\Ai Debate Coach"
   ```

2. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set Environment Variables**

   ```bash
   copy .env.example .env
   ```

   Edit `.env` and add your API keys:

   ```
   SECRET_KEY=your-secret-key-here
   OPENAI_API_KEY=your-openai-api-key  # Optional for demo
   ```

4. **Run the Application**

   ```bash
   python debate_coach.py
   ```

5. **Open in Browser**
   Visit: http://localhost:5000

### Option 2: Docker

1. **Build and Run**

   ```bash
   docker-compose up --build
   ```

2. **Access Application**
   Visit: http://localhost:5000

## Usage

### Argument Analysis

1. Enter a debate topic (e.g., "Should social media be regulated?")
2. Select your position (For/Against)
3. Write your argument with supporting points
4. Click "Analyze My Argument" to get AI feedback

### AI Chat Coach

- Ask questions about debate techniques
- Get help with argument structure
- Learn about evidence evaluation
- Practice counterargument strategies

### Sample Interactions

- "How do I structure an argument?"
- "What makes good evidence?"
- "Help me with counterarguments"
- "Tips for debate presentation"

## API Endpoints

### Authentication

- `POST /api/register` - User registration
- `POST /api/login` - User login

### Debate Analysis

- `POST /api/debate/analyze` - Analyze argument and get feedback
- `GET /api/debates/history` - Get user's debate history

### Practice Tools

- `POST /api/practice/question` - Generate practice questions

### Health Check

- `GET /api/health` - Application health status

## Project Structure

```
Ai Debate Coach/
├── templates/
│   └── index.html          # Frontend interface
├── debate_coach.py         # Main Flask application
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker container config
├── docker-compose.yml     # Docker compose setup
├── Procfile              # Heroku deployment
├── app.yaml              # Google App Engine config
├── .env.example          # Environment variables template
└── README.md             # This file
```

## Deployment Options

### Heroku

1. Create Heroku app
2. Set environment variables in Heroku dashboard
3. Deploy using Git or GitHub integration

### Google App Engine

1. Install Google Cloud SDK
2. Update `app.yaml` with your credentials
3. Deploy: `gcloud app deploy`

### Docker

1. Build: `docker build -t debate-coach .`
2. Run: `docker run -p 5000:5000 debate-coach`

## Technology Stack

- **Backend**: Flask, Flask-SocketIO, SQLite
- **Frontend**: HTML5, CSS3, JavaScript, Socket.IO
- **Authentication**: JWT tokens
- **AI Integration**: OpenAI API (configurable)
- **Database**: SQLite (easily replaceable)
- **Deployment**: Docker, Heroku, Google Cloud

## Development

### Adding New Features

1. Backend routes go in `debate_coach.py`
2. Frontend updates go in `templates/index.html`
3. Database schema changes in the `init_db()` function

### Customizing AI Responses

Edit the `DebateAI` class in `debate_coach.py`:

- `get_debate_feedback()` for argument analysis
- `generate_practice_question()` for practice questions
- `handle_chat_message()` for chat responses

## Demo Mode

The application includes a demo mode that works without API keys:

- Mock authentication accepts any credentials
- AI responses use predefined templates
- All features are functional for testing

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For issues or questions:

1. Check the troubleshooting section below
2. Open an issue on GitHub
3. Contact the development team

## Troubleshooting

### Common Issues

**Application won't start:**

- Check Python version (3.9+ recommended)
- Install dependencies: `pip install -r requirements.txt`
- Verify port 5000 is available

**Frontend not loading:**

- Ensure Flask app is running on localhost:5000
- Check browser console for JavaScript errors
- Verify templates folder exists

**Authentication errors:**

- Check SECRET_KEY in environment variables
- For demo mode, any credentials work
- Token issues: clear localStorage and reload

**Socket.IO connection issues:**

- Ensure eventlet is installed
- Check firewall settings
- Try refreshing the page

### Performance Optimization

For production use:

1. Use a production database (PostgreSQL/MySQL)
2. Configure Redis for Socket.IO scaling
3. Use a proper web server (nginx + gunicorn)
4. Enable SSL/HTTPS
5. Add rate limiting for API endpoints

## Roadmap

- [ ] Advanced AI training features
- [ ] Video practice sessions
- [ ] Tournament mode
- [ ] Mobile app
- [ ] Multi-language support
- [ ] Advanced analytics dashboard

