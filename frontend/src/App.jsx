import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Search from './pages/Search';
import Companies from './pages/Companies';
import Leads from './pages/Leads';
import { CampaignProvider } from './context/CampaignContext';

export default function App() {
  return (
    <CampaignProvider>
      <BrowserRouter>
        <div className="app-layout">
          <Sidebar />
          <main className="main-content">
            <Routes>
              <Route path="/" element={<Navigate to="/search" replace />} />
              <Route path="/search" element={<Search />} />
              <Route path="/companies" element={<Companies />} />
              <Route path="/leads" element={<Leads />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </CampaignProvider>
  );
}
