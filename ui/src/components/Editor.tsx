import React, { useEffect, useState } from 'react';
import Editor from '@monaco-editor/react';

interface EditorComponentProps {
  selectedFile: string | null;
  currentFolder: string;
  refreshTrigger?: number;
}

const EditorComponent: React.FC<EditorComponentProps> = ({ selectedFile, currentFolder, refreshTrigger }) => {
  const [content, setContent] = useState<string>('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (selectedFile) {
      loadFileContent(selectedFile, currentFolder);
    }
  }, [selectedFile, refreshTrigger, currentFolder]);

  const loadFileContent = async (path: string, folder: string) => {
    setLoading(true);
    try {
      const response = await fetch('/api/files/content', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path, folder }),
      });
      const data = await response.json();
      setContent(data.content || '');
    } catch (error) {
      console.error('Failed to load file:', error);
      setContent('// Error loading file');
    } finally {
      setLoading(false);
    }
  };

  const handleEditorChange = (value: string | undefined) => {
    if (value !== undefined) {
      setContent(value);
    }
  };

  const handleSave = async () => {
    if (!selectedFile) return;
    
    try {
      await fetch('/api/files/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: selectedFile, content, folder: currentFolder }),
      });
    } catch (error) {
      console.error('Failed to save file:', error);
    }
  };

  // Determine language from file extension
  const getLanguage = (filename: string): string => {
    const ext = filename.split('.').pop()?.toLowerCase();
    const languageMap: { [key: string]: string } = {
      'js': 'javascript',
      'jsx': 'javascript',
      'ts': 'typescript',
      'tsx': 'typescript',
      'py': 'python',
      'json': 'json',
      'html': 'html',
      'css': 'css',
      'md': 'markdown',
      'yml': 'yaml',
      'yaml': 'yaml',
      'toml': 'toml',
      'txt': 'plaintext',
    };
    return languageMap[ext || 'txt'] || 'plaintext';
  };

  return (
    <div className="editor-container">
      <div className="editor-header">
        {selectedFile || 'No file selected'}
        {selectedFile && (
          <button 
            onClick={handleSave}
            style={{
              marginLeft: '16px',
              padding: '4px 12px',
              background: 'var(--color-accent-green)',
              border: 'none',
              borderRadius: '4px',
              color: 'var(--color-bg-primary)',
              cursor: 'pointer',
              fontSize: '12px',
            }}
          >
            Save (Ctrl+S)
          </button>
        )}
      </div>
      <div className="editor-content">
        {!selectedFile ? (
          <div className="editor-placeholder">
            Select a file to edit
          </div>
        ) : loading ? (
          <div className="editor-placeholder">
            Loading...
          </div>
        ) : (
          <Editor
            height="100%"
            language={getLanguage(selectedFile)}
            value={content}
            onChange={handleEditorChange}
            theme="vs-dark"
            options={{
              minimap: { enabled: false },
              fontSize: 13,
              lineNumbers: 'on',
              scrollBeyondLastLine: false,
              automaticLayout: true,
              tabSize: 2,
            }}
            onMount={(editor, monaco) => {
              // Add Ctrl+S save shortcut
              editor.addCommand(
                monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS,
                handleSave
              );
            }}
          />
        )}
      </div>
    </div>
  );
};

export default EditorComponent;
