import { PrismLight as SyntaxHighlighter } from 'react-syntax-highlighter'
import solidity from 'react-syntax-highlighter/dist/esm/languages/prism/solidity'
import markdown from 'react-syntax-highlighter/dist/esm/languages/prism/markdown'
import { oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism'

SyntaxHighlighter.registerLanguage('solidity', solidity)
SyntaxHighlighter.registerLanguage('markdown', markdown)

export function CodeView({ code, language, maxHeight = 640 }: { code: string; language: 'solidity' | 'markdown'; maxHeight?: number }) {
  return (
    <div className="overflow-hidden rounded-lg border border-ink-200 bg-[#fafafa]">
      <SyntaxHighlighter
        language={language}
        style={oneLight}
        showLineNumbers
        wrapLongLines={language === 'markdown'}
        customStyle={{ margin: 0, maxHeight, fontSize: 12.5, background: 'transparent', fontFamily: 'JetBrains Mono Variable, monospace' }}
        lineNumberStyle={{ color: '#9aa3b2', minWidth: '2.5em' }}
      >
        {code}
      </SyntaxHighlighter>
    </div>
  )
}
