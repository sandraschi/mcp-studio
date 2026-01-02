import React, { useEffect, useState } from 'react';
import { mcpServersService } from '../../services/mcpServers';
import { Terminal, Square, Play, Settings } from 'lucide-react';

const MCPServersList = () => {
    const [servers, setServers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchServers = async () => {
            try {
                const data = await mcpServersService.getServers();
                setServers(data);
            } catch (err) {
                setError(err.message);
                // Fallback to empty list or mock if verify failed (optional, staying with empty for now)
            } finally {
                setLoading(false);
            }
        };

        fetchServers();
    }, []);

    const handleStart = async (id) => {
        try {
            await mcpServersService.startServer(id);
            // Refresh list
            const data = await mcpServersService.getServers();
            setServers(data);
        } catch (err) {
            console.error("Failed to start server", err);
        }
    };

    const handleStop = async (id) => {
        try {
            await mcpServersService.stopServer(id);
            // Refresh list
            const data = await mcpServersService.getServers();
            setServers(data);
        } catch (err) {
            console.error("Failed to stop server", err);
        }
    };

    if (loading) return <div>Loading servers...</div>;
    if (error) return <div style={{ color: 'red' }}>Error loading servers: {error}</div>;

    return (
        <div style={{ display: 'grid', gap: '15px' }}>
            {servers.length === 0 && <p>No servers found.</p>}
            {servers.map((server) => (
                <div key={server.id} style={{
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-md)',
                    padding: '15px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between'
                }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
                        <div style={{
                            width: '40px',
                            height: '40px',
                            background: 'var(--bg-panel)',
                            borderRadius: '8px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            border: '1px solid var(--border-active)'
                        }}>
                            <Terminal size={20} color="var(--accent-primary)" />
                        </div>
                        <div>
                            <h3 style={{ margin: '0 0 4px 0', fontSize: '16px' }}>{server.name}</h3>
                            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                                {server.status === 'running' ? 'Running' : 'Stopped'} • {server.command}
                            </span>
                        </div>
                    </div>

                    <div style={{ display: 'flex', gap: '10px' }}>
                        {server.status === 'running' ? (
                            <button
                                onClick={() => handleStop(server.id)}
                                title="Stop"
                                style={{ background: 'transparent', border: '1px solid var(--border-subtle)', borderRadius: '4px', padding: '6px', color: 'var(--text-secondary)', cursor: 'pointer' }}
                            >
                                <Square size={16} />
                            </button>
                        ) : (
                            <button
                                onClick={() => handleStart(server.id)}
                                title="Start"
                                style={{ background: 'transparent', border: '1px solid var(--border-subtle)', borderRadius: '4px', padding: '6px', color: 'var(--text-secondary)', cursor: 'pointer' }}
                            >
                                <Play size={16} />
                            </button>
                        )}
                        <button title="Configure" style={{ background: 'transparent', border: '1px solid var(--border-subtle)', borderRadius: '4px', padding: '6px', color: 'var(--text-secondary)', cursor: 'pointer' }}>
                            <Settings size={16} />
                        </button>
                    </div>
                </div>
            ))}
        </div>
    );
};

export default MCPServersList;
