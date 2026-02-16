import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';

interface Message {
  type: 'user' | 'assistant' | 'tool_call' | 'tool_response';
  content: string;
  toolName?: string;
  toolArgs?: any;
  expanded?: boolean;
}

const Chat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [expandedMessages, setExpandedMessages] = useState<Set<number>>(new Set());
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleNewSession = async () => {
    if (isStreaming) return;
    
    try {
      // Call backend to reset agent state
      await fetch('/api/chat/reset', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      
      // Clear UI state
      setMessages([]);
      setInput('');
      setExpandedMessages(new Set());
    } catch (error) {
      console.error('Failed to reset session:', error);
      // Still clear UI even if backend fails
      setMessages([]);
      setInput('');
      setExpandedMessages(new Set());
    }
  };

  const handleConsolidate = async () => {
    if (isStreaming) return;
    
    try {
      const response = await fetch('/api/memory/consolidate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      
      const data = await response.json();
      
      if (data.status === 'success') {
        // Add success message to chat
        setMessages(prev => [...prev, {
          type: 'assistant',
          content: '✓ Memory consolidation completed successfully. Short-term memories have been transferred to long-term storage.'
        }]);
      }
    } catch (error) {
      console.error('Failed to consolidate memory:', error);
      setMessages(prev => [...prev, {
        type: 'assistant',
        content: '✗ Failed to consolidate memory. Please try again.'
      }]);
    }
  };

  const toggleExpand = (index: number) => {
    setExpandedMessages(prev => {
      const newSet = new Set(prev);
      if (newSet.has(index)) {
        newSet.delete(index);
      } else {
        newSet.add(index);
      }
      return newSet;
    });
  };

  const handleSend = async () => {
    if (!input.trim() || isStreaming) return;

    const userMessage: Message = {
      type: 'user',
      content: input.trim(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsStreaming(true);

    try {
      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: userMessage.content,
          thread_id: '1',
        }),
      });

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('Failed to get response stream');
      }

      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            
            try {
              const event = JSON.parse(data);
              
              if (event.type === 'assistant_message') {
                setMessages(prev => {
                  if (!event.content) return prev;
                  
                  const lastMsg = prev[prev.length - 1];
                  
                  // Simple rule: If last message is assistant, append. Otherwise, create new.
                  // This naturally separates messages after tools because tool messages
                  // are different types (tool_call/tool_response)
                  if (lastMsg && lastMsg.type === 'assistant') {
                    // Append to existing assistant message - continuation
                    return [
                      ...prev.slice(0, -1),
                      { ...lastMsg, content: lastMsg.content + event.content }
                    ];
                  } else {
                    // Create new assistant message (first message or after non-assistant)
                    return [...prev, { type: 'assistant', content: event.content }];
                  }
                });
              } else if (event.type === 'tool_call') {
                const toolMsg: Message = {
                  type: 'tool_call',
                  content: `Calling: ${event.name}`,
                  toolName: event.name,
                  toolArgs: event.args,
                };
                setMessages(prev => [...prev, toolMsg]);
              } else if (event.type === 'tool_response') {
                const toolRespMsg: Message = {
                  type: 'tool_response',
                  content: event.content || 'Tool executed',
                };
                setMessages(prev => [...prev, toolRespMsg]);
              }
            } catch (e) {
              console.error('Failed to parse event:', e);
            }
          }
        }
      }
    } catch (error) {
      console.error('Stream error:', error);
      setMessages(prev => [
        ...prev,
        { type: 'assistant', content: 'Error: Failed to get response from agent.' }
      ]);
    } finally {
      setIsStreaming(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const renderMessage = (msg: Message, index: number) => {
    const isExpanded = expandedMessages.has(index);
    
    switch (msg.type) {
      case 'user':
        return (
          <div key={index} className="message message-user">
            {msg.content}
          </div>
        );
      
      case 'assistant':
        // Check if content is long enough to need collapsing
        const assistantLines = msg.content.split('\n');
        const assistantPreviewLines = assistantLines.slice(0, 3).join('\n');
        const hasMoreAssistantContent = assistantLines.length > 3 || msg.content.length > 200;
        
        return (
          <div key={index} className="message message-assistant">
            {hasMoreAssistantContent && (
              <div className="assistant-header">
                <span className="assistant-label">🤖 AI Response</span>
                <button 
                  className="expand-button"
                  onClick={() => toggleExpand(index)}
                >
                  <svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                    {isExpanded ? (
                      <polyline points="18 15 12 9 6 15"></polyline>
                    ) : (
                      <polyline points="6 9 12 15 18 9"></polyline>
                    )}
                  </svg>
                </button>
              </div>
            )}
            <div className={`assistant-content ${isExpanded || !hasMoreAssistantContent ? 'expanded' : ''}`}>
              <ReactMarkdown>
                {isExpanded || !hasMoreAssistantContent ? msg.content : assistantPreviewLines + '\n...'}
              </ReactMarkdown>
            </div>
          </div>
        );
      
      case 'tool_call':
        const argsString = msg.toolArgs ? JSON.stringify(msg.toolArgs, null, 2) : '';
        // Limit to 2 lines for preview
        const argsLines = argsString.split('\n');
        const argsPreview = argsLines.slice(0, 2).join('\n');
        const hasMoreArgs = argsLines.length > 2;
        
        return (
          <div key={index} className="message message-tool-call">
            <div className="tool-header">
              <div className="tool-name">🔧 {msg.toolName}</div>
              <button 
                className="expand-button"
                onClick={() => toggleExpand(index)}
              >
                <svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                  {isExpanded ? (
                    <polyline points="18 15 12 9 6 15"></polyline>
                  ) : (
                    <polyline points="6 9 12 15 18 9"></polyline>
                  )}
                </svg>
              </button>
            </div>
            {msg.toolArgs && (
              <div className={`tool-args ${isExpanded ? 'expanded' : ''}`}>
                {isExpanded ? argsString : argsPreview}
                {!isExpanded && hasMoreArgs && '\n...'}
              </div>
            )}
          </div>
        );
      
      case 'tool_response':
        // Limit to 2 lines for preview
        const contentLines = msg.content.split('\n');
        const contentPreview = contentLines.slice(0, 2).join('\n');
        const hasMoreContent = contentLines.length > 2;
        
        return (
          <div key={index} className="message message-tool-response">
            <div className="tool-header">
              <span className="tool-status">✓ Tool Response</span>
              <button 
                className="expand-button"
                onClick={() => toggleExpand(index)}
              >
                <svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                  {isExpanded ? (
                    <polyline points="18 15 12 9 6 15"></polyline>
                  ) : (
                    <polyline points="6 9 12 15 18 9"></polyline>
                  )}
                </svg>
              </button>
            </div>
            <div className={`tool-content ${isExpanded ? 'expanded' : ''}`}>
              {isExpanded ? msg.content : contentPreview}
              {!isExpanded && hasMoreContent && '\n...'}
            </div>
          </div>
        );
      
      default:
        return null;
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <span>Agent Chat</span>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button 
            onClick={handleConsolidate}
            className="consolidate-button"
            title="Consolidate short-term to long-term memory"
            disabled={isStreaming}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
              <polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline>
              <line x1="12" y1="22.08" x2="12" y2="12"></line>
            </svg>
            Consolidate
          </button>
          <button 
            onClick={handleNewSession}
            className="new-session-button"
            title="Start new session"
            disabled={isStreaming}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="1 4 1 10 7 10"></polyline>
              <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"></path>
            </svg>
            New Session
          </button>
        </div>
      </div>
      
      <div className="chat-messages">
        {messages.map((msg, idx) => renderMessage(msg, idx))}
        {isStreaming && (
          <div className="message message-thinking">
            <span className="loading-indicator"></span>
            Thinking...
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      
      <div className="chat-input-container">
        <textarea
          className="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask the agent anything..."
          rows={1}
          disabled={isStreaming}
        />
        <button
          className="send-button"
          onClick={handleSend}
          disabled={isStreaming || !input.trim()}
        >
          {isStreaming ? 'Sending...' : 'Send'}
        </button>
      </div>
    </div>
  );
};

export default Chat;
