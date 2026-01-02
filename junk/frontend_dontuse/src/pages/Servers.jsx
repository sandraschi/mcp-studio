import React from 'react';
import { Plus } from 'lucide-react';
import MCPServersList from '../components/Dashboard/MCPServersList';

const Servers = () => {
    return (
        <div style={{ padding: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <h1 style={{ fontSize: '24px', fontWeight: 600, margin: 0 }}>MCP Servers</h1>
                <button style={{
                    background: 'var(--accent-primary)',
                    color: 'black',
                    border: 'none',
                    padding: '8px 16px',
                    borderRadius: 'var(--radius-sm)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    fontWeight: 600,
                    cursor: 'pointer'
                }}>
                    <Plus size={16} /> New Server
                </button>
            </div>

            <MCPServersList />
        </div>
    );
};

export default Servers;
