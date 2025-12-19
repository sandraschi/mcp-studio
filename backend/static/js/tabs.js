// ═══════════════════════════════════════════════════════════════════
// TAB SWITCHING - Navigation between dashboard sections
// ═══════════════════════════════════════════════════════════════════

// Tab switching functionality
function switchTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
    document.querySelectorAll('[id^="tab-"]').forEach(el => {
        el.classList.remove('tab-active');
        el.classList.add('text-gray-400');
    });
    document.getElementById('content-' + tabId).classList.remove('hidden');
    document.getElementById('tab-' + tabId).classList.add('tab-active');
    document.getElementById('tab-' + tabId).classList.remove('text-gray-400');
}

// Initialize tab event listeners when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Add click handlers to tab buttons
    document.querySelectorAll('[id^="tab-"]').forEach(tab => {
        tab.addEventListener('click', function() {
            const tabId = this.id.replace('tab-', '');
            switchTab(tabId);
        });
    });
});
