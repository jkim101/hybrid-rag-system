import React, { createContext, useState, useContext, useEffect } from 'react';

const ConfigContext = createContext();

export const useConfig = () => useContext(ConfigContext);

export const ConfigProvider = ({ children }) => {
    const [config, setConfig] = useState({
        apiKey: '', // In a real app, might not store this in client state directly if using backend proxy
        ragMethod: 'Hybrid RAG',
        topK: 5,
        temperature: 0.7,
        chunkSize: 1000,
        chunkOverlap: 200,
        vectorWeight: 0.5,
        vectorWeight: 0.5,
        graphWeight: 0.5,
        lightragMode: 'hybrid', // local, global, hybrid, mix, naive
        lightragTopK: 60
    });

    // Load from localStorage on mount
    useEffect(() => {
        const savedConfig = localStorage.getItem('rag_config');
        if (savedConfig) {
            setConfig(JSON.parse(savedConfig));
        }
    }, []);

    // Save to localStorage on change
    useEffect(() => {
        localStorage.setItem('rag_config', JSON.stringify(config));
    }, [config]);

    const updateConfig = (newConfig) => {
        setConfig(prev => ({ ...prev, ...newConfig }));
    };

    return (
        <ConfigContext.Provider value={{ config, updateConfig }}>
            {children}
        </ConfigContext.Provider>
    );
};
