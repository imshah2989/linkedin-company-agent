const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const config = {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  };

  if (config.body && typeof config.body === 'object') {
    config.body = JSON.stringify(config.body);
  }

  const resp = await fetch(url, config);
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(err.detail || `HTTP ${resp.status}`);
  }
  return resp.json();
}

export const api = {
  // Search
  searchCompanies: (filters) =>
    request('/api/search/companies', { method: 'POST', body: filters }),
  searchDecisionMakers: (companyId, roles) =>
    request(`/api/search/decision-makers/${companyId}`, { method: 'POST', body: roles || {} }),
  getSearchHistory: () =>
    request('/api/search/history'),

  // Companies
  getCompanies: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/api/companies${qs ? '?' + qs : ''}`);
  },
  getCompany: (id, campaign = 'Default') =>
    request(`/api/companies/${id}?campaign=${encodeURIComponent(campaign)}`),
  deleteCompany: (id, campaign = 'Default') =>
    request(`/api/companies/${id}?campaign=${encodeURIComponent(campaign)}`, { method: 'DELETE' }),

  // Leads
  getLeads: (status = '', campaign = 'Default') => {
    const qs = new URLSearchParams();
    if (status) qs.append('status', status);
    if (campaign) qs.append('campaign', campaign);
    const str = qs.toString();
    return request(`/api/leads${str ? '?' + str : ''}`);
  },
  createLead: (decisionMakerId, campaign = 'Default', notes = '') =>
    request('/api/leads', { method: 'POST', body: { decision_maker_id: decisionMakerId, campaign, notes } }),
  updateLead: (id, data, campaign = 'Default') =>
    request(`/api/leads/${id}?campaign=${encodeURIComponent(campaign)}`, { method: 'PATCH', body: data }),
  deleteLead: (id, campaign = 'Default') =>
    request(`/api/leads/${id}?campaign=${encodeURIComponent(campaign)}`, { method: 'DELETE' }),
  getLeadStats: (campaign = 'Default') =>
    request(`/api/leads/stats?campaign=${encodeURIComponent(campaign)}`),

  // Messages
  generateMessage: (leadId, campaign = 'Default', messageType = 'connection_request', senderContext = '') =>
    request('/api/messages/generate', {
      method: 'POST',
      body: { lead_id: leadId, campaign, message_type: messageType, sender_context: senderContext },
    }),
  getMessages: (leadId, campaign = 'Default') =>
    request(`/api/messages/${leadId}?campaign=${encodeURIComponent(campaign)}`),
  updateMessage: (id, data, campaign = 'Default') =>
    request(`/api/messages/${id}?campaign=${encodeURIComponent(campaign)}`, { method: 'PATCH', body: data }),
  getCampaigns: () =>
    request('/api/campaigns'),
};
