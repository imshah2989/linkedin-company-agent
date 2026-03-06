import { useState } from 'react';
import { api } from '../api';
import { useCampaign } from '../context/CampaignContext';

export default function Search() {
    const { campaign } = useCampaign();
    const [filters, setFilters] = useState({
        industry: '',
        location: '',
        company_size: '',
        keywords: '',
        max_results: 10,
    });
    const [results, setResults] = useState([]);
    const [searching, setSearching] = useState(false);
    const [error, setError] = useState('');
    const [selectedCompany, setSelectedCompany] = useState(null);
    const [decisionMakers, setDecisionMakers] = useState([]);
    const [findingDMs, setFindingDMs] = useState(false);
    const [toast, setToast] = useState(null);

    function showToast(msg, type = 'success') {
        setToast({ msg, type });
        setTimeout(() => setToast(null), 3000);
    }

    async function handleSearch(e) {
        e.preventDefault();
        setSearching(true);
        setError('');
        setResults([]);
        try {
            const data = await api.searchCompanies({ ...filters, campaign });
            setResults(data.companies || []);
            if (data.companies?.length === 0) setError('No companies found. Try broader search terms.');
        } catch (e) {
            setError(e.message);
        } finally {
            setSearching(false);
        }
    }

    async function findDecisionMakers(company) {
        setSelectedCompany(company);
        setFindingDMs(true);
        setDecisionMakers([]);
        try {
            const data = await api.searchDecisionMakers(company.id, { campaign });
            setDecisionMakers(data.decision_makers || []);
        } catch (e) {
            showToast(e.message, 'error');
        } finally {
            setFindingDMs(false);
        }
    }

    async function addAsLead(dm) {
        try {
            await api.createLead(dm.id, campaign);
            showToast(`${dm.name} added as lead!`);
        } catch (e) {
            showToast(e.message, 'error');
        }
    }

    function getInitials(name) {
        return name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();
    }

    return (
        <div>
            <div className="page-header">
                <h2>🔍 Search Companies</h2>
                <p>Use Google X-ray search to discover companies on LinkedIn</p>
            </div>

            {/* Search Form */}
            <form onSubmit={handleSearch} className="glass-card no-hover" style={{ marginBottom: '24px' }}>
                <div className="search-form">
                    <div className="input-group">
                        <label>Industry</label>
                        <input
                            className="input-field"
                            placeholder="e.g., AI, SaaS, Fintech"
                            value={filters.industry}
                            onChange={(e) => setFilters({ ...filters, industry: e.target.value })}
                        />
                    </div>
                    <div className="input-group">
                        <label>Location</label>
                        <input
                            className="input-field"
                            placeholder="e.g., San Francisco, USA"
                            value={filters.location}
                            onChange={(e) => setFilters({ ...filters, location: e.target.value })}
                        />
                    </div>
                    <div className="input-group">
                        <label>Company Size</label>
                        <select
                            className="input-field"
                            value={filters.company_size}
                            onChange={(e) => setFilters({ ...filters, company_size: e.target.value })}
                        >
                            <option value="">Any size</option>
                            <option value="1-10 employees">1–10 (Micro)</option>
                            <option value="11-50 employees">11–50 (Small)</option>
                            <option value="51-200 employees">51–200 (Medium)</option>
                            <option value="201-500 employees">201–500 (Large)</option>
                            <option value="501-1000 employees">501–1000 (Enterprise)</option>
                        </select>
                    </div>
                    <div className="input-group">
                        <label>Keywords</label>
                        <input
                            className="input-field"
                            placeholder="e.g., hiring, AI automation"
                            value={filters.keywords}
                            onChange={(e) => setFilters({ ...filters, keywords: e.target.value })}
                        />
                    </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginTop: '16px' }}>
                    <div className="input-group" style={{ width: '120px' }}>
                        <label>Max Results</label>
                        <select
                            className="input-field"
                            value={filters.max_results}
                            onChange={(e) => setFilters({ ...filters, max_results: Number(e.target.value) })}
                        >
                            <option value={10}>10</option>
                            <option value={20}>20</option>
                            <option value={30}>30</option>
                        </select>
                    </div>
                    <button type="submit" className="btn btn-primary btn-lg" disabled={searching} style={{ marginTop: 'auto' }}>
                        {searching ? (
                            <><div className="spinner" style={{ width: 18, height: 18, borderWidth: 2 }} /> Searching...</>
                        ) : '🔍 Search LinkedIn'}
                    </button>
                </div>
            </form>

            {error && (
                <div className="glass-card no-hover" style={{ borderColor: 'rgba(239,68,68,0.3)', marginBottom: '24px' }}>
                    <p style={{ color: '#ef4444' }}>⚠️ {error}</p>
                </div>
            )}

            {/* Results Grid */}
            {results.length > 0 && (
                <>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                        <h3 style={{ fontSize: '1.1rem' }}>Found {results.length} companies</h3>
                    </div>
                    <div className="company-grid">
                        {results.map((c, i) => (
                            <div key={c.id || i} className="company-card animate-in" onClick={() => findDecisionMakers(c)}>
                                <div className="card-header">
                                    <div className="company-avatar">{getInitials(c.name)}</div>
                                    <div className="company-info">
                                        <h3>{c.name}</h3>
                                        {c.industry && <div className="industry-tag">{c.industry}</div>}
                                    </div>
                                </div>
                                <div className="card-description">{c.description || 'No description available'}</div>
                                <div className="card-meta">
                                    {c.location && <span>📍 {c.location}</span>}
                                    {c.employee_count && <span>👥 {c.employee_count}</span>}
                                </div>
                                <div style={{ marginTop: '12px', display: 'flex', gap: '8px' }}>
                                    <a
                                        href={c.linkedin_url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="btn btn-sm btn-secondary"
                                        onClick={(e) => e.stopPropagation()}
                                    >
                                        🔗 LinkedIn
                                    </a>
                                    <button className="btn btn-sm btn-primary" onClick={(e) => { e.stopPropagation(); findDecisionMakers(c); }}>
                                        👤 Find Decision Makers
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                </>
            )}

            {/* Decision Makers Modal */}
            {selectedCompany && (
                <div className="modal-overlay" onClick={() => setSelectedCompany(null)}>
                    <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3>👤 Decision Makers at {selectedCompany.name}</h3>
                            <button className="btn btn-icon btn-secondary" onClick={() => setSelectedCompany(null)}>✕</button>
                        </div>
                        {findingDMs ? (
                            <div className="loading-spinner">
                                <div className="spinner" />
                                <p>Searching for decision makers...</p>
                            </div>
                        ) : decisionMakers.length === 0 ? (
                            <div className="empty-state">
                                <div className="empty-icon">🔍</div>
                                <p>No decision makers found. Try searching with different company keywords.</p>
                            </div>
                        ) : (
                            <div className="person-grid">
                                {decisionMakers.map((dm) => (
                                    <div key={dm.id} className="person-card">
                                        <div className="person-top">
                                            <div className="person-avatar">{getInitials(dm.name)}</div>
                                            <div className="person-info">
                                                <h4>{dm.name}</h4>
                                                <div className="person-title">{dm.title || 'Unknown Title'}</div>
                                            </div>
                                        </div>
                                        {dm.location && (
                                            <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: '8px' }}>
                                                📍 {dm.location}
                                            </div>
                                        )}
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

            {/* Toast */}
            {toast && (
                <div className={`toast ${toast.type}`}>
                    <span>{toast.type === 'success' ? '✅' : '❌'}</span>
                    <span>{toast.msg}</span>
                </div>
            )}
        </div>
    );
}
