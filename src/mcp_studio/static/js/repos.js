// ═══════════════════════════════════════════════════════════════════
// REPOSITORY SCANNING - MCP repository discovery and analysis
// ═══════════════════════════════════════════════════════════════════

// Global repository data
let reposData = [];

// Load repositories from API
async function loadRepos() {
    console.log('🔍 loadRepos() called');
    // Show progress UI
    const progressHtml = `
        <div class="p-4 space-y-3">
            <div class="text-sm font-semibold text-indigo-400 mb-3">Scanning Repositories...</div>
            <div id="scan-progress-display" class="space-y-2">
                <div class="flex items-center justify-between text-xs">
                    <span class="text-gray-400">Current:</span>
                    <span id="scan-current" class="text-gray-300 font-mono">-</span>
                </div>
                <div class="flex items-center justify-between text-xs">
                    <span class="text-gray-400">Progress:</span>
                    <span id="scan-progress" class="text-gray-300">0 / 0</span>
                </div>
                <div class="w-full bg-black/30 rounded-full h-2">
                    <div id="scan-progress-bar" class="bg-indigo-600 h-2 rounded-full transition-all duration-300" style="width: 0%"></div>
                </div>
                <div class="grid grid-cols-3 gap-2 mt-3 text-xs">
                    <div class="bg-green-500/10 p-2 rounded text-center">
                        <div id="scan-found" class="text-green-400 font-bold">0</div>
                        <div class="text-gray-500">MCP Repos</div>
                    </div>
                    <div class="bg-gray-500/10 p-2 rounded text-center">
                        <div id="scan-skipped" class="text-gray-400 font-bold">0</div>
                        <div class="text-gray-500">Skipped</div>
                    </div>
                    <div class="bg-red-500/10 p-2 rounded text-center">
                        <div id="scan-errors" class="text-red-400 font-bold">0</div>
                        <div class="text-gray-500">Errors</div>
                    </div>
                </div>
                  <div class="mt-3 max-h-32 overflow-y-auto bg-black/20 rounded p-2">
                    <div id="scan-activity" class="text-xs text-gray-400 font-mono space-y-1">
                        <div>Waiting for scan to start...</div>
                    </div>
                  </div>
                  <div class="mt-4">
                    <button onclick="toggleScanMonitor()" class="px-3 py-1 bg-blue-600 hover:bg-blue-500 rounded text-xs">
                      📊 Live Monitor
                    </button>
                    <div id="scan-monitor" class="hidden mt-2 max-h-48 overflow-y-auto bg-black/30 rounded p-3">
                      <div class="text-xs font-semibold text-blue-400 mb-2">🔄 Live Scan Progress</div>
                      <div id="scan-monitor-content" class="text-xs text-gray-300 font-mono space-y-1">
                        <div>Connecting to scan monitor...</div>
                      </div>
                    </div>
                  </div>
            </div>
        </div>
    `;
    document.getElementById('repos-health').innerHTML = progressHtml;
    document.getElementById('repos-detail').innerHTML = progressHtml;

        // Start the scan first, then poll for progress
    let progressInterval;
    try {
        console.log('Starting repository scan...');
        // Auto-show scan monitor section
        document.getElementById('scan-monitor-section').classList.remove('hidden');
        console.log('Scan monitor section should now be visible');
        startScanMonitor();
        console.log('Scan monitor started');

        const scanPromise = fetch('/api/v1/repos/run_scan/', { method: 'POST' });
        console.log('API call initiated:', scanPromise);

        // Start polling for progress immediately
        console.log('Starting progress polling...');
        let consecutiveErrors = 0;
        const maxConsecutiveErrors = 5;
        const scanStartTime = Date.now();
        const maxScanTime = 15 * 60 * 1000; // 15 minutes max scan time

        progressInterval = setInterval(async () => {
            // Check for overall scan timeout
            if (Date.now() - scanStartTime > maxScanTime) {
                console.error('Scan timeout reached, stopping progress monitoring');
                clearInterval(progressInterval);
                const activityDiv = document.getElementById('scan-activity');
                if (activityDiv) {
                    activityDiv.innerHTML += '<div class="text-yellow-400 font-semibold">⏰ Scan timeout reached (15 minutes). Scan may still be running on server.</div>';
                }
                return;
            }
            try {
                console.log('Polling progress...');
                const progressRes = await fetch('/api/v1/repos/progress', {
                    timeout: 5000, // 5 second timeout for progress requests
                    signal: AbortSignal.timeout(5000)
                });
                const progress = await progressRes.json();
                console.log('Progress received:', progress);

                // Reset error counter on successful response
                consecutiveErrors = 0;

                if (progress.status === 'scanning') {
                    // Update progress display
                    document.getElementById('scan-current').textContent = progress.current || '-';
                    document.getElementById('scan-progress').textContent = `${progress.done || 0} / ${progress.total || 0}`;

                    const percent = progress.total > 0 ? ((progress.done || 0) / progress.total) * 100 : 0;
                    document.getElementById('scan-progress-bar').style.width = percent + '%';

                    document.getElementById('scan-found').textContent = progress.mcp_repos_found || 0;
                    document.getElementById('scan-skipped').textContent = progress.skipped || 0;
                    document.getElementById('scan-errors').textContent = progress.errors || 0;

                    // Update activity log
                    if (progress.activity_log && progress.activity_log.length > 0) {
                        const activityDiv = document.getElementById('scan-activity');
                        let activityHtml = progress.activity_log.slice(-10).map(msg =>
                            `<div class="text-gray-300">${msg}</div>`
                        ).join('');

                        // Add recent errors if available
                        if (progress.recent_errors && progress.recent_errors.length > 0) {
                            activityHtml += '<div class="mt-2 pt-2 border-t border-gray-600">';
                            activityHtml += '<div class="text-red-400 text-xs font-semibold mb-1">Recent Errors:</div>';
                            progress.recent_errors.forEach(error => {
                                activityHtml += `<div class="text-red-300 text-xs">• ${error.repo}: ${error.error.substring(0, 50)}${error.error.length > 50 ? '...' : ''}</div>`;
                            });
                            activityHtml += '</div>';
                        }

                        activityDiv.innerHTML = activityHtml;
                        activityDiv.scrollTop = activityDiv.scrollHeight;
                    }
                } else if (progress.status === 'complete') {
                    // Scan finished, clear interval and load results
                    clearInterval(progressInterval);
                    document.getElementById('scan-progress-display').innerHTML =
                        `<div class="text-green-400 text-sm font-semibold">Scan complete! Loading results...</div>`;

                    // Fetch final results
                    const res = await fetch('/api/v1/repos');
                    const data = await res.json();
                    reposData = data.data || []; // Only set to array if data exists
                    renderRepos();
                    populateRepoSelector();
                    updateStats();
                }
            } catch (e) {
                consecutiveErrors++;
                console.error(`Error polling progress (${consecutiveErrors}/${maxConsecutiveErrors}):`, e);

                // Show error in activity log if too many consecutive errors
                if (consecutiveErrors >= 3) {
                    const activityDiv = document.getElementById('scan-activity');
                    if (activityDiv) {
                        const errorMsg = `<div class="text-red-400">⚠️ Progress polling error (${consecutiveErrors}): ${e.message}</div>`;
                        activityDiv.innerHTML += errorMsg;
                        activityDiv.scrollTop = activityDiv.scrollHeight;
                    }
                }

                // Stop polling if too many consecutive errors
                if (consecutiveErrors >= maxConsecutiveErrors) {
                    console.error('Too many consecutive progress polling errors, stopping scan monitoring');
                    clearInterval(progressInterval);
                    const activityDiv = document.getElementById('scan-activity');
                    if (activityDiv) {
                        activityDiv.innerHTML += '<div class="text-red-400 font-semibold">❌ Progress monitoring stopped due to repeated errors</div>';
                    }
                }
            }
        }, 500); // Poll every 500ms

        // Wait for scan to complete
        const res = await scanPromise;
        const data = await res.json();
        reposData = data.data || []; // Only set to array if data exists

        // Clear interval after scan completes
        clearInterval(progressInterval);
        stopScanMonitor();
        // Keep scan monitor visible for a bit to show completion
        setTimeout(() => {
            document.getElementById('scan-monitor-section').classList.add('hidden');
        }, 5000);

        renderRepos();
        populateRepoSelector();
        updateStats();
    } catch (e) {
        if (progressInterval) clearInterval(progressInterval);
        console.error('Error scanning repositories:', e);

        // Show error in scan monitor but keep the UI visible
        const monitorContent = document.getElementById('scan-monitor-content');
        if (monitorContent) {
            monitorContent.innerHTML = `
                <div class="text-red-400 font-semibold">❌ SCAN ERROR DETECTED</div>
                <div class="text-red-300 mt-2">${e.message || 'Unknown error occurred'}</div>
                <div class="text-gray-400 mt-2 text-xs">Check browser console and server logs for details</div>
                <div class="text-yellow-400 mt-2 text-xs">🔄 Scan may still be running in background...</div>
            `;
        }

        // Don't replace the entire scan UI - just add error notification
        const progressDisplay = document.getElementById('scan-progress-display');
        if (progressDisplay) {
            // Add error banner but keep existing progress visible
            const errorBanner = document.createElement('div');
            errorBanner.className = 'mb-4 p-3 bg-red-500/20 border border-red-500/50 rounded-lg';
            errorBanner.innerHTML = `
                <div class="flex items-center gap-2 text-red-400">
                    <span>⚠️</span>
                    <span class="font-semibold">Scan Error</span>
                </div>
                <div class="text-red-300 text-sm mt-1">${e.message || 'Unknown error occurred'}</div>
                <div class="text-gray-400 text-xs mt-1">The scan may continue in the background. Check progress above.</div>
            `;
            progressDisplay.insertBefore(errorBanner, progressDisplay.firstChild);
        }

        // Keep scan monitor visible for debugging
        setTimeout(() => {
            // Only hide after giving user time to see the error
            stopScanMonitor();
        }, 10000); // Keep visible for 10 seconds on error
    }
}

// Render repositories in the UI
function renderRepos() {
    const health = document.getElementById('repos-health');
    const detail = document.getElementById('repos-detail');
    const filter = document.getElementById('repo-filter').value;

    // Ensure reposData is always an array
    if (!Array.isArray(reposData)) {
        reposData = [];
    }

    let filtered = reposData;
    if (filter !== 'all') {
        filtered = reposData.filter(r => r.status === filter);
    }

    // Health summary for overview
    const sota = reposData.filter(r => r.status === 'sota').length;
    const improvable = reposData.filter(r => r.status === 'improvable').length;
    const runts = reposData.filter(r => r.status === 'runt').length;

    health.innerHTML = `
        <div class="grid grid-cols-3 gap-3 mb-4">
            <div class="p-3 bg-green-500/10 rounded-lg text-center">
                <div class="text-2xl font-bold text-green-400">${sota}</div>
                <div class="text-xs text-gray-400">✅ SOTA</div>
            </div>
            <div class="p-3 bg-yellow-500/10 rounded-lg text-center">
                <div class="text-2xl font-bold text-yellow-400">${improvable}</div>
                <div class="text-xs text-gray-400">⚠️ Improvable</div>
            </div>
            <div class="p-3 bg-red-500/10 rounded-lg text-center">
                <div class="text-2xl font-bold text-red-400">${runts}</div>
                <div class="text-xs text-gray-400">🐛 Issues</div>
            </div>
        </div>
        <div class="space-y-2">
            ${reposData.slice(0, 8).map(r => `
                <div class="flex items-center justify-between p-2 bg-white/5 rounded cursor-pointer hover:bg-white/10" onclick="showRepoDetail('${r.name}')">
                    <div class="flex items-center gap-2">
                        <span>${r.zoo_emoji}</span>
                        <span>${r.status_emoji}</span>
                        <span class="font-medium">${r.name}</span>
                    </div>
                    <span class="text-xs text-gray-400">${r.tools} tools</span>
                </div>
            `).join('')}
            ${reposData.length > 8 ? '<div class="text-center text-xs text-gray-500 pt-2">+' + (reposData.length - 8) + ' more...</div>' : ''}
        </div>
    `;

    // Detailed grid
    detail.innerHTML = `
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            ${filtered.map(r => `
                <div class="p-4 bg-white/5 rounded-xl hover:bg-white/10 cursor-pointer transition-all" onclick="showRepoDetail('${r.name}')">
                    <div class="flex items-center gap-2 mb-2">
                        <span class="text-xl">${r.zoo_emoji}</span>
                        <span class="text-lg">${r.status_emoji}</span>
                        <span class="font-semibold">${r.name}</span>
                    </div>
                    <div class="text-sm text-gray-300 mb-2">${r.fastmcp_version || 'unknown'} • ${r.tools} tools</div>
                    <div class="flex flex-wrap gap-1">
                        ${r.status === 'sota' ? '<span class="px-2 py-1 bg-green-500/20 text-green-400 text-xs rounded-full">✅ SOTA</span>' : ''}
                        ${r.status === 'improvable' ? '<span class="px-2 py-1 bg-yellow-500/20 text-yellow-400 text-xs rounded-full">⚠️ Improvable</span>' : ''}
                        ${r.status === 'runt' ? '<span class="px-2 py-1 bg-red-500/20 text-red-400 text-xs rounded-full">🐛 Issues</span>' : ''}
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

// Show repository detail modal
function showRepoDetail(repoName) {
    const repo = reposData.find(r => r.name === repoName);
    if (!repo) return;

    const modal = document.getElementById('modal');
    const modalContent = document.getElementById('modal-content');

    modalContent.innerHTML = `
        <div class="max-w-2xl">
            <div class="flex items-center gap-3 mb-4">
                <span class="text-4xl">${repo.zoo_emoji}</span>
                <div>
                    <h2 class="text-2xl font-bold">${repo.name}</h2>
                    <div class="flex items-center gap-2 text-sm text-gray-400">
                        <span>${repo.fastmcp_version || 'unknown'}</span>
                        <span>•</span>
                        <span>${repo.tools} tools</span>
                        <span>${repo.status_emoji}</span>
                    </div>
                </div>
            </div>

            <div class="grid grid-cols-2 gap-4 mb-4">
                <div class="p-3 bg-white/5 rounded-lg">
                    <div class="text-xs text-gray-400">Status</div>
                    <div class="font-semibold">
                        ${repo.status === 'sota' ? '✅ SOTA' : repo.status === 'improvable' ? '⚠️ Improvable' : '🐛 Issues'}
                    </div>
                </div>
                <div class="p-3 bg-white/5 rounded-lg">
                    <div class="text-xs text-gray-400">Tools</div>
                    <div class="font-semibold text-indigo-400">${repo.tools}</div>
                </div>
            </div>

            <div class="text-sm text-gray-300">
                <p><strong>Path:</strong> ${repo.path}</p>
                <p><strong>Status:</strong> ${repo.status}</p>
                ${repo.issues ? `<p><strong>Issues:</strong> ${repo.issues.join(', ')}</p>` : ''}
                ${repo.recommendations ? `<p><strong>Recommendations:</strong> ${repo.recommendations.join(', ')}</p>` : ''}
            </div>
        </div>
    `;

    modal.classList.remove('hidden');
}

// Populate repository selector dropdown
function populateRepoSelector() {
    const select = document.getElementById('repo-selector');
    if (!select || reposData.length === 0) return;

    select.innerHTML = '<option value="">Select a repository...</option>' +
        reposData.map(r => `<option value="${r.name}">${r.zoo_emoji} ${r.name} (${r.tools} tools)</option>`).join('');
}

// Initialize repository event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Repo filter change handler
    const repoFilter = document.getElementById('repo-filter');
    if (repoFilter) {
        repoFilter.addEventListener('change', renderRepos);
    }
});
