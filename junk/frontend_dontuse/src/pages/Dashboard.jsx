import React from 'react';
import RepoList from '../components/Dashboard/RepoList';

const Dashboard = () => {
    return (
        <div style={{ padding: '20px' }}>
            <h1 style={{ fontSize: '24px', marginBottom: '20px', fontWeight: 600 }}>Dashboard</h1>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>
                {/* Active Servers Card */}
                <div className="card" style={{
                    background: 'var(--bg-card)',
                    padding: '20px',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border-subtle)',
                    backdropFilter: 'blur(10px)'
                }}>
                    <h3 style={{ margin: '0 0 10px 0', fontSize: '16px', color: 'var(--text-secondary)' }}>Active Servers</h3>
                    <p style={{ fontSize: '28px', margin: 0, fontWeight: 700, color: 'var(--accent-primary)' }}>12</p>
                </div>

                {/* Total Tools Card */}
                <div className="card" style={{
                    background: 'var(--bg-card)',
                    padding: '20px',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border-subtle)',
                    backdropFilter: 'blur(10px)'
                }}>
                    <h3 style={{ margin: '0 0 10px 0', fontSize: '16px', color: 'var(--text-secondary)' }}>Total Tools</h3>
                    <p style={{ fontSize: '28px', margin: 0, fontWeight: 700, color: 'var(--accent-secondary)' }}>148</p>
                </div>

                {/* System Health Card */}
                <div className="card" style={{
                    background: 'var(--bg-card)',
                    padding: '20px',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border-subtle)',
                    backdropFilter: 'blur(10px)'
                }}>
                    <h3 style={{ margin: '0 0 10px 0', fontSize: '16px', color: 'var(--text-secondary)' }}>System Health</h3>
                    <p style={{ fontSize: '28px', margin: 0, fontWeight: 700, color: 'var(--accent-success)' }}>98%</p>
                </div>
            </div>

            <div style={{ marginTop: '20px' }}>
                <RepoList />
            </div>
        </div>
    );
};

export default Dashboard;
