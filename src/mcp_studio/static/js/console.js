// ═══════════════════════════════════════════════════════════════════
// EXECUTION CONSOLE - Interactive command execution
// ═══════════════════════════════════════════════════════════════════

let consoleHistory = [];
let historyIndex = -1;

// Execute console command
async function executeConsoleCommand() {
    const input = document.getElementById('console-input');
    const output = document.getElementById('console-output');
    const command = input.value.trim();

    if (!command) return;

    // Add to history
    consoleHistory.push(command);
    historyIndex = consoleHistory.length;

    // Add command to output
    addToConsole(`💻 $ ${command}`, 'command');

    try {
        // Here you would implement actual command execution
        // For now, just show a mock response
        addToConsole(`Executing: ${command}`, 'info');

        // Simulate command execution
        setTimeout(() => {
            addToConsole(`✅ Command "${command}" executed successfully`, 'success');
        }, 1000);

    } catch (e) {
        addToConsole(`❌ Error: ${e.message}`, 'error');
    }

    input.value = '';
}

// Add message to console output
function addToConsole(message, type = 'info') {
    const output = document.getElementById('console-output');
    const timestamp = new Date().toLocaleTimeString();

    const colorClass = {
        'command': 'text-blue-400',
        'success': 'text-green-400',
        'error': 'text-red-400',
        'warning': 'text-yellow-400',
        'info': 'text-gray-300'
    }[type] || 'text-gray-300';

    const emoji = {
        'command': '💻',
        'success': '✅',
        'error': '❌',
        'warning': '⚠️',
        'info': 'ℹ️'
    }[type] || '📝';

    const line = document.createElement('div');
    line.className = `mb-1 ${colorClass} font-mono text-sm`;
    line.innerHTML = `<span class="text-gray-500">${timestamp}</span> ${emoji} ${message}`;

    output.appendChild(line);
    output.scrollTop = output.scrollHeight;
}

// Clear console
function clearConsole() {
    document.getElementById('console-output').innerHTML = '<div class="text-gray-400">Console cleared...</div>';
}

// Console input handlers
document.addEventListener('DOMContentLoaded', function() {
    const consoleInput = document.getElementById('console-input');

    if (consoleInput) {
        consoleInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                executeConsoleCommand();
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                if (historyIndex > 0) {
                    historyIndex--;
                    this.value = consoleHistory[historyIndex];
                }
            } else if (e.key === 'ArrowDown') {
                e.preventDefault();
                if (historyIndex < consoleHistory.length - 1) {
                    historyIndex++;
                    this.value = consoleHistory[historyIndex];
                } else {
                    historyIndex = consoleHistory.length;
                    this.value = '';
                }
            }
        });
    }
});
