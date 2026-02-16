import { useState, useRef, useEffect } from 'react';
import FileTree from './components/FileTree';
import EditorComponent from './components/Editor';
import Chat from './components/Chat';
import FeedbackModal from './components/FeedbackModal';

function App() {
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [currentFolder, setCurrentFolder] = useState<string>('workspace');
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [fileTreeWidth, setFileTreeWidth] = useState(10); // percentage
  const [chatWidth, setChatWidth] = useState(25); // percentage
  const [isResizingLeft, setIsResizingLeft] = useState(false);
  const [isResizingRight, setIsResizingRight] = useState(false);
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);

  const handleFileSelect = (path: string, folder: string) => {
    setSelectedFile(path);
    setCurrentFolder(folder);
  };

  const handleFolderChange = (folder: string) => {
    setCurrentFolder(folder);
    setSelectedFile(null); // Clear selection when switching folders
  };

  const handleRefresh = () => {
    setRefreshTrigger(prev => prev + 1);
  };

  // Handle resize for left divider (file tree)
  const handleMouseDownLeft = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizingLeft(true);
  };

  // Handle resize for right divider (chat)
  const handleMouseDownRight = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizingRight(true);
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (isResizingLeft) {
        const newWidth = (e.clientX / window.innerWidth) * 100;
        if (newWidth >= 5 && newWidth <= 30) {
          setFileTreeWidth(newWidth);
        }
      } else if (isResizingRight) {
        const newWidth = ((window.innerWidth - e.clientX) / window.innerWidth) * 100;
        if (newWidth >= 15 && newWidth <= 50) {
          setChatWidth(newWidth);
        }
      }
    };

    const handleMouseUp = () => {
      setIsResizingLeft(false);
      setIsResizingRight(false);
    };

    if (isResizingLeft || isResizingRight) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isResizingLeft, isResizingRight]);

  // Poll for feedback requests
  useEffect(() => {
    const checkFeedbackRequest = async () => {
      try {
        const response = await fetch('/api/feedback/check');
        const data = await response.json();
        
        if (data.requested && !showFeedbackModal) {
          setShowFeedbackModal(true);
        }
      } catch (error) {
        console.error('Error checking feedback request:', error);
      }
    };

    const interval = setInterval(checkFeedbackRequest, 1000); // Check every second
    return () => clearInterval(interval);
  }, [showFeedbackModal]);

  const handleFeedbackSubmit = async (feedback: string, accepted: boolean) => {
    try {
      await fetch('/api/feedback/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ feedback, accepted }),
      });
      setShowFeedbackModal(false);
    } catch (error) {
      console.error('Error submitting feedback:', error);
    }
  };

  const editorWidth = 100 - fileTreeWidth - chatWidth;

  return (
    <div className="app-container">
      <div style={{ width: `${fileTreeWidth}%`, minWidth: '150px', height: '100%', overflow: 'hidden' }}>
        <FileTree 
          onFileSelect={handleFileSelect} 
          selectedFile={selectedFile}
          onRefresh={handleRefresh}
          onFolderChange={handleFolderChange}
        />
      </div>
      
      <div 
        className="resize-divider"
        onMouseDown={handleMouseDownLeft}
      />
      
      <div style={{ width: `${editorWidth}%`, height: '100%', overflow: 'hidden' }}>
        <EditorComponent 
          selectedFile={selectedFile}
          currentFolder={currentFolder}
          refreshTrigger={refreshTrigger}
        />
      </div>
      
      <div 
        className="resize-divider"
        onMouseDown={handleMouseDownRight}
      />
      
      <div style={{ width: `${chatWidth}%`, minWidth: '300px', height: '100%', overflow: 'hidden' }}>
        <Chat />
      </div>

      {showFeedbackModal && (
        <FeedbackModal
          onSubmit={handleFeedbackSubmit}
          onClose={() => setShowFeedbackModal(false)}
        />
      )}
    </div>
  );
}

export default App;
