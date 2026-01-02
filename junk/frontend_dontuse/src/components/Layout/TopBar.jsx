import React from 'react';
import { Bell, User, Search } from 'lucide-react';
import '../../styles/layout.css';

const TopBar = () => {
    return (
        <header className="topbar-area">
            {/* Search Bar */}
            <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: '12px' }}>
                <Search size={18} color="var(--text-muted)" />
                <input
                    type="text"
                    placeholder="Search servers, tools, or logs..."
                    style={{
                        background: 'transparent',
                        border: 'none',
                        color: 'var(--text-primary)',
                        fontSize: '14px',
                        width: '100%',
                        outline: 'none'
                    }}
                />
            </div>

            {/* Actions */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
                <button style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)' }}>
                    <Bell size={20} />
                </button>
                <div style={{ width: '32px', height: '32px', borderRadius: '50%', background: 'var(--bg-card)', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid var(--border-active)' }}>
                    <User size={18} color="var(--accent-primary)" />
                </div>
            </div>
        </header>
    );
};

export default TopBar;
