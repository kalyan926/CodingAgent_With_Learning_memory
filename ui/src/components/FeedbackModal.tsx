import React, { useState } from 'react';

interface FeedbackModalProps {
  onSubmit: (feedback: string, accepted: boolean) => void;
  onClose: () => void;
}

const FeedbackModal: React.FC<FeedbackModalProps> = ({ onSubmit, onClose }) => {
  const [feedback, setFeedback] = useState('');

  const handleAccept = () => {
    onSubmit(feedback, true);
    onClose();
  };

  const handleReject = () => {
    onSubmit('', false);
    onClose();
  };

  return (
    <div className="feedback-modal-overlay">
      <div className="feedback-modal">
        <div className="feedback-modal-header">
          <h3>🤖 Agent Requests Feedback</h3>
          <button className="close-button" onClick={handleReject}>×</button>
        </div>
        
        <div className="feedback-modal-body">
          <p className="feedback-prompt">
            The agent is requesting your feedback to proceed. 
            Please provide guidance or click reject to let the agent continue independently.
          </p>
          
          <textarea
            className="feedback-textarea"
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder="Enter your feedback here..."
            rows={6}
            autoFocus
          />
        </div>
        
        <div className="feedback-modal-footer">
          <button 
            className="feedback-button feedback-reject"
            onClick={handleReject}
          >
            Reject
          </button>
          <button 
            className="feedback-button feedback-accept"
            onClick={handleAccept}
          >
            Send Feedback
          </button>
        </div>
      </div>
    </div>
  );
};

export default FeedbackModal;
