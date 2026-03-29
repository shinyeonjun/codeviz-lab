import { useEffect } from 'react';

interface UseLineHighlightParams {
  monaco: any;
  editorRef: React.MutableRefObject<any>;
  decorationsRef: React.MutableRefObject<string[]>;
  lineNumber: number | null;
}

export function useLineHighlight({
  monaco,
  editorRef,
  decorationsRef,
  lineNumber,
}: UseLineHighlightParams) {
  useEffect(() => {
    if (!editorRef.current || !monaco) {
      return;
    }

    if (lineNumber && lineNumber > 0) {
      decorationsRef.current = editorRef.current.deltaDecorations(decorationsRef.current, [
        {
          range: new monaco.Range(lineNumber, 1, lineNumber, 1),
          options: {
            isWholeLine: true,
            className: 'bg-yellow-100/60',
            glyphMarginClassName: 'bg-accent w-full h-full block rounded-r',
          },
        },
      ]);
      editorRef.current.revealLineInCenter(lineNumber);
      return;
    }

    decorationsRef.current = editorRef.current.deltaDecorations(decorationsRef.current, []);
  }, [decorationsRef, editorRef, lineNumber, monaco]);
}
