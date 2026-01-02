import React from 'react';

const ServerBuilder = () => {
    return (
        <div className="page-container">
            <h1 style={{ marginBottom: '10px' }}>Server Builder</h1>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '30px' }}>
                Scaffold a new FastMCP server with SOTA standards.
            </p>

            <div style={{
                background: 'var(--bg-card)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-lg)',
                padding: '30px',
                maxWidth: '800px'
            }}>
                <div style={{ display: 'grid', gap: '20px' }}>
                    <div>
                        <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: 500 }}>Server Name</label>
                        <input
                            type="text"
                            placeholder="e.g. my-awesome-server"
                            style={{
                                width: '100%',
                                padding: '10px 12px',
                                background: 'var(--bg-panel)',
                                border: '1px solid var(--border-subtle)',
                                borderRadius: 'var(--radius-md)',
                                color: 'var(--text-primary)',
                                outline: 'none'
                            }}
                        />
                    </div>
                    <div>
                        <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: 500 }}>Description</label>
                        <textarea
                            placeholder="A brief description of what this server does..."
                            style={{
                                width: '100%',
                                height: '100px',
                                padding: '10px 12px',
                                background: 'var(--bg-panel)',
                                border: '1px solid var(--border-subtle)',
                                borderRadius: 'var(--radius-md)',
                                color: 'var(--text-primary)',
                                outline: 'none',
                                resize: 'none'
                            }}
                        />
                    </div>
                    <button style={{
                        background: 'var(--accent-primary)',
                        color: 'white',
                        border: 'none',
                        padding: '12px',
                        borderRadius: 'var(--radius-md)',
                        fontWeight: 600,
                        cursor: 'pointer'
                    }}>
                        Create Server
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ServerBuilder;
