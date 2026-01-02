import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from './components/Layout/MainLayout';
import Dashboard from './pages/Dashboard';
import Servers from './pages/Servers';
import ServerBuilder from './pages/builders/ServerBuilder';
import ToolBuilder from './pages/builders/ToolBuilder';
import ConfigBuilder from './pages/builders/ConfigBuilder';

function App() {
  return (
    <Router>
      <MainLayout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/servers" element={<Servers />} />
          <Route path="/builder/server" element={<ServerBuilder />} />
          <Route path="/builder/tool" element={<ToolBuilder />} />
          <Route path="/builder/config" element={<ConfigBuilder />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </MainLayout>
    </Router>
  );
}

export default App;
