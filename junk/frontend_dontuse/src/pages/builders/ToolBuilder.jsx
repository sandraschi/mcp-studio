import React from 'react';

const ToolBuilder = () => {
    return (
        <div className="page-container">
            <h1 style={{ marginBottom: '10px' }}>Tool Builder</h1>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '30px' }}>
                Visually define new tools and generate Python @mcp.tool() decorators.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 400px', gap: '20px' }}>
                <div style={{
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-lg)',
                    padding: '25px'
                }}>
                    <h2 style={{ fontSize: '18px', marginBottom: '15px' }}>Tool Definition</h2>
                    <div style={{ display: 'grid', gap: '15px' }}>
                        <input
                            type="text"
                            placeholder="Tool Name (e.g. get_weather)"
                            className="input-base"
                            style={{ width: '100%', padding: '10px', background: 'var(--bg-panel)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)', color: 'var(--text-primary)' }}
                        />
                        <div style={{ minHeight: '200px', border: '2px dashed var(--border-subtle)', borderRadius: 'var(--radius-md)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
                            Parameters Editor coming soon...
                        </div>
                    </div>
                </div>

                <div style={{
                    background: 'var(--bg-panel)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-lg)',
                    padding: '20px'
                }}>
                    <h2 style={{ fontSize: '16px', marginBottom: '15px', color: 'var(--accent-primary)' }}>Code Preview</h2>
                    <pre style={{ margin: 0, fontSize: '13px', color: 'var(--text-secondary)' }}>
                        {`@mcp.tool()
def new_tool(param: str) -> str:
    """Description here"""
    return "Result"`}
                    </pre>
                </div>
            </div>
        </div>
    );
};

export default ToolBuilder;
