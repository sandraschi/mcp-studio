// ═══════════════════════════════════════════════════════════════════
// TOOL EXPLORATION - Browse and execute MCP tools
// ═══════════════════════════════════════════════════════════════════

// Load tools for selected repository
async function loadToolsForRepo(repoName) {
    if (!repoName) {
        document.getElementById('tools-list').innerHTML = `
            <div class="text-4xl mb-4">🔧</div>
            <div class="text-gray-500">Select a repository above to explore its tools</div>
        `;
        return;
    }

    try {
        const res = await fetch(`/api/v1/tools?repo=${repoName}`);
        const data = await res.json();

        if (data.tools && data.tools.length > 0) {
            renderTools(data.tools, repoName);
        } else {
            document.getElementById('tools-list').innerHTML = `
                <div class="text-yellow-400 text-center py-8">
                    <div class="text-4xl mb-4">⚠️</div>
                    <div>No tools found for ${repoName}</div>
                </div>
            `;
        }
    } catch (e) {
        console.error('Failed to load tools:', e);
        document.getElementById('tools-list').innerHTML = `
            <div class="text-red-400 text-center py-8">
                <div class="text-4xl mb-4">❌</div>
                <div>Failed to load tools: ${e.message}</div>
            </div>
        `;
    }
}

// Render tools in the UI
function renderTools(tools, repoName) {
    const html = `
        <div class="mb-6">
            <h3 class="text-lg font-semibold">🔧 Tools from ${repoName}</h3>
            <p class="text-gray-400 text-sm">${tools.length} tools available</p>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            ${tools.map(tool => `
                <div class="p-4 bg-white/5 rounded-xl hover:bg-white/10 cursor-pointer transition-all" onclick="showToolDetail('${tool.name}', '${repoName}')">
                    <div class="flex items-center gap-3 mb-2">
                        <span class="text-xl">🔧</span>
                        <div>
                            <div class="font-semibold">${tool.name}</div>
                            <div class="text-xs text-gray-400">Click to execute</div>
                        </div>
                    </div>
                    <div class="text-sm text-gray-300">${tool.description || 'No description available'}</div>
                </div>
            `).join('')}
        </div>
    `;

    document.getElementById('tools-list').innerHTML = html;
}

// Show tool execution modal
function showToolDetail(toolName, repoName) {
    const modal = document.getElementById('modal');
    const modalContent = document.getElementById('modal-content');

    modalContent.innerHTML = `
        <div class="max-w-2xl">
            <div class="flex items-center gap-3 mb-4">
                <span class="text-3xl">🔧</span>
                <div>
                    <h2 class="text-2xl font-bold">${toolName}</h2>
                    <p class="text-gray-400">From ${repoName}</p>
                </div>
            </div>

            <div class="mb-6">
                <label class="block text-sm font-medium mb-2">Parameters (JSON):</label>
                <textarea id="tool-params" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm font-mono min-h-24" placeholder='{"param": "value"}'></textarea>
            </div>

            <div class="flex gap-3">
                <button onclick="executeTool('${toolName}', '${repoName}')" class="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg transition-colors">
                    ▶️ Execute Tool
                </button>
                <button onclick="hideModal()" class="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg transition-colors">
                    Cancel
                </button>
            </div>

            <div id="tool-result" class="mt-6 hidden">
                <h3 class="font-semibold mb-2">📋 Result:</h3>
                <pre id="tool-result-content" class="bg-black/40 p-3 rounded text-xs text-gray-300 font-mono overflow-x-auto border border-white/10"></pre>
            </div>
        </div>
    `;

    modal.classList.remove('hidden');
}

// Execute a tool
async function executeTool(toolName, repoName) {
    const paramsInput = document.getElementById('tool-params');
    const resultDiv = document.getElementById('tool-result');
    const resultContent = document.getElementById('tool-result-content');

    let params = {};
    try {
        const paramsText = paramsInput.value.trim();
        if (paramsText) {
            params = JSON.parse(paramsText);
        }
    } catch (e) {
        showToast('❌ Invalid JSON parameters', 'error');
        return;
    }

    try {
        resultDiv.classList.add('hidden');
        showToast('⚡ Executing tool...', 'info');

        const res = await fetch(`/api/v1/tools/${toolName}/execute`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ repo: repoName, params })
        });

        const result = await res.json();

        resultContent.textContent = JSON.stringify(result, null, 2);
        resultDiv.classList.remove('hidden');

        showToast('✅ Tool executed successfully', 'success');
    } catch (e) {
        console.error('Tool execution failed:', e);
        resultContent.textContent = `Error: ${e.message}`;
        resultDiv.classList.remove('hidden');
        showToast('❌ Tool execution failed', 'error');
    }
}

// Initialize tool selector
document.addEventListener('DOMContentLoaded', function() {
    const repoSelector = document.getElementById('repo-selector');
    if (repoSelector) {
        repoSelector.addEventListener('change', function() {
            loadToolsForRepo(this.value);
        });
    }
});
