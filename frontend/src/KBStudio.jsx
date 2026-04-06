import { useState, useEffect, useCallback, useMemo } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  useNodesState,
  useEdgesState,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import dagre from 'dagre';
import CodeMirror from '@uiw/react-codemirror';
import { createTheme } from '@uiw/codemirror-themes';
import { html } from '@codemirror/lang-html';
import { tags as t } from '@lezer/highlight';
import { EditorView } from '@codemirror/view';
import KBNode from './KBNode';

// ========== Dagre Auto-Layout ==========
function getLayoutedElements(nodes, edges) {
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: 'TB', nodesep: 40, ranksep: 60 });

  nodes.forEach((node) => {
    g.setNode(node.id, { width: 200, height: 80 });
  });

  edges.forEach((edge) => {
    g.setEdge(edge.source, edge.target);
  });

  dagre.layout(g);

  const layoutedNodes = nodes.map((node) => {
    const pos = g.node(node.id);
    return {
      ...node,
      position: { x: pos.x - 100, y: pos.y - 40 },
    };
  });

  return { nodes: layoutedNodes, edges };
}

// ========== HTML → Graph Converter ==========
const SKIP_TAGS = new Set(['html', 'head', 'script', 'style', 'meta', 'link', 'title']);

function htmlToGraph(htmlString) {
  const parser = new DOMParser();
  const doc = parser.parseFromString(htmlString, 'text/html');
  const nodes = [];
  const edges = [];
  let autoId = 0;

  function getDirectText(el) {
    let text = '';
    for (const child of el.childNodes) {
      if (child.nodeType === Node.TEXT_NODE) {
        text += child.textContent;
      }
    }
    return text.trim();
  }

  function traverse(element, parentId) {
    if (!element.tagName) return;
    const tag = element.tagName.toLowerCase();
    if (SKIP_TAGS.has(tag)) {
      for (const child of element.children) traverse(child, parentId);
      return;
    }

    const id = element.id || `auto-${autoId++}`;
    const directText = getDirectText(element);
    const fullText = element.textContent?.trim() || '';
    const previewText = directText
      ? directText.slice(0, 50) + (directText.length > 50 ? '…' : '')
      : fullText.slice(0, 50) + (fullText.length > 50 ? '…' : '');

    nodes.push({
      id,
      type: 'kbNode',
      data: {
        tag,
        text: previewText,
        fullText: tag === 'body' ? '(document root)' : fullText,
        elementId: element.id || null,
      },
      position: { x: 0, y: 0 },
    });

    if (parentId) {
      edges.push({
        id: `${parentId}->${id}`,
        source: parentId,
        target: id,
        style: { stroke: '#585b70', strokeWidth: 1.5 },
        animated: false,
      });
    }

    for (const child of element.children) {
      traverse(child, id);
    }
  }

  const body = doc.body;
  if (body) {
    traverse(body, null);
  }

  return { nodes, edges };
}

// ========== Editor Theme ==========
const catppuccinTheme = createTheme({
  theme: 'dark',
  settings: {
    background: '#1e1e2e',
    foreground: '#cdd6f4',
    caret: '#cba6f7',
    selection: '#45475a',
    selectionMatch: '#45475a',
    lineHighlight: '#313244',
    gutterBackground: '#181825',
    gutterForeground: '#6c7086',
    gutterBorder: 'transparent',
  },
  styles: [
    { tag: t.keyword, color: '#cba6f7' },
    { tag: t.string, color: '#a6e3a1' },
    { tag: t.comment, color: '#6c7086' },
    { tag: t.tagName, color: '#89b4fa' },
    { tag: t.attributeName, color: '#f9e2af' },
    { tag: t.attributeValue, color: '#a6e3a1' },
    { tag: t.content, color: '#cdd6f4' },
  ],
});

// ========== Main Component ==========
const nodeTypes = { kbNode: KBNode };

export default function KBStudio() {
  const [activeTab, setActiveTab] = useState('editor'); // 'editor' | 'graph'
  const [htmlContent, setHtmlContent] = useState('');
  const [savedContent, setSavedContent] = useState('');
  const [saveStatus, setSaveStatus] = useState('idle');
  const [loadError, setLoadError] = useState(null);
  const [showPreview, setShowPreview] = useState(false);

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  // Load KB on mount
  useEffect(() => {
    const fetchKB = async () => {
      try {
        const res = await fetch('/state');
        const data = await res.json();
        if (data.knowledge_base) {
          setHtmlContent(data.knowledge_base);
          setSavedContent(data.knowledge_base);
        }
      } catch (err) {
        setLoadError('Failed to load KB — backend may be down. Editor is empty.');
      }
    };
    fetchKB();
  }, []);

  // Rebuild graph whenever we switch to graph tab or content changes
  useEffect(() => {
    if (!htmlContent) return;
    const { nodes: rawNodes, edges: rawEdges } = htmlToGraph(htmlContent);
    if (rawNodes.length === 0) return;
    const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(rawNodes, rawEdges);
    setNodes(layoutedNodes);
    setEdges(layoutedEdges);
  }, [htmlContent, activeTab]);

  const handleSave = useCallback(async () => {
    setSaveStatus('saving');
    try {
      const res = await fetch('/kb', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ html: htmlContent }),
      });
      const data = await res.json();
      if (data.status === 'success') {
        // Reload to get finalized IDs
        const stateRes = await fetch('/state');
        const stateData = await stateRes.json();
        if (stateData.knowledge_base) {
          setHtmlContent(stateData.knowledge_base);
          setSavedContent(stateData.knowledge_base);
        }
        setSaveStatus('saved');
        setTimeout(() => setSaveStatus('idle'), 2000);
      } else {
        setSaveStatus('error');
        setTimeout(() => setSaveStatus('idle'), 3000);
      }
    } catch (err) {
      setSaveStatus('error');
      setTimeout(() => setSaveStatus('idle'), 3000);
    }
  }, [htmlContent]);

  const hasChanges = htmlContent !== savedContent;

  const saveButtonLabel = {
    idle: hasChanges ? '● Save to Backend' : 'No Changes',
    saving: 'Saving…',
    saved: '✓ Saved',
    error: '✗ Error',
  }[saveStatus];

  const saveButtonColor = {
    idle: hasChanges ? '#cba6f7' : '#585b70',
    saving: '#f9e2af',
    saved: '#a6e3a1',
    error: '#f38ba8',
  }[saveStatus];



  return (
    <div className="kb-studio">
      {/* Tab Bar */}
      <div className="kb-tab-bar">
        <div className="kb-tabs">
          <button
            className={`kb-tab ${activeTab === 'editor' ? 'active' : ''}`}
            onClick={() => setActiveTab('editor')}
          >
            {'</>'}  HTML Editor
          </button>
          <button
            className={`kb-tab ${activeTab === 'graph' ? 'active' : ''}`}
            onClick={() => setActiveTab('graph')}
          >
            ◉ DOM Graph
          </button>
        </div>
        <div className="kb-actions">
          <button
            className="kb-save-btn"
            onClick={handleSave}
            disabled={saveStatus === 'saving' || !hasChanges}
            style={{
              color: saveButtonColor,
              borderColor: saveButtonColor,
            }}
          >
            {saveButtonLabel}
          </button>
        </div>
      </div>

      {/* Content Area */}
      <div className="kb-content">
        {loadError && <div className="kb-load-error">{loadError}</div>}
        {activeTab === 'editor' && (
          <div className="kb-editor-wrap">
            <div className="kb-editor-toolbar">
              <button
                className={`kb-toggle-btn ${!showPreview ? 'active' : ''}`}
                onClick={() => setShowPreview(false)}
              >Source</button>
              <button
                className={`kb-toggle-btn ${showPreview ? 'active' : ''}`}
                onClick={() => setShowPreview(true)}
              >Preview</button>
            </div>
            {showPreview ? (
              <div
                className="kb-preview"
                dangerouslySetInnerHTML={{ __html: htmlContent }}
              />
            ) : (
              <CodeMirror
                value={htmlContent}
                onChange={(val) => setHtmlContent(val)}
                extensions={[html(), EditorView.lineWrapping]}
                theme={catppuccinTheme}
                height="calc(100vh - 300px)"
                basicSetup={{
                  lineNumbers: true,
                  foldGutter: true,
                  highlightActiveLine: true,
                  highlightSelectionMatches: true,
                  bracketMatching: true,
                  autocompletion: true,
                }}
              />
            )}
          </div>
        )}

        {activeTab === 'graph' && (
          <div className="kb-graph-wrap">
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              nodeTypes={nodeTypes}
              fitView
              fitViewOptions={{ padding: 0.3 }}
              proOptions={{ hideAttribution: true }}
              style={{ background: '#11111b' }}
            >
              <Background color="#313244" gap={20} size={1} />
              <Controls
                style={{
                  background: '#1e1e2e',
                  borderColor: '#313244',
                  color: '#cdd6f4',
                }}
              />
            </ReactFlow>
          </div>
        )}
      </div>
    </div>
  );
}
