import React from 'react';
import { Home, Server, Settings, Activity, Box, Hammer, Wrench, FileJson } from 'lucide-react';
import { NavLink } from 'react-router-dom';
import '../../styles/layout.css';

const Sidebar = () => {
    return (
        <aside className="sidebar-area">
            <div className="sidebar-header" style={{ padding: '20px', display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--accent-primary)' }}>
                <Box size={24} />
                <span style={{ fontWeight: 700, fontSize: '18px', letterSpacing: '0.5px' }}>MCP Studio</span>
            </div>

            <nav style={{ flex: 1, padding: '10px' }}>
                <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '5px' }}>
                    <NavItem to="/" icon={<Home size={20} />} label="Dashboard" />
                    <NavItem to="/servers" icon={<Server size={20} />} label="Servers" />
                    <NavItem to="/monitoring" icon={<Activity size={20} />} label="Monitoring" />
                    <NavItem to="/settings" icon={<Settings size={20} />} label="Settings" />
                </ul>

                <div style={{ marginTop: '20px', padding: '0 12px' }}>
                    <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px' }}>Builders</span>
                </div>
                <ul style={{ listStyle: 'none', padding: '10px 0', margin: 0, display: 'flex', flexDirection: 'column', gap: '5px' }}>
                    <NavItem to="/builder/server" icon={<Hammer size={20} />} label="Server Builder" />
                    <NavItem to="/builder/tool" icon={<Wrench size={20} />} label="Tool Builder" />
                    <NavItem to="/builder/config" icon={<FileJson size={20} />} label="Config Builder" />
                </ul>
            </nav>

            <div className="sidebar-footer" style={{ padding: '20px', borderTop: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                    v2.0.0 (SOTA)
                </div>
            </div>
        </aside>
    );
};

const NavItem = ({ to, icon, label }) => (
    <li>
        <NavLink
            to={to}
            className={({ isActive }) => isActive ? 'nav-item active' : 'nav-item'}
            style={({ isActive }) => ({
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '10px 12px',
                borderRadius: 'var(--radius-md)',
                color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
                backgroundColor: isActive ? 'var(--bg-glass)' : 'transparent',
                textDecoration: 'none',
                transition: 'var(--transition-fast)',
                borderLeft: isActive ? '3px solid var(--accent-primary)' : '3px solid transparent'
            })}
        >
            {icon}
            <span style={{ fontSize: '14px', fontWeight: 500 }}>{label}</span>
            {/* 
        Note: The explicit style prop overrides class-based styles for now, 
        but in a larger app we should move these to CSS classes.
       */}
        </NavLink>
    </li>
);

export default Sidebar;
