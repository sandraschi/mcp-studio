// ═══════════════════════════════════════════════════════════════════
// MAIN DASHBOARD COORDINATOR - Initializes all modules and handles global state
// ═══════════════════════════════════════════════════════════════════

// Global state
// reposData is declared in repos.js

// ═══════════════════════════════════════════════════════════════════
// UI FUNCTIONS - Implemented functionality for dashboard interactions
// ═══════════════════════════════════════════════════════════════════

// Theme management
function toggleTheme() {
    const html = document.documentElement;
    const themeIcon = document.getElementById('theme-icon-dark');
    const themeIconLight = document.getElementById('theme-icon-light');

    if (html.classList.contains('dark')) {
        // Switch to light theme
        html.classList.remove('dark');
        themeIcon.style.display = 'none';
        themeIconLight.style.display = 'inline';
        localStorage.setItem('theme', 'light');
    } else {
        // Switch to dark theme
        html.classList.add('dark');
        themeIcon.style.display = 'inline';
        themeIconLight.style.display = 'none';
        localStorage.setItem('theme', 'dark');
    }
}

// Initialize theme on page load
document.addEventListener('DOMContentLoaded', function() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    const html = document.documentElement;
    const themeIcon = document.getElementById('theme-icon-dark');
    const themeIconLight = document.getElementById('theme-icon-light');

    if (savedTheme === 'light') {
        html.classList.remove('dark');
        themeIcon.style.display = 'none';
        themeIconLight.style.display = 'inline';
    } else {
        html.classList.add('dark');
        themeIcon.style.display = 'inline';
        themeIconLight.style.display = 'none';
    }
});

// Help modal
function showHelp() {
    const modal = document.getElementById('modal');
    const modalContent = document.getElementById('modal-content');

    modalContent.innerHTML = `
        <div class="max-w-2xl">
            <div class="text-center mb-6">
                <span class="text-6xl mb-4 block">❓</span>
                <h2 class="text-2xl font-bold mb-4">MCP Studio Help</h2>
            </div>

            <div class="space-y-6">
                <div>
                    <h3 class="text-lg font-semibold mb-2">📊 Overview Tab</h3>
                    <p class="text-gray-300 text-sm">Dashboard overview with statistics, quick actions, and AI assistant.</p>
                </div>

                <div>
                    <h3 class="text-lg font-semibold mb-2">🔌 MCP Clients Tab</h3>
                    <p class="text-gray-300 text-sm">Discover and manage MCP client configurations on your system.</p>
                </div>

                <div>
                    <h3 class="text-lg font-semibold mb-2">📁 Repositories Tab</h3>
                    <p class="text-gray-300 text-sm">Scan and analyze MCP server repositories for compliance and quality.</p>
                </div>

                <div>
                    <h3 class="text-lg font-semibold mb-2">🔧 Tools Tab</h3>
                    <p class="text-gray-300 text-sm">Explore tools from scanned repositories and execute them directly.</p>
                </div>

                <div>
                    <h3 class="text-lg font-semibold mb-2">💻 Console Tab</h3>
                    <p class="text-gray-300 text-sm">Execute commands and interact with MCP servers directly.</p>
                </div>

                <div>
                    <h3 class="text-lg font-semibold mb-2">🤖 AI Assistant</h3>
                    <p class="text-gray-300 text-sm">Get AI-powered insights about your MCP setup and repositories.</p>
                </div>
            </div>

            <div class="mt-6 pt-4 border-t border-white/10">
                <p class="text-xs text-gray-400 text-center">
                    MCP Studio v0.2.1 - Mission Control for your MCP Zoo
                </p>
            </div>
        </div>
    `;

    modal.classList.remove('hidden');
}

// Logs modal
function showLogs() {
    const modal = document.getElementById('modal');
    const modalContent = document.getElementById('modal-content');

    // Show loading state first
    modalContent.innerHTML = `
        <div class="text-center py-8">
            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500 mx-auto mb-4"></div>
            <p class="text-gray-300">Loading logs...</p>
        </div>
    `;

    modal.classList.remove('hidden');

    // Try to load logs (this endpoint may not exist, so handle gracefully)
    fetch('/api/logs')
        .then(response => response.json())
        .then(data => {
            modalContent.innerHTML = `
                <div class="max-w-4xl">
                    <div class="flex justify-between items-center mb-4">
                        <h2 class="text-2xl font-bold">📋 System Logs</h2>
                        <button onclick="clearLogs()" class="px-3 py-1 bg-red-600 hover:bg-red-700 text-white text-sm rounded">
                            🗑️ Clear Logs
                        </button>
                    </div>

                    <div class="bg-black/50 rounded-lg p-4 max-h-96 overflow-y-auto">
                        <div id="logs-content" class="font-mono text-sm text-gray-300 space-y-1">
                            ${data.logs && data.logs.length > 0
                                ? data.logs.map(log => `<div class="text-gray-400">${log}</div>`).join('')
                                : '<div class="text-gray-500 italic">No logs available</div>'
                            }
                        </div>
                    </div>

                    <div class="mt-4 text-xs text-gray-400">
                        Showing last ${data.logs ? data.logs.length : 0} log entries
                    </div>
                </div>
            `;
        })
        .catch(error => {
            modalContent.innerHTML = `
                <div class="max-w-2xl">
                    <div class="text-center mb-6">
                        <span class="text-4xl mb-4 block">📋</span>
                        <h2 class="text-2xl font-bold mb-4">System Logs</h2>
                    </div>

                    <div class="bg-black/50 rounded-lg p-6 text-center">
                        <p class="text-gray-300 mb-4">Logs endpoint not available</p>
                        <p class="text-sm text-gray-400">The logging system is not currently configured.</p>
                    </div>
                </div>
            `;
        });
}

// Clear logs function
function clearLogs() {
    const logsContent = document.getElementById('logs-content');
    if (logsContent) {
        logsContent.innerHTML = '<div class="text-gray-500 italic">Logs cleared</div>';
    }
}

// AI Assistant functionality
let currentAIPrompt = '';
let aiIncludeRepos = false;

function setAIPrompt(text, includeRepos = false) {
    currentAIPrompt = text;
    aiIncludeRepos = includeRepos;

    // Switch to overview tab to show AI section
    switchTab('overview');

    // Update the AI prompt input
    const promptInput = document.getElementById('ai-prompt-input');
    if (promptInput) {
        promptInput.value = text;
    }

    // Update the checkbox
    const checkbox = document.getElementById('ai-include-repos');
    if (checkbox) {
        checkbox.checked = includeRepos;
    }

    // Scroll to AI section
    setTimeout(() => {
        const aiSection = document.querySelector('[data-ai-section]');
        if (aiSection) {
            aiSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }, 100);
}

function sendAIPrompt() {
    const promptInput = document.getElementById('ai-prompt-input');
    const includeReposCheckbox = document.getElementById('ai-include-repos');

    if (!promptInput) return;

    const prompt = promptInput.value.trim();
    const includeRepos = includeReposCheckbox ? includeReposCheckbox.checked : false;

    if (!prompt) {
        showToast('Please enter a prompt', 'warning');
        return;
    }

    // Show loading state
    showToast('🤖 Processing AI request...', 'info');

    // Prepare the request data
    const requestData = {
        prompt: prompt,
        include_repos: includeRepos
    };

    // If include_repos is true, add repository context
    if (includeRepos && typeof reposData !== 'undefined' && reposData.length > 0) {
        requestData.repo_context = reposData.map(repo => ({
            name: repo.name,
            status: repo.status,
            tools: repo.tools,
            fastmcp_version: repo.fastmcp_version
        }));
    }

    // Send to AI endpoint (this may not exist, so handle gracefully)
    fetch('/api/ai/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showToast(`❌ ${data.error}`, 'error');
            return;
        }

        // Show success and display result
        showToast('✅ AI response received', 'success');

        // For now, just log the response since we don't have a dedicated AI response UI
        console.log('AI Response:', data);

        // Could show in a modal or update a response area
        showModal(`
            <div class="max-w-2xl">
                <h2 class="text-2xl font-bold mb-4">🤖 AI Response</h2>
                <div class="bg-black/50 rounded-lg p-4 max-h-96 overflow-y-auto">
                    <pre class="text-gray-300 whitespace-pre-wrap font-sans">${data.response || 'No response received'}</pre>
                </div>
            </div>
        `);
    })
    .catch(error => {
        console.error('AI request failed:', error);
        showToast('❌ AI request failed - service not available', 'error');
    });
}

// ═══════════════════════════════════════════════════════════════════
// INITIALIZATION - Load all modules and set up the dashboard
// ═══════════════════════════════════════════════════════════════════

async function initDashboard() {
    console.log('🚀 Initializing MCP Studio Dashboard...');

    try {
        // Load initial data
        await loadClients();
        await loadInitialRepos();

        // Update UI
        updateStats();

        console.log('✅ Dashboard initialized successfully');
    } catch (e) {
        console.error('❌ Failed to initialize dashboard:', e);
    }
}

// Load initial repository data (if any exists)
async function loadInitialRepos() {
    try {
        const res = await fetch('/api/v1/repos');
        const data = await res.json();
        reposData = data.data || [];
        renderRepos();
        populateRepoSelector();
    } catch (e) {
        console.warn('No existing repo data:', e.message);
        reposData = [];
    }
}

// Update global statistics
function updateStats() {
    // Update repo count
    const repoCount = reposData.length;
    document.getElementById('stat-repos').textContent = repoCount;
    document.getElementById('repo-count').textContent = repoCount;

    // Update AI context stats
    document.getElementById('ai-context-repos').textContent = repoCount;
    document.getElementById('ai-context-tools').textContent = reposData.reduce((acc, r) => acc + r.tools, 0);
    document.getElementById('ai-context-sota').textContent = reposData.filter(r => r.status === 'sota').length;
    document.getElementById('ai-context-runts').textContent = reposData.filter(r => r.status === 'runt').length;
}

// ═══════════════════════════════════════════════════════════════════
// MODAL MANAGEMENT - Handle modal dialogs
// ═══════════════════════════════════════════════════════════════════

function showModal(content) {
    const modal = document.getElementById('modal');
    const modalContent = document.getElementById('modal-content');
    modalContent.innerHTML = content;
    modal.classList.remove('hidden');
}

function hideModal() {
    document.getElementById('modal').classList.add('hidden');
}

// ═══════════════════════════════════════════════════════════════════
// UTILITY FUNCTIONS - Global helpers
// ═══════════════════════════════════════════════════════════════════

// Toast notifications
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `fixed bottom-4 right-4 px-4 py-2 rounded-lg text-sm font-medium z-50 ${
        type === 'success' ? 'bg-green-500 text-white' :
        type === 'error' ? 'bg-red-500 text-white' :
        type === 'warning' ? 'bg-yellow-500 text-black' :
        'bg-blue-500 text-white'
    }`;
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// ═══════════════════════════════════════════════════════════════════
// SCAN MONITORING - Real-time scan progress
// ═══════════════════════════════════════════════════════════════════

let scanMonitorInterval;

function startScanMonitor() {
    const monitorContent = document.getElementById('scan-monitor-content');
    monitorContent.innerHTML = '<div>🔄 Connecting to scan monitor...</div>';

    scanMonitorInterval = setInterval(async () => {
        try {
            const res = await fetch('/api/v1/repos/progress');
            const progress = await res.json();

            monitorContent.innerHTML = progress.activity_log && progress.activity_log.length > 0
                ? progress.activity_log.slice(-15).map(msg => `<div>${msg}</div>`).join('')
                : '<div>⏳ Waiting for scan data...</div>';

            monitorContent.scrollTop = monitorContent.scrollHeight;
        } catch (e) {
            monitorContent.innerHTML = '<div class="text-red-400">❌ Monitor connection failed</div>';
        }
    }, 1000);
}

function stopScanMonitor() {
    if (scanMonitorInterval) {
        clearInterval(scanMonitorInterval);
        scanMonitorInterval = null;
    }
}

function toggleScanMonitor() {
    const monitor = document.getElementById('scan-monitor');
    const isHidden = monitor.classList.contains('hidden');

    if (isHidden) {
        monitor.classList.remove('hidden');
        startScanMonitor();
    } else {
        monitor.classList.add('hidden');
        stopScanMonitor();
    }
}

// ═══════════════════════════════════════════════════════════════════
// INITIALIZE WHEN DOM IS READY
// ═══════════════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', function() {
    console.log('📋 DOM loaded, initializing dashboard...');
    initDashboard();

    // Global modal close handler
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            hideModal();
        }
    });

    // Click outside modal to close
    document.getElementById('modal').addEventListener('click', function(e) {
        if (e.target === this) {
            hideModal();
        }
    });
});
