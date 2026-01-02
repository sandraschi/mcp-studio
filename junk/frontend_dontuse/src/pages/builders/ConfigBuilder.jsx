import React from 'react';

const ConfigBuilder = () => {
    return (
        <div className="page-container">
            <h1 style={{ marginBottom: '10px' }}>Config Builder</h1>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '30px' }}>
                Manage your mcp.json and client configurations.
            </p>

            <div style={{
                background: 'var(--bg-card)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-lg)',
                padding: '25px'
            }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                    <h2 style={{ fontSize: '18px' }}>Active Servers</h2>
                    <button style={{
                        background: 'var(--bg-panel)',
                        border: '1px solid var(--border-subtle)',
                        padding: '6px 12px',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        color: 'var(--text-primary)'
                    }}>
                        Add External Server
                    </button>
                </div>

                <div style={{ display: 'grid', gap: '10px' }}>
                    <div style={{ padding: '12px', background: 'var(--bg-panel)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between' }}>
                        <span>weather-mcp</span>
                        <code style={{ color: 'var(--accent-primary)' }}>uvx weather-mcp</code>
                    </div>
                </div>

                <div style={{ marginTop: '30px' }}>
                    <button style={{
                        background: 'var(--accent-primary)',
                        color: 'white',
                        border: 'none',
                        padding: '12px 24px',
                        borderRadius: 'var(--radius-md)',
                        fontWeight: 600,
                        cursor: 'pointer'
                    }}>
                        Save to Config
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ConfigBuilder;
