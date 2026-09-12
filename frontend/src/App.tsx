import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Dashboard from './pages/Dashboard';
import Alerts from './pages/Alerts';
import FieldReports from './pages/FieldReports';
import './index.css';

import { AuthProvider } from './AuthContext';
import Login from './pages/Login';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30000, retry: 2 },
  },
});

function App() {
  return (
    <AuthProvider>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/login" element={<Login />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/alerts" element={<Alerts />} />
            <Route path="/field-reports" element={<FieldReports />} />
          </Routes>
        </BrowserRouter>
      </QueryClientProvider>
    </AuthProvider>
  );
}

export default App;
