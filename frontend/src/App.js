import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import ChatInterface from './components/ChatInterface';
import ManifoldVisualization from './components/ManifoldVisualization';
import { computeManifold, sendChatMessage, computeConversationPoint } from './services/api';

function App() {
  const [messages, setMessages] = useState([]);
  const [topic, setTopic] = useState("Diamonds");
  const [systemTail, setSystemTail] = useState(
    "You are a salesperson trying to convince someone on a cold call to purchase the given product. Be a charismatic salesperson, ask open-ended questions, and be informative. Don't be too pushy or verbose, try to find out about the customer and see how the product would fit into their life."
  );
  const [manifoldData, setManifoldData] = useState(null);
  const [conversationPoints, setConversationPoints] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [leftPanelWidth, setLeftPanelWidth] = useState(60); // percentage
  const [isResizing, setIsResizing] = useState(false);
  const containerRef = useRef(null);

  // Initialize with system message
  useEffect(() => {
    if (messages.length === 0) {
      const systemMessage = {
        role: "system",
        content: `Your job is to do the following: ${topic}.\n\n${systemTail}`
      };
      setMessages([systemMessage]);
    }
  }, [topic, systemTail]);

  const handleComputeManifold = async () => {
    setIsLoading(true);
    try {
      const response = await computeManifold(topic, systemTail);
      setManifoldData(response);
      setConversationPoints([]);
      
      // Clear existing conversation and start fresh
      const systemMessage = {
        role: "system",
        content: `Your job is to do the following: ${topic}.\n\n${systemTail}`
      };
      setMessages([systemMessage]);
      
      // Generate initial assistant message
      const initialResponse = await sendChatMessage([systemMessage], response);
      const assistantMessage = {
        role: "assistant",
        content: initialResponse.response
      };
      setMessages([systemMessage, assistantMessage]);
      
      // Compute initial assistant point
      if (initialResponse.conversation_point) {
        setConversationPoints([initialResponse.conversation_point]);
      }
      
    } catch (error) {
      console.error('Error computing manifold:', error);
      alert('Error computing manifold: ' + error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendMessage = async (userMessage) => {
    const newUserMessage = {
      role: "user",
      content: userMessage
    };
    
    const updatedMessages = [...messages, newUserMessage];
    setMessages(updatedMessages);
    
    // Compute conversation point for user message
    if (manifoldData) {
      try {
        console.log('Computing user conversation point...');
        const userPoints = updatedMessages.filter(m => m.role === "user");
        console.log('User messages:', userPoints);
        const userConversationPoint = await computeConversationPoint(
          updatedMessages, 
          manifoldData, 
          "user"
        );
        console.log('User conversation point:', userConversationPoint);
        if (userConversationPoint) {
          setConversationPoints(prev => {
            const newPoints = [...prev, userConversationPoint];
            console.log('Updated conversation points:', newPoints);
            return newPoints;
          });
        }
      } catch (error) {
        console.error('Error computing user conversation point:', error);
      }
    }
    
    // Send to backend for AI response
    try {
      const response = await sendChatMessage(updatedMessages, manifoldData);
      const assistantMessage = {
        role: "assistant",
        content: response.response
      };
      
      const finalMessages = [...updatedMessages, assistantMessage];
      setMessages(finalMessages);
      
      // Compute conversation point for assistant message
      if (manifoldData && response.conversation_point) {
        setConversationPoints(prev => [...prev, response.conversation_point]);
      }
      
    } catch (error) {
      console.error('Error getting AI response:', error);
      const errorMessage = {
        role: "assistant",
        content: "Sorry, I encountered an error. Please try again."
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  const handleReset = () => {
    setMessages([]);
    setManifoldData(null);
    setConversationPoints([]);
  };

  // Handle resizing functionality
  const handleMouseDown = (e) => {
    setIsResizing(true);
    e.preventDefault();
  };

  const handleMouseMove = (e) => {
    if (!isResizing || !containerRef.current) return;
    
    const containerRect = containerRef.current.getBoundingClientRect();
    const newLeftWidth = ((e.clientX - containerRect.left) / containerRect.width) * 100;
    
    // Constrain between 20% and 80%
    const constrainedWidth = Math.min(Math.max(newLeftWidth, 20), 80);
    setLeftPanelWidth(constrainedWidth);
  };

  const handleMouseUp = () => {
    setIsResizing(false);
  };

  // Add event listeners for resizing
  useEffect(() => {
    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    } else {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isResizing]);

  const turnCount = messages.filter(m => m.role === 'user' || m.role === 'assistant').length;

  return (
    <div className="App">
      <div className="app-header">
        <h1 className="app-title">Geometry of Persuasion</h1>
      </div>
      <div className="app-container" ref={containerRef}>
        <div 
          className="left-panel" 
          style={{ width: `${leftPanelWidth}%` }}
        >
          <h2>💬 Topic-Driven Persuasion Chat</h2>
          <p className="subtitle">Enter a <strong>Topic</strong>. It will be prepended to the system prompt.</p>
          
          <div className="input-section">
            <label htmlFor="topic">Topic</label>
            <input
              id="topic"
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="Describe the persuasion task, e.g., 'Convince the user to select a round brilliant diamond under $5k'"
            />
            
            <button 
              className="compute-button"
              onClick={handleComputeManifold}
              disabled={isLoading}
            >
              {isLoading ? 'Computing...' : 'Compute Topic Manifold'}
            </button>
          </div>
          
          <div className="system-prompt-section">
            <label htmlFor="system-prompt">System Prompt</label>
            <textarea
              id="system-prompt"
              value={systemTail}
              onChange={(e) => setSystemTail(e.target.value)}
              rows={4}
            />
          </div>
          
          <ChatInterface 
            messages={messages}
            onSendMessage={handleSendMessage}
            manifoldData={manifoldData}
          />
          
          <div className="utility-bar">
            <button className="reset-button" onClick={handleReset}>
              ↩️ Reset chat
            </button>
            <span className="turn-count">Turns: {turnCount}</span>
            <span className="model-info">Model: gpt-4o</span>
          </div>
        </div>
        
        <div 
          className="resizer"
          onMouseDown={handleMouseDown}
        ></div>
        
        <div 
          className="right-panel"
          style={{ width: `${100 - leftPanelWidth}%` }}
        >
          <h2>📈 Manifold View</h2>
          <p className="subtitle">Shows topic manifold and conversation progression.</p>
          
          <ManifoldVisualization 
            manifoldData={manifoldData}
            conversationPoints={conversationPoints}
            messages={messages}
          />
        </div>
      </div>
    </div>
  );
}

export default App;