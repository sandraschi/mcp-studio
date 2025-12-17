// ═══════════════════════════════════════════════════════════════════
// CLIENT MANAGEMENT - MCP client configuration and management
// ═══════════════════════════════════════════════════════════════════

// Global client data
let clientsData = {};

// Load clients from API
async function loadClients() {
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 3000); // 3 second timeout

        const res = await fetch('/api/v1/clients/', { signal: controller.signal });
        clearTimeout(timeoutId);

        if (!res.ok) {
            throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        }

        const responseData = await res.json();
        clientsData = responseData.clients || [];
        renderClients();
        updateStats();
    } catch (e) {
        console.error('Failed to load clients:', e);
        // Show error in UI but don't block
        document.getElementById('clients-list').innerHTML = `
            <div class="p-4 text-center text-gray-500">
                <p>⚠️ Failed to load clients</p>
                <p class="text-xs mt-2">${e.message || 'Connection timeout'}</p>
                <button onclick="loadClients()" class="mt-3 text-xs text-indigo-400 hover:text-indigo-300">Retry</button>
            </div>
        `;
    }
}

// Render clients in the UI
function renderClients() {
    const list = document.getElementById('clients-list');
    const detail = document.getElementById('clients-detail');

    if (!clientsData || clientsData.length === 0) {
        list.innerHTML = '<div class="text-gray-500 text-sm">No MCP clients found</div>';
        detail.innerHTML = '<div class="text-gray-500">No MCP client configurations found</div>';
        return;
    }

    // Compact list for overview
    let listHtml = '';
    for (const client of clientsData) {
        const icon = client.id.includes('claude') ? '🟣' : client.id.includes('cursor') ? '🔵' : client.id.includes('zed') ? '⚡' : client.id.includes('windsurf') ? '🌊' : '🟢';
        const installedBadge = client.installed ? '<span class="text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded-full">✅ Installed</span>' : '<span class="text-xs bg-gray-500/20 text-gray-400 px-2 py-1 rounded-full">❌ Not Found</span>';
        const serverCount = client.server_count > 0 ? `<span class="text-xs text-indigo-400">${client.server_count} servers</span>` : '';

        listHtml += `
            <div class="flex items-center justify-between p-3 bg-white/5 rounded-lg hover:bg-white/10">
                <div class="flex items-center gap-3 flex-1 cursor-pointer" onclick="switchTab('clients'); setTimeout(() => document.getElementById('clients-detail').scrollIntoView({behavior: 'smooth', block: 'start'}), 100);">
                    <span class="text-lg">${icon}</span>
                    <div>
                        <div class="font-medium">${client.name}</div>
                        <div class="text-xs text-gray-400">${client.platform} • ${client.client_type}</div>
                        <div class="flex gap-2 mt-1">
                            ${installedBadge}
                            ${serverCount}
                        </div>
                    </div>
                </div>
                <button class="text-gray-400 hover:text-indigo-400 transition-colors px-2 py-1 rounded hover:bg-white/5" onclick="event.stopPropagation(); window.location.href='/clients/${client.id}'" title="View client details">
                    →
                </button>
            </div>
        `;
    }
    list.innerHTML = listHtml;

    // Detailed view - Client Information
    let detailHtml = '<div class="space-y-6">';
    for (const client of clientsData) {
        const icon = client.id.includes('claude') ? '🟣' : client.id.includes('cursor') ? '🔵' : client.id.includes('zed') ? '⚡' : client.id.includes('windsurf') ? '🌊' : '🟢';
        detailHtml += `
            <div class="border border-white/10 rounded-xl overflow-hidden">
                <div class="px-4 py-3 bg-white/5 flex items-center gap-3">
                    <span class="text-xl">${icon}</span>
                    <div>
                        <div class="font-medium">${client.name}</div>
                        <div class="text-xs text-gray-400">${client.platform} • ${client.client_type}</div>
                    </div>
                </div>
                <div class="p-4">
                    <p class="text-sm text-gray-300 mb-3">${client.short_description}</p>
                    <div class="flex gap-2 mb-3">
                        ${client.installed ? '<span class="text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded-full">✅ Installed</span>' : '<span class="text-xs bg-gray-500/20 text-gray-400 px-2 py-1 rounded-full">❌ Not Found</span>'}
                        ${client.server_count > 0 ? `<span class="text-xs bg-indigo-500/20 text-indigo-400 px-2 py-1 rounded-full">🔧 ${client.server_count} servers configured</span>` : '<span class="text-xs bg-orange-500/20 text-orange-400 px-2 py-1 rounded-full">⚠️ No servers configured</span>'}
                    </div>
                    ${client.homepage ? `<p class="text-xs text-blue-400"><a href="${client.homepage}" target="_blank" class="hover:text-blue-300">🌐 Homepage</a></p>` : ''}
                    ${client.documentation ? `<p class="text-xs text-blue-400"><a href="${client.documentation}" target="_blank" class="hover:text-blue-300">📚 Documentation</a></p>` : ''}
                    ${client.github ? `<p class="text-xs text-blue-400"><a href="${client.github}" target="_blank" class="hover:text-blue-300">🐙 GitHub</a></p>` : ''}
                </div>
            </div>
        `;
    }
    detailHtml += '</div>';
    detail.innerHTML = detailHtml;
}

// Client information database
const clientInfo = {
    'claude-desktop': {
        name: 'Claude Desktop',
        description: 'Official desktop application from Anthropic for interacting with Claude AI.',
        website: 'https://claude.ai/download',
        configLocation: 'Config file contains MCP server definitions used by Claude Desktop.',
        icon: '🟣',
        developer: 'Anthropic'
    },
    'cursor': {
        name: 'Cursor IDE',
        description: 'AI-first code editor built on VS Code, designed for pair programming with AI.',
        website: 'https://cursor.sh',
        configLocation: 'Uses Cline extension settings or .cursor/mcp.json for MCP server configuration.',
        icon: '🔵',
        developer: 'Cursor'
    },
    'windsurf-ide': {
        name: 'Windsurf IDE',
        description: 'AI-powered code editor from Codeium, built for modern development workflows.',
        website: 'https://codeium.com/windsurf',
        configLocation: 'MCP servers configured in Windsurf settings or mcp_config.json.',
        icon: '🟢',
        developer: 'Codeium'
    },
    'zed-ide': {
        name: 'Zed Editor',
        description: 'High-performance, multiplayer code editor written in Rust with AI capabilities.',
        website: 'https://zed.dev',
        configLocation: 'MCP servers configured in settings.json under mcpServers key.',
        icon: '⚡',
        developer: 'Zed Industries'
    },
    'antigravity-ide': {
        name: 'Antigravity IDE',
        description: 'AI-powered IDE from GitKraken with integrated MCP server support.',
        website: 'https://www.gitkraken.com/antigravity',
        configLocation: 'MCP servers managed through the IDE UI, stored in mcp_config.json.',
        icon: '▶️',
        developer: 'GitKraken'
    },
    'cline': {
        name: 'Cline (VSCode Extension)',
        description: 'VSCode extension for Claude AI, formerly known as Claude Dev.',
        website: 'https://marketplace.visualstudio.com/items?itemName=saoudrizwan.claude-dev',
        configLocation: 'MCP servers configured in VSCode globalStorage settings.',
        icon: '💜',
        developer: 'Saoud Rizwan'
    }
};

// Show detailed client information
function showClientInfo(clientId) {
    const info = clientInfo[clientId] || {
        name: 'Unknown Client',
        description: 'No information available for this MCP client.',
        website: '#',
        configLocation: 'Configuration location unknown.',
        icon: '❓',
        developer: 'Unknown'
    };

    const modal = document.getElementById('modal');
    const modalContent = document.getElementById('modal-content');

    modalContent.innerHTML = `
        <div class="text-center mb-6">
            <span class="text-6xl mb-4 block">${info.icon}</span>
            <h2 class="text-2xl font-bold mb-2">${info.name}</h2>
            <p class="text-gray-300 mb-4">${info.description}</p>
            <div class="text-sm text-gray-400 mb-4">
                <strong>Developer:</strong> ${info.developer}<br>
                <strong>Config Location:</strong> ${info.configLocation}
            </div>
            <a href="${info.website}" target="_blank" class="inline-block bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg transition-colors">
                Visit Website →
            </a>
        </div>
    `;

    modal.classList.remove('hidden');
}
