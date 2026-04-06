import { memo, useState } from 'react';
import { Handle, Position } from '@xyflow/react';

const TAG_COLORS = {
  body: '#6366f1',
  main: '#6366f1',
  section: '#3b82f6',
  article: '#3b82f6',
  div: '#06b6d4',
  h1: '#a855f7',
  h2: '#a855f7',
  h3: '#a855f7',
  h4: '#a855f7',
  h5: '#a855f7',
  h6: '#a855f7',
  p: '#10b981',
  ul: '#f59e0b',
  ol: '#f59e0b',
  li: '#f59e0b',
};

function KBNode({ data }) {
  const [expanded, setExpanded] = useState(false);
  const color = TAG_COLORS[data.tag] || '#6b7280';
  const hasLongText = data.fullText && data.fullText.length > 50;

  return (
    <div
      style={{
        background: '#1e1e2e',
        border: `2px solid ${color}`,
        borderRadius: 8,
        padding: 0,
        minWidth: 160,
        maxWidth: expanded ? 400 : 240,
        fontFamily: 'ui-monospace, Consolas, monospace',
        fontSize: 12,
        color: '#cdd6f4',
        boxShadow: `0 2px 8px ${color}33`,
        cursor: 'default',
        transition: 'max-width 0.2s ease, box-shadow 0.2s ease',
      }}
    >
      <Handle type="target" position={Position.Top} style={{ background: color, width: 8, height: 8 }} />

      {/* Tag Badge */}
      <div
        style={{
          background: color,
          color: '#fff',
          padding: '3px 10px',
          borderRadius: '6px 6px 0 0',
          fontSize: 11,
          fontWeight: 700,
          letterSpacing: 0.5,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <span>{'<'}{data.tag}{'>'}</span>
        {data.elementId && (
          <span style={{ opacity: 0.7, fontSize: 10, marginLeft: 8 }}>
            #{data.elementId.slice(0, 14)}
          </span>
        )}
      </div>

      {/* Content Preview */}
      <div style={{ padding: '6px 10px', lineHeight: 1.4 }}>
        {expanded ? (
          <div style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
            {data.fullText || data.text}
          </div>
        ) : (
          <div style={{
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical',
          }}>
            {data.text || '(empty)'}
          </div>
        )}

        {hasLongText && (
          <button
            onClick={(e) => { e.stopPropagation(); setExpanded(!expanded); }}
            style={{
              background: 'transparent',
              border: `1px solid ${color}55`,
              color: color,
              padding: '2px 8px',
              borderRadius: 4,
              fontSize: 10,
              cursor: 'pointer',
              marginTop: 4,
              width: '100%',
            }}
          >
            {expanded ? '▲ Collapse' : '▼ Expand'}
          </button>
        )}
      </div>

      <Handle type="source" position={Position.Bottom} style={{ background: color, width: 8, height: 8 }} />
    </div>
  );
}

export default memo(KBNode);
