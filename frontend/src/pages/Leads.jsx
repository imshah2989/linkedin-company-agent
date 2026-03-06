import { useState, useEffect } from 'react';
import { api } from '../api';
import { useCampaign } from '../context/CampaignContext';

const PIPELINE_STAGES = [
    { key: 'new', label: 'New', color: '#6366f1', icon: '🆕' },
    { key: 'contacted', label: 'Contacted', color: '#0ea5e9', icon: '📧' },
    { key: 'replied', label: 'Replied', color: '#f59e0b', icon: '💬' },
    { key: 'meeting', label: 'Meeting', color: '#8b5cf6', icon: '📅' },
    { key: 'negotiation', label: 'Negotiation', color: '#06b6d4', icon: '🤝' },
    { key: 'closed_won', label: 'Won', color: '#10b981', icon: '🎉' },
    { key: 'closed_lost', label: 'Lost', color: '#ef4444', icon: '❌' },
];

export default function Leads() {
    const { campaign, setCampaign } = useCampaign();
    const [leads, setLeads] = useState([]);
    const [campaigns, setCampaigns] = useState(['Default']);
    const [loading, setLoading] = useState(true);
    const [toast, setToast] = useState(null);

    useEffect(() => { loadLeads(); }, [campaign]);
    useEffect(() => { loadCampaigns(); }, []);

    async function loadCampaigns() {
        try {
            const data = await api.getCampaigns();
            if (data.campaigns) setCampaigns(data.campaigns);
        } catch (e) { console.error(e); }
    }

    function showToast(msg, type = 'success') {
        setToast({ msg, type });
        setTimeout(() => setToast(null), 3000);
    }

    async function loadLeads() {
        try {
            const data = await api.getLeads('', campaign);
            setLeads(data);
        } catch (e) { console.error(e); }
        finally { setLoading(false); }
    }

    async function moveToStage(leadId, newStatus) {
        try {
            await api.updateLead(leadId, { status: newStatus }, campaign);
            setLeads(leads.map(l => l.id === leadId ? { ...l, status: newStatus } : l));
            showToast(`Lead moved to ${newStatus.replace('_', ' ')}`);
        } catch (e) { showToast(e.message, 'error'); }
    }

    async function deleteLead(id) {
        try {
            await api.deleteLead(id, campaign);
            setLeads(leads.filter(l => l.id !== id));
            showToast('Lead deleted');
        } catch (e) { showToast(e.message, 'error'); }
    }

    function getInitials(name) {
        return name?.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase() || '??';
    }

    function getLeadsByStage(stage) {
        return leads.filter(l => l.status === stage);
    }

    if (loading) {
        return <div className="loading-spinner"><div className="spinner" /><p>Loading pipeline...</p></div>;
    }

    return (
        <div>
            <div className="page-header">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <h2>🎯 Lead Pipeline</h2>
                        <p>{leads.length} leads in <strong>{campaign}</strong></p>
                    </div>
                    <div className="input-group" style={{ width: '200px', marginBottom: 0 }}>
                        <label style={{ fontSize: '0.7rem' }}>Switch Campaign</label>
                        <select
                            className="input-field"
                            value={campaign}
                            onChange={(e) => setCampaign(e.target.value)}
                            style={{ padding: '8px 12px' }}
                        >
                            {campaigns.map(c => <option key={c} value={c}>{c}</option>)}
                        </select>
                    </div>
                </div>
            </div>

            {/* Pipeline Board */}
            {leads.length === 0 ? (
                <div className="empty-state">
                    <div className="empty-icon">🎯</div>
                    <p>No leads yet. Search for companies and add decision makers as leads.</p>
                </div>
            ) : (
                <div className="pipeline-board">
                    {PIPELINE_STAGES.map((stage) => {
                        const stageLeads = getLeadsByStage(stage.key);
                        return (
                            <div key={stage.key} className="pipeline-column">
                                <div className="column-header">
                                    <h4 style={{ color: stage.color }}>
                                        {stage.icon} {stage.label}
                                    </h4>
                                    <div className="count">{stageLeads.length}</div>
                                </div>
                                {stageLeads.map((lead) => (
                                    <div key={lead.id} className="lead-card">
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                                            <div className="person-avatar" style={{ width: 32, height: 32, fontSize: '0.75rem' }}>
                                                {getInitials(lead.decision_maker?.name)}
                                            </div>
                                            <div>
                                                <div className="lead-name">{lead.decision_maker?.name}</div>
                                                <div className="lead-company">{lead.decision_maker?.company?.name}</div>
                                            </div>
                                        </div>
                                        <div className="lead-title">{lead.decision_maker?.title}</div>

                                        {/* Stage Selector */}
                                        <div style={{ marginTop: '10px' }}>
                                            <select
                                                className="input-field"
                                                style={{ padding: '6px 10px', fontSize: '0.78rem' }}
                                                value={lead.status}
                                                onChange={(e) => moveToStage(lead.id, e.target.value)}
                                            >
                                                {PIPELINE_STAGES.map(s => (
                                                    <option key={s.key} value={s.key}>{s.icon} {s.label}</option>
                                                ))}
                                            </select>
                                        </div>

                                        {/* Actions */}
                                        <div style={{ display: 'flex', gap: '4px', marginTop: '8px', flexWrap: 'wrap' }}>
                                            {lead.decision_maker?.linkedin_url && (
                                                <a href={lead.decision_maker.linkedin_url} target="_blank" rel="noopener noreferrer"
                                                    className="btn btn-sm btn-secondary" style={{ fontSize: '0.75rem', padding: '4px 10px', color: 'var(--text-primary)', textDecoration: 'none' }}>
                                                    🔗 Profile
                                                </a>
                                            )}
                                            <button className="btn btn-sm btn-danger" style={{ fontSize: '0.75rem', padding: '4px 10px' }}
                                                onClick={() => deleteLead(lead.id)}>
                                                🗑 Delete
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        );
                    })}
                </div>
            )}

            {toast && <div className={`toast ${toast.type}`}><span>{toast.type === 'success' ? '✅' : '❌'}</span><span>{toast.msg}</span></div>}
        </div>
    );
}
