import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import ChatInterface from './components/ChatInterface';
import ManifoldVisualization from './components/ManifoldVisualization';
import { computeManifold, sendChatMessage } from './services/api';

function App() {
  const [messages, setMessages] = useState([]);
  const [topic, setTopic] = useState("Dunkin Donuts");
  const [systemTail, setSystemTail] = useState(
    "You are a salesperson named Duncan trying to convince someone on a cold call to purchase the given product. Be a charismatic salesperson, ask open-ended questions, and be informative. Don't be too pushy or verbose, try to find out about the customer and see how the product would fit into their life. Limit your response to 30 words maximum."
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
        content: `Your job is to do convince someone to support the following topic or item: ${topic}.  This is your description:\n\n${systemTail}`
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
      
      // Plot the initial assistant message immediately
      if (initialResponse.conversation_points && initialResponse.conversation_points.length > 0) {
        setConversationPoints(initialResponse.conversation_points);
      } else {
        // If no conversation points returned, create a placeholder point for the initial agent message
        const initialAgentPoint = {
          role: "assistant",
          x: 0.5, // Place at center of manifold
          y: 0.5,
          message_index: 0,
          message: initialResponse.response
        };
        setConversationPoints([initialAgentPoint]);
      }
      
    } catch (error) {
      console.error('Error computing manifold:', error);
      alert('Error computing manifold: ' + error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendMessage = async (userMessage) => {
    console.log('🔍 DEBUG: handleSendMessage called with:', userMessage);
    
    const newUserMessage = {
      role: "user",
      content: userMessage
    };
    
    const updatedMessages = [...messages, newUserMessage];
    setMessages(updatedMessages);
    console.log('🔍 DEBUG: Updated messages:', updatedMessages.map(m => ({ role: m.role, contentLength: m.content.length })));
    
    // Send to backend for AI response and conversation points
    console.log('🔍 DEBUG: Sending chat message to backend...');
    try {
      const response = await sendChatMessage(updatedMessages, manifoldData);
      console.log('🔍 DEBUG: Chat response received:', {
        responseLength: response.response?.length,
        conversationPointsCount: response.conversation_points?.length || 0,
        conversationPoints: response.conversation_points
      });
      
      const assistantMessage = {
        role: "assistant",
        content: response.response
      };
      
      const finalMessages = [...updatedMessages, assistantMessage];
      setMessages(finalMessages);
      console.log('🔍 DEBUG: Final messages after assistant response:', finalMessages.map(m => ({ role: m.role, contentLength: m.content.length })));
      
      // Plot all conversation points immediately as they're generated
      if (response.conversation_points && response.conversation_points.length > 0) {
        console.log('🔍 DEBUG: Adding conversation points to state:', response.conversation_points);
        setConversationPoints(prev => {
          const newPoints = [...prev, ...response.conversation_points];
          console.log('🔍 DEBUG: New conversation points after backend response:', newPoints);
          return newPoints;
        });
      } else {
        console.log('🔍 DEBUG: No conversation points returned from backend');
      }
      
    } catch (error) {
      console.error('❌ ERROR: Error getting AI response:', error);
      console.error('❌ ERROR: Error details:', error.message);
      console.error('❌ ERROR: Error response:', error.response?.data);
      
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
        <h1 className="app-title">Geometry of Influence</h1>
      </div>
      <div className="app-container" ref={containerRef}>
        <div 
          className="left-panel" 
          style={{ width: `${leftPanelWidth}%` }}
        >
          <h2>💬 Topic-Driven Influence Chat</h2>
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