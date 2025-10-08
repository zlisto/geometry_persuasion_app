# Geometry of Persuasion

A React + FastAPI application that visualizes conversation dynamics in a geometric "persuasion space" using AI embeddings and manifold projection.

## Overview

This application allows you to:
- Define a persuasion topic and system prompt
- Generate a 2D manifold representing the "persuasion space" for that topic
- Conduct AI-powered conversations and visualize how messages map to this space
- Track conversation progression as points in the geometric space

The manifold is created by generating extreme sentiment statements (1/100 and 100/100) for your topic, then projecting conversation messages into the 2D space spanned by these vectors.

## Architecture

```
project-root/
├── backend/                 # FastAPI Python backend
│   ├── main.py             # FastAPI app with chat/manifold endpoints
│   ├── geometry_persuasion.py  # Core geometry and AI functions
│   ├── requirements.txt    # Python dependencies
│   └── .env               # Environment variables (OPENAI_API_KEY)
├── frontend/               # React frontend
│   ├── src/
│   │   ├── App.js         # Main React component
│   │   ├── App.css        # Styling (black/pink theme)
│   │   ├── components/
│   │   │   ├── ChatInterface.js      # Chat UI component
│   │   │   └── ManifoldVisualization.js  # Plotly.js visualization
│   │   └── services/
│   │       └── api.js     # API client for backend communication
│   ├── package.json       # Node.js dependencies
│   └── build/             # Production build (created by npm run build)
├── render.yaml            # Render.com deployment configuration
└── README.md              # This file
```

## Features

### Backend (FastAPI)
- **POST /compute-manifold**: Generate 2D manifold vectors for a topic
- **POST /chat**: Send messages and get AI responses with conversation points
- **POST /compute-conversation-point**: Compute geometric coordinates for message sequences
- CORS enabled for React frontend
- OpenAI GPT-4o integration for text generation and embeddings

### Frontend (React)
- **Chat Interface**: Real-time conversation with AI assistant
- **Manifold Visualization**: Interactive Plotly.js charts showing:
  - Topic manifold (red=1/100 sentiment, blue=100/100 sentiment)
  - User message progression (orange circles)
  - Assistant message progression (green squares)
- **Topic Management**: Define persuasion objectives and system prompts
- **Responsive Design**: Black background with hot pink accents

## Setup

### Prerequisites
- Python 3.8+
- Node.js 16+
- OpenAI API key

### Local Development

1. **Backend Setup**
   ```bash
   cd backend
   pip install -r requirements.txt
   # Add your OPENAI_API_KEY to .env file
   python main.py
   ```
   Backend runs on http://localhost:8000

2. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm start
   ```
   Frontend runs on http://localhost:3000

3. **Environment Variables**
   Create `backend/.env`:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

### Production Deployment (Render.com)

1. **Connect Repository**
   - Connect your GitHub repository to Render.com
   - The `render.yaml` file will automatically configure both services

2. **Environment Variables**
   - Set `OPENAI_API_KEY` in the backend service environment variables
   - The frontend will automatically connect to the deployed backend

3. **Deploy**
   - Render will build and deploy both services automatically
   - Backend: `https://geometry-persuasion-backend.onrender.com`
   - Frontend: `https://geometry-persuasion-frontend.onrender.com`

## Usage

1. **Set Topic**: Enter a persuasion objective (e.g., "Convince user to buy diamonds under $5k")
2. **Customize System Prompt**: Modify the AI assistant's behavior
3. **Compute Manifold**: Generate the 2D persuasion space for your topic
4. **Start Chatting**: Have conversations and watch them map to the geometric space
5. **Analyze Patterns**: Observe how different conversation strategies move through the space

## API Endpoints

### Backend API

- `GET /` - Health check
- `POST /compute-manifold` - Generate manifold vectors
  ```json
  {
    "topic": "string",
    "system_tail": "string"
  }
  ```
- `POST /chat` - Send chat message
  ```json
  {
    "messages": [{"role": "string", "content": "string"}],
    "manifold_data": {"vector_0": [...], "vector_1": [...]}
  }
  ```
- `POST /compute-conversation-point` - Compute message coordinates
  ```json
  {
    "messages": [...],
    "manifold_data": {...},
    "role": "user|assistant"
  }
  ```

## Technical Details

### Manifold Generation
1. Generate extreme sentiment statements (1/100 and 100/100) for the topic
2. Create embeddings for these statements using OpenAI's text-embedding-3-large
3. Project conversation messages into the 2D space spanned by these vectors
4. Scale coordinates so v0=(-1,1) and v1=(1,1)

### Conversation Tracking
- User and assistant messages are tracked separately
- Each role's cumulative message history is embedded and projected
- Points are connected with lines to show conversation flow
- Message numbers are displayed in hover tooltips

### Styling
- Dark theme with hot pink (#ff69b4) accents
- Responsive design with flexbox layout
- Custom scrollbars and hover effects
- Plotly.js charts with matching color scheme

## Dependencies

### Backend
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `openai` - AI text generation and embeddings
- `numpy` - Numerical computations
- `plotly` - Plotting (for backend utilities)
- `python-dotenv` - Environment variable management

### Frontend
- `react` - UI framework
- `react-plotly.js` - Interactive charts
- `plotly.js` - Plotting library
- `axios` - HTTP client

## Troubleshooting

### Common Issues

1. **CORS Errors**: Ensure backend CORS settings include your frontend URL
2. **OpenAI API Errors**: Verify API key is set correctly in environment
3. **Build Failures**: Check Node.js and Python versions match requirements
4. **Plot Not Rendering**: Ensure Plotly.js dependencies are installed

### Development Tips

- Use browser dev tools to inspect API calls
- Check backend logs for detailed error messages
- Test manifold computation with simple topics first
- Verify environment variables are loaded correctly

## License

MIT License - feel free to use and modify for your projects.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally
5. Submit a pull request

## Support

For issues and questions:
- Check the troubleshooting section above
- Review the API documentation
- Open an issue on GitHub
