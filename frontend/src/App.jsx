import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const API_BASE_URL = '/api';

function App() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hello! I\'m your Mathematical Question Assistant. I can help you with:\n\n• Valid mathematical questions - I\'ll accept and process them\n• Mathematical questions with errors - I\'ll automatically refine them\n• Non-mathematical questions - I\'ll reject them with helpful examples\n\nJust type your math question, and I\'ll handle the rest!',
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const addMessage = (role, content, data = null) => {
    setMessages(prev => [...prev, {
      role,
      content,
      data,
      timestamp: new Date()
    }]);
  };

  const handleChat = async (userMessage) => {
    try {
      setLoading(true);
      
      const chatHistory = messages.map(msg => ({
        role: msg.role,
        content: msg.content
      }));

      const response = await axios.post(`${API_BASE_URL}/process`, {
        question: userMessage,
        chat_history: chatHistory
      });

      const data = response.data;
      let fullResponse = '';
      
      if (data.status === 'guardrail') {
        fullResponse = data.message;
        
      } else if (data.status === 'invalid') {
        fullResponse = `**Invalid Question - Not Mathematical**\n\n`;
        fullResponse += `**Your input:** ${data.original_question}\n\n`;
        fullResponse += `**Error:** ${data.reason}\n\n`;
        fullResponse += `**This question is not mathematical and cannot be refined.**\n\n`;
        fullResponse += `Please enter a valid mathematical question (related to algebra, calculus, geometry, statistics, etc.)\n\n`;
        
        if (data.examples && data.examples.length > 0) {
          fullResponse += `**Examples of valid questions:**\n`;
          data.examples.forEach(ex => {
            fullResponse += `• ${ex}\n`;
          });
        }
        
      } else if (data.status === 'valid') {
        fullResponse = `**Valid Mathematical Question**\n\n`;
        fullResponse += `**Your question:** ${data.original_question}\n\n`;
        fullResponse += `**Status:** This is a valid mathematical question!\n`;
        
        if (data.changes && data.changes.length > 0) {
          fullResponse += `\n**Minor improvements made:**\n`;
          data.changes.forEach((change, idx) => {
            fullResponse += `${idx + 1}. ${change}\n`;
          });
          fullResponse += `\n**Refined version:** ${data.refined_question}\n`;
        }
        
        if (data.similar_questions && data.similar_questions.length > 0) {
          fullResponse += `\n**Similar Questions Found:**\n\n`;
          data.similar_questions.forEach((result, idx) => {
            fullResponse += `${idx + 1}. "${result.question}" (${result.similarity}% similar)\n`;
            fullResponse += `   Domain: ${result.domain} - ${result.subdomain}\n\n`;
          });
        } else {
          fullResponse += `\nNo similar questions found! Your question is unique.\n`;
        }
        
      } else if (data.status === 'refineable') {
        fullResponse = `**Mathematical Question - Refinement Needed**\n\n`;
        fullResponse += `**Your input:** ${data.original_question}\n\n`;
        fullResponse += `**Issue:** ${data.reason}\n\n`;
        fullResponse += `**Refined version:** ${data.refined_question}\n\n`;
        fullResponse += `**Changes made:**\n`;
        data.changes.forEach((change, idx) => {
          fullResponse += `${idx + 1}. ${change}\n`;
        });
        
        if (data.similar_questions && data.similar_questions.length > 0) {
          fullResponse += `\n**Similar Questions Found:**\n\n`;
          data.similar_questions.forEach((result, idx) => {
            fullResponse += `${idx + 1}. "${result.question}" (${result.similarity}% similar)\n`;
            fullResponse += `   Domain: ${result.domain} - ${result.subdomain}\n\n`;
          });
        } else {
          fullResponse += `\nNo similar questions found! Your question is unique.\n`;
        }
      }

      addMessage('assistant', fullResponse, data);
      
    } catch (error) {
      addMessage('assistant', `Error: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    addMessage('user', userMessage);
    setInput('');

    await handleChat(userMessage);
  };

  const formatTime = (date) => {
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <div className="app">
      <div className="chat-container">
        <div className="chat-header">
          <div className="chat-header-content">
            <span className="chat-icon">Math</span>
            <div>
              <h1>Math Question Assistant</h1>
              <p>AI-powered validation, refinement & similarity checking</p>
            </div>
          </div>
        </div>

        <div className="messages-container">
          {messages.map((message, index) => (
            <div 
              key={index} 
              className={`message-wrapper ${message.role}`}
            >
              <div className="message">
                <div className="message-avatar">
                  {message.role === 'user' ? 'U' : 'AI'}
                </div>
                <div className="message-content">
                  <div className="message-text">
                    {message.content.split('\n').map((line, i) => (
                      <React.Fragment key={i}>
                        {line}
                        {i < message.content.split('\n').length - 1 && <br />}
                      </React.Fragment>
                    ))}
                  </div>
                  <div className="message-time">
                    {formatTime(message.timestamp)}
                  </div>
                </div>
              </div>
            </div>
          ))}
          
          {loading && (
            <div className="message-wrapper assistant">
              <div className="message">
                <div className="message-avatar">AI</div>
                <div className="message-content">
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        <form className="input-container" onSubmit={handleSubmit}>
          <div className="input-wrapper">
            <div className="message-input-container">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmit(e);
                  }
                }}
                placeholder="Message Math Assistant..."
                disabled={loading}
                className="message-input"
                rows={1}
                style={{
                  height: 'auto',
                  minHeight: '24px',
                  maxHeight: '200px',
                  overflow: input.split('\n').length > 5 ? 'auto' : 'hidden'
                }}
                onInput={(e) => {
                  e.target.style.height = 'auto';
                  e.target.style.height = e.target.scrollHeight + 'px';
                }}
              />
              <button 
                type="submit" 
                disabled={loading || !input.trim()}
                className="send-button"
              >
                {loading ? '...' : 'Send'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}

export default App;