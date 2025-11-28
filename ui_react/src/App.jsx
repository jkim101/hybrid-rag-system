import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider } from './contexts/ConfigContext';
import Layout from './components/Layout';
import Dashboard from './components/Dashboard';
import Playground from './components/Playground';
import EvaluationStudio from './components/EvaluationStudio';
import DataManager from './components/DataManager';
import GraphExplorer from './components/GraphExplorer';
import Settings from './components/Settings';
import './App.css';

function App() {
  return (
    <ConfigProvider>
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/playground" element={<Playground />} />
            <Route path="/evaluation" element={<EvaluationStudio />} />
            <Route path="/data" element={<DataManager />} />
            <Route path="/graph" element={<GraphExplorer />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Layout>
      </Router>
    </ConfigProvider>
  );
}

export default App;
