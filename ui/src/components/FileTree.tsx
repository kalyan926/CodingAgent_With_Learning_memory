import React, { useEffect, useState } from 'react';

interface FileNode {
  name: string;
  path: string;
  type: 'file' | 'directory';
  children?: FileNode[];
}

interface FileTreeProps {
  onFileSelect: (path: string, folder: string) => void;
  selectedFile: string | null;
  onRefresh?: () => void;
  onFolderChange?: (folder: string) => void;
}

const FileTree: React.FC<FileTreeProps> = ({ onFileSelect, selectedFile, onRefresh, onFolderChange }) => {
  const [tree, setTree] = useState<FileNode[]>([]);
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set());
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [selectedFolder, setSelectedFolder] = useState<string>('workspace');

  useEffect(() => {
    fetchFileTree();
  }, [selectedFolder]);

  const fetchFileTree = async () => {
    setIsRefreshing(true);
    try {
      const response = await fetch(`/api/files/tree?folder=${selectedFolder}`);
      const data = await response.json();
      setTree(data.tree || []);
    } catch (error) {
      console.error('Failed to fetch file tree:', error);
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleRefresh = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    fetchFileTree();
    if (onRefresh) {
      onRefresh();
    }
  };

  const handleFolderChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newFolder = e.target.value;
    setSelectedFolder(newFolder);
    setExpandedFolders(new Set()); // Reset expanded folders when switching
    if (onFolderChange) {
      onFolderChange(newFolder);
    }
  };

  const toggleFolder = (path: string) => {
    setExpandedFolders(prev => {
      const newSet = new Set(prev);
      if (newSet.has(path)) {
        newSet.delete(path);
      } else {
        newSet.add(path);
      }
      return newSet;
    });
  };

  const renderNode = (node: FileNode, level: number = 0) => {
    if (node.type === 'directory') {
      const isExpanded = expandedFolders.has(node.path);
      return (
        <React.Fragment key={node.path}>
          <div 
            className="folder-item" 
            onClick={() => toggleFolder(node.path)}
            style={{ paddingLeft: `${level * 16}px` }}
          >
            <svg className="chevron-icon" width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              {isExpanded ? (
                <path d="M4.5 5.5l3.5 3.5 3.5-3.5"/>
              ) : (
                <path d="M6 4l4 4-4 4"/>
              )}
            </svg>
            <svg className="folder-icon" width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <path d="M1 3.5A1.5 1.5 0 0 1 2.5 2h3.879a1.5 1.5 0 0 1 1.06.44l1.122 1.12A.5.5 0 0 0 9.207 4H13.5A1.5 1.5 0 0 1 15 5.5v7a1.5 1.5 0 0 1-1.5 1.5h-11A1.5 1.5 0 0 1 1 12.5v-9z"/>
            </svg>
            <span className="node-name">{node.name}</span>
          </div>
          {isExpanded && node.children && (
            <>
              {node.children.map(child => renderNode(child, level + 1))}
            </>
          )}
        </React.Fragment>
      );
    } else {
      return (
        <div
          key={node.path}
          className={`file-item ${selectedFile === node.path ? 'active' : ''}`}
          onClick={() => onFileSelect(node.path, selectedFolder)}
          style={{ paddingLeft: `${level * 16 + 16}px` }}
        >
          <svg className="file-icon" width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
            <path d="M4 0a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V4.707A1 1 0 0 0 13.707 4L10 .293A1 1 0 0 0 9.293 0H4z"/>
          </svg>
          <span className="node-name">{node.name}</span>
        </div>
      );
    }
  };

  return (
    <div className="file-tree">
      <div className="file-tree-header">
        <select 
          className="folder-selector"
          value={selectedFolder}
          onChange={handleFolderChange}
        >
          <option value="workspace">Workspace</option>
          <option value="memory">Memory</option>
        </select>
        <button 
          onClick={handleRefresh}
          className={`refresh-button ${isRefreshing ? 'refreshing' : ''}`}
          title="Refresh file tree"
          disabled={isRefreshing}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/>
          </svg>
        </button>
      </div>
      {tree.map(node => renderNode(node))}
    </div>
  );
};

export default FileTree;
