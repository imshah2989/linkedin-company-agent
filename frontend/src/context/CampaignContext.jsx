import { createContext, useContext, useState, useEffect } from 'react';

const CampaignContext = createContext();

export function CampaignProvider({ children }) {
    const [campaign, setCampaign] = useState(() => {
        return localStorage.getItem('activeCampaign') || 'Default';
    });

    useEffect(() => {
        localStorage.setItem('activeCampaign', campaign);
    }, [campaign]);

    return (
        <CampaignContext.Provider value={{ campaign, setCampaign }}>
            {children}
        </CampaignContext.Provider>
    );
}

export function useCampaign() {
    return useContext(CampaignContext);
}
