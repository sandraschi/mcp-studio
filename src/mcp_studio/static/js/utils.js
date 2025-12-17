// ═══════════════════════════════════════════════════════════════════
// DOCSTRING FORMATTER - Makes tool docstrings human-readable
// ═══════════════════════════════════════════════════════════════════

function formatDocstring(docstring) {
    if (!docstring || docstring.trim() === '') {
        return '<div class="text-gray-500 italic">No description available</div>';
    }

    // Clean up the docstring
    let text = docstring.trim();

    // Split into sections
    const sections = {
        brief: '',
        detailed: '',
        args: '',
        returns: '',
        examples: '',
        usage: '',
        raises: '',
        notes: '',
        seeAlso: ''
    };

    // Extract brief description (first line or paragraph)
    const lines = text.split('\n');
    let currentSection = 'brief';
    let currentContent = [];
    let inCodeBlock = false;

    for (let i = 0; i < lines.length; i++) {
        const originalLine = lines[i];
        const trimmed = originalLine.trim();

        // Skip empty lines at start
        if (i === 0 && trimmed === '') continue;

        // Detect code blocks (preserve original line including leading spaces)
        if (trimmed.startsWith('```')) {
            inCodeBlock = !inCodeBlock;
            currentContent.push(originalLine);
            continue;
        }

        // If in code block, preserve line as-is
        if (inCodeBlock) {
            currentContent.push(originalLine);
            continue;
        }

        const line = trimmed;

        // Detect section headers (case-insensitive)
        const sectionPatterns = {
            'args': /^(Args|Parameters|Arguments):/i,
            'returns': /^(Returns?|Return):/i,
            'examples': /^(Examples?|Example):/i,
            'usage': /^(Usage|When to use):/i,
            'raises': /^(Raises?|Exceptions?):/i,
            'notes': /^(Notes?|Note):/i,
            'seeAlso': /^(See Also|See|Related):/i
        };

        let sectionFound = false;
        for (const [section, pattern] of Object.entries(sectionPatterns)) {
            if (pattern.test(line)) {
                // Save previous section
                if (currentSection !== 'brief' && currentContent.length > 0) {
                    sections[currentSection] = currentContent.join('\n').trim();
                } else if (currentSection === 'brief' && currentContent.length > 0) {
                    sections.brief = currentContent.join('\n').trim();
                    sections.detailed = '';
                }
                // Start new section
                currentSection = section;
                currentContent = [];
                sectionFound = true;
                break;
            }
        }

        if (!sectionFound) {
            // First non-empty line after brief becomes detailed description
            if (currentSection === 'brief' && line && sections.brief && !sections.detailed) {
                sections.detailed = line;
                currentContent = [line];
            } else {
                currentContent.push(line);
            }
        }
    }

    // Save last section
    if (currentContent.length > 0) {
        if (currentSection === 'brief') {
            sections.brief = currentContent.join('\n').trim();
        } else {
            sections[currentSection] = currentContent.join('\n').trim();
        }
    }

    // If no sections found, treat entire docstring as brief
    if (!sections.brief && !sections.args && !sections.returns) {
        sections.brief = text;
    }

    // Build HTML
    let html = '<div class="space-y-4">';

    // Brief description
    if (sections.brief) {
        html += `<div class="text-base text-gray-200 leading-relaxed">${formatText(sections.brief)}</div>`;
    }

    // Detailed description
    if (sections.detailed) {
        html += `<div class="text-sm text-gray-300 mt-2 leading-relaxed">${formatText(sections.detailed)}</div>`;
    }

    // Usage section
    if (sections.usage) {
        html += `<div class="mt-4 pt-3 border-t border-white/10">
            <div class="text-xs font-semibold text-indigo-400 uppercase tracking-wide mb-2">Usage</div>
            <div class="text-sm text-gray-300 leading-relaxed">${formatText(sections.usage)}</div>
        </div>`;
    }

    // Args section
    if (sections.args) {
        html += `<div class="mt-4 pt-3 border-t border-white/10">
            <div class="text-xs font-semibold text-indigo-400 uppercase tracking-wide mb-2">Parameters</div>
            <div class="text-sm text-gray-300 space-y-2">${formatArgs(sections.args)}</div>
        </div>`;
    }

    // Returns section
    if (sections.returns) {
        html += `<div class="mt-4 pt-3 border-t border-white/10">
            <div class="text-xs font-semibold text-indigo-400 uppercase tracking-wide mb-2">Returns</div>
            <div class="text-sm text-gray-300 leading-relaxed">${formatText(sections.returns)}</div>
        </div>`;
    }

    // Examples section
    if (sections.examples) {
        html += `<div class="mt-4 pt-3 border-t border-white/10">
            <div class="text-xs font-semibold text-indigo-400 uppercase tracking-wide mb-2">Examples</div>
            <div class="text-sm text-gray-300">${formatExamples(sections.examples)}</div>
        </div>`;
    }

    // Raises section
    if (sections.raises) {
        html += `<div class="mt-4 pt-3 border-t border-white/10">
            <div class="text-xs font-semibold text-yellow-400 uppercase tracking-wide mb-2">Raises</div>
            <div class="text-sm text-gray-300">${formatText(sections.raises)}</div>
        </div>`;
    }

    // Notes section
    if (sections.notes) {
        html += `<div class="mt-4 pt-3 border-t border-white/10">
            <div class="text-xs font-semibold text-blue-400 uppercase tracking-wide mb-2">Notes</div>
            <div class="text-sm text-gray-300">${formatText(sections.notes)}</div>
        </div>`;
    }

    // See Also section
    if (sections.seeAlso) {
        html += `<div class="mt-4 pt-3 border-t border-white/10">
            <div class="text-xs font-semibold text-purple-400 uppercase tracking-wide mb-2">See Also</div>
            <div class="text-sm text-gray-300">${formatText(sections.seeAlso)}</div>
        </div>`;
    }

    html += '</div>';
    return html;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatText(text) {
    if (!text) return '';

    // Handle code blocks first (before escaping HTML)
    const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
    const codeBlocks = [];
    let codeBlockIndex = 0;
    let processed = text.replace(codeBlockRegex, (match, lang, code) => {
        const placeholder = `__CODE_BLOCK_${codeBlockIndex}__`;
        codeBlocks.push({ lang: lang || '', code: code.trim() });
        codeBlockIndex++;
        return placeholder;
    });

    // Convert markdown-style formatting
    let formatted = escapeHtml(processed);

    // Restore code blocks with proper formatting
    codeBlocks.forEach((block, idx) => {
        const placeholder = `__CODE_BLOCK_${idx}__`;
        formatted = formatted.replace(placeholder,
            `<pre class="bg-black/40 p-3 rounded text-xs text-gray-300 font-mono overflow-x-auto border border-white/10 my-2"><code>${escapeHtml(block.code)}</code></pre>`
        );
    });

    // Convert **bold** to <strong>
    formatted = formatted.replace(/\*\*(.+?)\*\*/g, '<strong class="text-white font-semibold">$1</strong>');

    // Convert *italic* to <em>
    formatted = formatted.replace(/(?<!\*)\*(?!\*)([^*]+?)\*(?!\*)/g, '<em class="text-gray-300">$1</em>');

    // Convert `code` to <code> (inline code, not in code blocks)
    formatted = formatted.replace(/`([^`\n]+)`/g, '<code class="bg-black/30 px-1 py-0.5 rounded text-indigo-300 font-mono text-xs">$1</code>');

    // Convert bullet points (properly handle lists)
    const lines = formatted.split('<br>');
    let inList = false;
    let listItems = [];
    let result = [];

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        const bulletMatch = line.match(/^([-*]|\d+\.)\s+(.+)$/);

        if (bulletMatch) {
            if (!inList) {
                if (listItems.length > 0) {
                    result.push(listItems.join(''));
                    listItems = [];
                }
                inList = true;
            }
            listItems.push(`<li class="ml-4 mb-1">${bulletMatch[2]}</li>`);
        } else {
            if (inList) {
                result.push(`<ul class="list-disc space-y-1 my-2 ml-4">${listItems.join('')}</ul>`);
                listItems = [];
                inList = false;
            }
            if (line.trim()) {
                result.push(line);
            }
        }
    }

    if (inList && listItems.length > 0) {
        result.push(`<ul class="list-disc space-y-1 my-2 ml-4">${listItems.join('')}</ul>`);
    }

    formatted = result.length > 0 ? result.join('<br>') : formatted;

    // Convert line breaks (but preserve existing HTML)
    if (!formatted.includes('<pre>') && !formatted.includes('<ul>')) {
        formatted = formatted.replace(/\n/g, '<br>');
    }

    return formatted;
}

function formatArgs(argsText) {
    if (!argsText) return '';

    const lines = argsText.split('\n');
    let html = '';
    let currentParam = null;
    let paramDetails = [];

    for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) continue;

        // Check if this is a parameter name (supports various formats):
        // - name: description
        // - name (type): description
        // - name (type, optional): description
        const paramMatch = trimmed.match(/^(\w+)(?:\s*\(([^)]+)\))?:\s*(.+)$/);
        if (paramMatch) {
            // Save previous param
            if (currentParam) {
                const typeInfo = currentParam.type ? `<span class="text-purple-400 text-xs">(${currentParam.type})</span>` : '';
                html += `<div class="mb-3 pb-2 border-b border-white/5">
                    <div class="flex items-center gap-2">
                        <span class="font-mono text-indigo-300 font-semibold">${currentParam.name}</span>
                        ${typeInfo}
                    </div>
                    <div class="text-gray-400 text-xs ml-4 mt-1">${formatText(currentParam.desc)}</div>
                    ${paramDetails.length > 0 ? `<ul class="text-xs text-gray-500 ml-6 mt-1 space-y-1 list-disc">${paramDetails.map(d => `<li>${formatText(d)}</li>`).join('')}</ul>` : ''}
                </div>`;
            }
            // Start new param
            currentParam = {
                name: paramMatch[1],
                type: paramMatch[2] || null,
                desc: paramMatch[3]
            };
            paramDetails = [];
        } else if (trimmed.match(/^[-*]\s+/) && currentParam) {
            // Detail line for current param (bullet point)
            paramDetails.push(trimmed.replace(/^[-*]\s+/, ''));
        } else if (trimmed.match(/^\s{4,}/) && currentParam) {
            // Indented continuation line
            currentParam.desc += ' ' + trimmed.trim();
        } else if (currentParam && !trimmed.match(/^\w+:/)) {
            // Continuation of param description (not a new param)
            currentParam.desc += ' ' + trimmed;
        }
    }

    // Save last param
    if (currentParam) {
        const typeInfo = currentParam.type ? `<span class="text-purple-400 text-xs">(${currentParam.type})</span>` : '';
        html += `<div class="mb-3 pb-2 border-b border-white/5">
            <div class="flex items-center gap-2">
                <span class="font-mono text-indigo-300 font-semibold">${currentParam.name}</span>
                ${typeInfo}
            </div>
            <div class="text-gray-400 text-xs ml-4 mt-1">${formatText(currentParam.desc)}</div>
            ${paramDetails.length > 0 ? `<ul class="text-xs text-gray-500 ml-6 mt-1 space-y-1 list-disc">${paramDetails.map(d => `<li>${formatText(d)}</li>`).join('')}</ul>` : ''}
        </div>`;
    }

    return html || formatText(argsText);
}

function formatExamples(examplesText) {
    if (!examplesText) return '';

    // Check if it's already a code block
    const codeBlockMatch = examplesText.match(/```(\w+)?\n([\s\S]*?)```/);
    if (codeBlockMatch) {
        return `<pre class="bg-black/40 p-3 rounded text-xs text-gray-300 font-mono overflow-x-auto border border-white/10 my-2"><code>${escapeHtml(codeBlockMatch[2].trim())}</code></pre>`;
    }

    // Split by example headers (e.g., "Example 1:", "Basic usage:", etc.)
    const parts = examplesText.split(/(?:^|\n)([A-Z][^:\n]+:)/gm);
    let html = '<div class="space-y-4">';
    let hasStructured = false;

    for (let i = 0; i < parts.length; i += 2) {
        if (i + 1 < parts.length && parts[i + 2]) {
            const title = parts[i + 1].replace(':', '').trim();
            const code = parts[i + 2].trim();

            if (code) {
                hasStructured = true;
                html += `<div class="mb-4">
                    <div class="text-xs font-semibold text-green-400 mb-2">${escapeHtml(title)}</div>
                    <pre class="bg-black/40 p-3 rounded text-xs text-gray-300 font-mono overflow-x-auto border border-white/10"><code>${escapeHtml(code)}</code></pre>
                </div>`;
            }
        }
    }

    // If no structured examples, check for plain code or format as text
    if (!hasStructured) {
        const trimmed = examplesText.trim();
        // If it looks like code (has indentation, keywords, etc.), format as code block
        if (trimmed.match(/^(def |class |import |from |\s{4,})/m)) {
            html = `<pre class="bg-black/40 p-3 rounded text-xs text-gray-300 font-mono overflow-x-auto border border-white/10"><code>${escapeHtml(trimmed)}</code></pre>`;
        } else {
            // Format as regular text with markdown support
            html = formatText(trimmed);
        }
    } else {
        html += '</div>';
    }

    return html;
}
