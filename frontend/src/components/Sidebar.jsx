import { NavLink } from 'react-router-dom';
import { useCampaign } from '../context/CampaignContext';

const navItems = [
    { path: '/search', icon: '🔍', label: 'Search Companies' },
    { path: '/companies', icon: '🏢', label: 'Companies' },
    { path: '/leads', icon: '🎯', label: 'Lead Pipeline' },
];

export default function Sidebar() {
    const { campaign, setCampaign } = useCampaign();

    return (
        <aside className="sidebar">
            <div className="sidebar-brand">
                <div className="brand-icon">⚡</div>
                <h1>LeadForge AI</h1>
            </div>


            <nav className="sidebar-nav">
                {navItems.map((item) => (
                    <NavLink
                        key={item.path}
                        to={item.path}
                        end={item.path === '/'}
                        className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
                    >
                        <span className="nav-icon">{item.icon}</span>
                        <span className="nav-label">{item.label}</span>
                    </NavLink>
                ))}
            </nav>
            <div style={{ padding: '0 16px', marginTop: 'auto' }}>
                <div className="glass-card no-hover" style={{ padding: '12px 16px', fontSize: '0.8rem' }}>
                    <div style={{ color: 'var(--text-muted)', marginBottom: '4px' }}>Powered by</div>
                    <div style={{ fontWeight: 600, color: 'var(--text-accent)' }}>Cerebras AI · Free Tier</div>
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', marginTop: '4px' }}>1M tokens/day</div>
                </div>
            </div>
        </aside>
    );
}
