import React from 'react';
import Sidebar from './Sidebar';
import TopBar from './TopBar';
import '../../styles/layout.css';

const MainLayout = ({ children }) => {
    return (
        <div className="app-layout">
            <Sidebar />
            <TopBar />

            <main className="main-area">
                <div style={{
                    height: '100%',
                    overflowY: 'auto',
                    paddingRight: '4px' /* Space for scrollbar */
                }}>
                    {children}
                </div>
            </main>

            {/* Right Panel - Optional/Collapsible */}
            <aside className="right-panel-area">
                <div style={{ padding: '20px' }}>
                    <h3 style={{ margin: '0 0 15px 0', fontSize: '14px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px' }}>
                        System Status
                    </h3>
                    <div style={{ background: 'var(--bg-card)', padding: '15px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                            <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>CPU Usage</span>
                            <span style={{ fontSize: '13px', color: 'var(--accent-success)' }}>12%</span>
                        </div>
                        <div style={{ height: '4px', background: 'var(--bg-glass)', borderRadius: '2px', overflow: 'hidden' }}>
                            <div style={{ width: '12%', height: '100%', background: 'var(--accent-success)' }}></div>
                        </div>
                    </div>
                </div>
            </aside>
        </div>
    );
};

export default MainLayout;
