import Editor from '@monaco-editor/react';

import type { ExecutionLanguage } from '../../../types/execution';

interface CodeEditorPanelProps {
  fileName: string;
  language: ExecutionLanguage;
  code: string;
  onChange: (value: string) => void;
  editorRef: React.MutableRefObject<any>;
}

export function CodeEditorPanel({
  fileName,
  language,
  code,
  onChange,
  editorRef,
}: CodeEditorPanelProps) {
  return (
    <div className="overflow-hidden rounded-xl border border-surface-border">
      <div className="flex items-center gap-2 border-b border-surface-border bg-surface-soft px-4 py-2">
        <span className="text-xs text-ink-muted">{fileName}</span>
      </div>
      <div className="h-[500px]">
        <Editor
          height="100%"
          language={language}
          defaultLanguage={language}
          value={code}
          onChange={(value) => onChange(value || '')}
          theme="vs-dark"
          onMount={(editor) => {
            editorRef.current = editor;
          }}
          options={{
            minimap: { enabled: false },
            fontSize: 14,
            lineHeight: 24,
            padding: { top: 12 },
            scrollBeyondLastLine: false,
            smoothScrolling: true,
            glyphMargin: true,
            fontFamily: '"JetBrains Mono", monospace',
            renderLineHighlight: 'gutter',
          }}
        />
      </div>
    </div>
  );
}
