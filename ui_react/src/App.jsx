import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import ChatInterface from './components/ChatInterface';
import DocumentUpload from './components/DocumentUpload';
import EvaluationPanel from './components/EvaluationPanel';
import { checkStatus } from './api';

function App() {
  const [currentView, setCurrentView] = useState('chat'); // 'chat', 'upload', 'evaluate'
  const [config, setConfig] = useState({
    apiKey: '',
    ragMethod: 'Hybrid RAG',
    topK: 5,
    temperature: 0.7,
    apiKeyConfigured: false
  });

  const [status, setStatus] = useState('initializing');

  useEffect(() => {
    const initSystem = async () => {
      try {
        const statusData = await checkStatus();
        setStatus(statusData.status);
        if (statusData.api_key_configured) {
          setConfig(prev => ({ ...prev, apiKeyConfigured: true }));
        }
      } catch (error) {
        setStatus('error');
      }
    };

    initSystem();
    const interval = setInterval(initSystem, 30000); // Check status every 30s
    return () => clearInterval(interval);
  }, []);

  const renderContent = () => {
    switch (currentView) {
      case 'upload':
        return <DocumentUpload />;
      case 'evaluate':
        return <EvaluationPanel />;
      default:
        return <ChatInterface config={config} />;
    }
  };

  return (
    <div className="flex h-screen bg-white">
      <Sidebar
        config={config}
        setConfig={setConfig}
        status={status}
        currentView={currentView}
        setCurrentView={setCurrentView}
      />
      {renderContent()}
    </div>
  );
}

export default App;
