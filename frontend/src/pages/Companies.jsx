import { useState, useEffect } from 'react';
import { api } from '../api';
import { useCampaign } from '../context/CampaignContext';

export default function Companies() {
    const { campaign } = useCampaign();
    const [companies, setCompanies] = useState([]);
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(1);
    const [search, setSearch] = useState('');
    const [loading, setLoading] = useState(true);
    const [selected, setSelected] = useState(null);
    const [decisionMakers, setDecisionMakers] = useState([]);
    const [findingDMs, setFindingDMs] = useState(false);
    const [toast, setToast] = useState(null);

    useEffect(() => { loadCompanies(); }, [page, search, campaign]);

    function showToast(msg, type = 'success') {
        setToast({ msg, type });
        setTimeout(() => setToast(null), 3000);
    }

    async function loadCompanies() {
        setLoading(true);
        try {
            const data = await api.getCompanies({ page, limit: 20, search, campaign });
            setCompanies(data.companies || []);
            setTotal(data.total || 0);
        } catch (e) { console.error(e); }
        finally { setLoading(false); }
    }

    async function viewCompany(company) {
        setSelected(company);
        setFindingDMs(true);
        try {
            const data = await api.getCompany(company.id, campaign);
            setDecisionMakers(data.decision_makers || []);
        } catch (e) { showToast(e.message, 'error'); }
        finally { setFindingDMs(false); }
    }

    async function deleteCompany(id) {
        try {
            await api.deleteCompany(id, campaign);
            showToast('Company deleted');
            loadCompanies();
            setSelected(null);
        } catch (e) { showToast(e.message, 'error'); }
    }

    async function addAsLead(dm) {
        try {
            await api.createLead(dm.id, campaign);
            showToast(`${dm.name} added as lead!`);
        } catch (e) { showToast(e.message, 'error'); }
    }

    async function findMore() {
        if (!selected) return;
        setFindingDMs(true);
        try {
            const data = await api.searchDecisionMakers(selected.id, { campaign });
            setDecisionMakers(data.decision_makers || []);
            showToast(`Found ${data.count} decision makers`);
        } catch (e) { showToast(e.message, 'error'); }
        finally { setFindingDMs(false); }
    }

    function getInitials(name) {
        return name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();
    }

    const totalPages = Math.ceil(total / 20);

    return (
        <div>
            <div className="page-header">
                <h2>🏢 Companies</h2>
                <p>{total} companies discovered</p>
            </div>

            {/* Search Bar */}
            <div className="glass-card no-hover" style={{ marginBottom: '24px', padding: '16px' }}>
                <input
                    className="input-field"
                    placeholder="🔍 Search companies by name or description..."
                    value={search}
                    onChange={(e) => { setSearch(e.target.value); setPage(1); }}
                />
            </div>

            {loading ? (
                <div className="loading-spinner"><div className="spinner" /><p>Loading companies...</p></div>
            ) : companies.length === 0 ? (
                <div className="empty-state">
                    <div className="empty-icon">🏢</div>
                    <p>No companies found. Go to Search to discover companies on LinkedIn.</p>
                </div>
            ) : (
                <>
                    <div className="company-grid">
                        {companies.map((c, i) => (
                            <div key={c.id} className="company-card animate-in" onClick={() => viewCompany(c)}>
                                <div className="card-header">
                                    <div className="company-avatar">{getInitials(c.name)}</div>
                                    <div className="company-info">
                                        <h3>{c.name}</h3>
                                        {c.industry && <div className="industry-tag">{c.industry}</div>}
                                    </div>
                                </div>
                                <div className="card-description">{c.description || 'No description'}</div>
                                <div className="card-meta">
                                    {c.location && <span>📍 {c.location}</span>}
                                    {c.employee_count && <span>👥 {c.employee_count}</span>}
                                    <span>👤 {c.decision_makers_count || 0} DMs</span>
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* Pagination */}
                    {totalPages > 1 && (
                        <div style={{ display: 'flex', justifyContent: 'center', gap: '8px', marginTop: '24px' }}>
                            <button className="btn btn-secondary btn-sm" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>← Prev</button>
                            <span style={{ padding: '6px 12px', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                                Page {page} of {totalPages}
                            </span>
                            <button className="btn btn-secondary btn-sm" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>Next →</button>
                        </div>
                    )}
                </>
            )}

            {/* Company Detail Modal */}
            {selected && (
                <div className="modal-overlay" onClick={() => setSelected(null)}>
                    <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                <div className="company-avatar" style={{ width: 40, height: 40, fontSize: '1rem' }}>{getInitials(selected.name)}</div>
                                <div>
                                    <h3>{selected.name}</h3>
                                    {selected.industry && <span style={{ fontSize: '0.85rem', color: 'var(--text-accent)' }}>{selected.industry}</span>}
                                </div>
                            </div>
                            <button className="btn btn-icon btn-secondary" onClick={() => setSelected(null)}>✕</button>
                        </div>

                        <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem', marginBottom: '16px' }}>{selected.description}</p>

                        <div style={{ display: 'flex', gap: '16px', marginBottom: '20px', flexWrap: 'wrap' }}>
                            {selected.location && <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>📍 {selected.location}</span>}
                            {selected.employee_count && <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>👥 {selected.employee_count}</span>}
                            {selected.linkedin_url && (
                                <a href={selected.linkedin_url} target="_blank" rel="noopener noreferrer" style={{ fontSize: '0.85rem' }}>🔗 LinkedIn Page</a>
                            )}
                        </div>

                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
                            <h4>👤 Decision Makers ({decisionMakers.length})</h4>
                            <div style={{ display: 'flex', gap: '8px' }}>
                                <button className="btn btn-sm btn-primary" onClick={findMore}>🔍 Find More</button>
                                <button className="btn btn-sm btn-danger" onClick={() => deleteCompany(selected.id)}>🗑 Delete</button>
                            </div>
                        </div>

                        {findingDMs ? (
                            <div className="loading-spinner"><div className="spinner" /><p>Searching...</p></div>
                        ) : decisionMakers.length === 0 ? (
                            <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '20px' }}>
                                No decision makers found yet. Click "Find More" to search.
                            </p>
                        ) : (
                            <div className="person-grid">
                                {decisionMakers.map((dm) => (
                                    <div key={dm.id} className="person-card">
                                        <div className="person-top">
                                            <div className="person-avatar">{getInitials(dm.name)}</div>
                                            <div className="person-info">
                                                <h4>{dm.name}</h4>
                                                <div className="person-title">{dm.title || 'Unknown'}</div>
                                            </div>
                                        </div>
                                        <div className="person-actions">
                                            <a href={dm.linkedin_url} target="_blank" rel="noopener noreferrer" className="btn btn-sm btn-secondary">🔗 Profile</a>
                                            <button className="btn btn-sm btn-primary" onClick={() => addAsLead(dm)}>🎯 Add Lead</button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            )}

            {toast && <div className={`toast ${toast.type}`}><span>{toast.type === 'success' ? '✅' : '❌'}</span><span>{toast.msg}</span></div>}
        </div>
    );
}
