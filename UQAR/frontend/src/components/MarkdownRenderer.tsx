import React from 'react';

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content, className = '' }) => {
  const parseMarkdown = (text: string): JSX.Element[] => {
    const elements: JSX.Element[] = [];
    const lines = text.split('\n');
    let inCodeBlock = false;
    let codeLanguage = '';
    let codeContent = '';
    let key = 0;

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];

      // Gestion des blocs de code
      if (line.startsWith('```')) {
        if (inCodeBlock) {
          // Fin du bloc de code
          elements.push(
            <div key={key++} className="my-3">
              <div className="bg-gray-800 text-gray-100 p-4 rounded-lg overflow-x-auto">
                {codeLanguage && (
                  <div className="text-xs text-gray-400 mb-2 uppercase">
                    {codeLanguage}
                  </div>
                )}
                <pre className="text-sm font-mono whitespace-pre-wrap">
                  <code>{codeContent}</code>
                </pre>
              </div>
            </div>
          );
          inCodeBlock = false;
          codeContent = '';
          codeLanguage = '';
        } else {
          // Début du bloc de code
          inCodeBlock = true;
          codeLanguage = line.slice(3).trim();
        }
        continue;
      }

      if (inCodeBlock) {
        codeContent += (codeContent ? '\n' : '') + line;
        continue;
      }

      // Gestion des titres
      if (line.startsWith('### ')) {
        elements.push(
          <h3 key={key++} className="text-lg font-semibold text-gray-900 mt-4 mb-2">
            {parseInlineMarkdown(line.slice(4))}
          </h3>
        );
        continue;
      }

      if (line.startsWith('## ')) {
        elements.push(
          <h2 key={key++} className="text-xl font-semibold text-gray-900 mt-4 mb-2">
            {parseInlineMarkdown(line.slice(3))}
          </h2>
        );
        continue;
      }

      if (line.startsWith('# ')) {
        elements.push(
          <h1 key={key++} className="text-2xl font-bold text-gray-900 mt-4 mb-2">
            {parseInlineMarkdown(line.slice(2))}
          </h1>
        );
        continue;
      }

      // Gestion des listes
      if (line.startsWith('- ') || line.startsWith('* ')) {
        const listItems = [line];
        let j = i + 1;
        while (j < lines.length && (lines[j].startsWith('- ') || lines[j].startsWith('* '))) {
          listItems.push(lines[j]);
          j++;
        }
        
        elements.push(
          <ul key={key++} className="list-disc list-inside my-2 ml-4">
            {listItems.map((item, idx) => (
              <li key={idx} className="mb-1">
                {parseInlineMarkdown(item.slice(2))}
              </li>
            ))}
          </ul>
        );
        
        i = j - 1;
        continue;
      }

      // Gestion des listes numérotées
      if (/^\d+\.\s/.test(line)) {
        const listItems = [line];
        let j = i + 1;
        while (j < lines.length && /^\d+\.\s/.test(lines[j])) {
          listItems.push(lines[j]);
          j++;
        }
        
        elements.push(
          <ol key={key++} className="list-decimal list-inside my-2 ml-4">
            {listItems.map((item, idx) => (
              <li key={idx} className="mb-1">
                {parseInlineMarkdown(item.replace(/^\d+\.\s/, ''))}
              </li>
            ))}
          </ol>
        );
        
        i = j - 1;
        continue;
      }

      // Lignes vides
      if (line.trim() === '') {
        elements.push(<div key={key++} className="h-2"></div>);
        continue;
      }

      // Paragraphes normaux
      elements.push(
        <p key={key++} className="mb-2 leading-relaxed">
          {parseInlineMarkdown(line)}
        </p>
      );
    }

    return elements;
  };

  const parseInlineMarkdown = (text: string): React.ReactNode => {
    const parts: React.ReactNode[] = [];
    let currentText = text;
    let key = 0;

    // Gestion du code inline
    currentText = currentText.replace(/`([^`]+)`/g, (match, code) => {
      const placeholder = `__CODE_${key}__`;
      parts.push(
        <code key={`code-${key++}`} className="bg-gray-100 text-gray-800 px-1 py-0.5 rounded text-sm font-mono">
          {code}
        </code>
      );
      return placeholder;
    });

    // Gestion du gras
    currentText = currentText.replace(/\*\*([^*]+)\*\*/g, (match, bold) => {
      const placeholder = `__BOLD_${key}__`;
      parts.push(
        <strong key={`bold-${key++}`} className="font-semibold">
          {bold}
        </strong>
      );
      return placeholder;
    });

    // Gestion de l'italique
    currentText = currentText.replace(/\*([^*]+)\*/g, (match, italic) => {
      const placeholder = `__ITALIC_${key}__`;
      parts.push(
        <em key={`italic-${key++}`} className="italic">
          {italic}
        </em>
      );
      return placeholder;
    });

    // Reconstituer le texte avec les éléments formatés
    const finalParts: React.ReactNode[] = [];
    const textParts = currentText.split(/(__(?:CODE|BOLD|ITALIC)_\d+__)/);
    
    textParts.forEach((part, index) => {
      if (part.startsWith('__CODE_')) {
        const codeIndex = parseInt(part.match(/__CODE_(\d+)__/)?.[1] || '0');
        finalParts.push(parts.find((p: any) => p.key === `code-${codeIndex}`));
      } else if (part.startsWith('__BOLD_')) {
        const boldIndex = parseInt(part.match(/__BOLD_(\d+)__/)?.[1] || '0');
        finalParts.push(parts.find((p: any) => p.key === `bold-${boldIndex}`));
      } else if (part.startsWith('__ITALIC_')) {
        const italicIndex = parseInt(part.match(/__ITALIC_(\d+)__/)?.[1] || '0');
        finalParts.push(parts.find((p: any) => p.key === `italic-${italicIndex}`));
      } else if (part) {
        finalParts.push(part);
      }
    });

    return finalParts;
  };

  return (
    <div className={`prose prose-sm max-w-none ${className}`}>
      {parseMarkdown(content)}
    </div>
  );
};

export default MarkdownRenderer; 