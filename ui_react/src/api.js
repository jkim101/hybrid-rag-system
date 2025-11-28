import axios from 'axios';

const api = axios.create({
    baseURL: '/', // Proxy handles the forwarding to localhost:8000
    headers: {
        'Content-Type': 'application/json',
    },
});

export const checkStatus = async () => {
    try {
        const response = await api.get('/status');
        return response.data;
    } catch (error) {
        console.error('Status check failed:', error);
        throw error;
    }
};

export const sendQuery = async (query, config = {}) => {
    try {
        const response = await api.post('/query', {
            query,
            top_k: config.topK || 5,
            rag_method: config.ragMethod || "Hybrid RAG",
            temperature: config.temperature || 0.7,
            lightrag_mode: config.lightragMode || 'hybrid',
            lightrag_top_k: config.lightragTopK || 60
        });
        return response.data;
    } catch (error) {
        console.error('Query failed:', error);
        throw error;
    }
};

export const uploadFiles = async (files, clearExisting = false) => {
    const formData = new FormData();
    Array.from(files).forEach(file => {
        formData.append('files', file);
    });

    try {
        const response = await api.post(`/upload?clear_existing=${clearExisting}`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    } catch (error) {
        console.error('Upload failed:', error);
        throw error;
    }
};

export const evaluateCommunication = async (docPaths, persona, aggregate, evaluationFile = null, compareMethods = false) => {
    try {
        const formData = new FormData();
        formData.append('document_paths', JSON.stringify(docPaths));
        formData.append('student_persona', persona);
        formData.append('aggregate', aggregate);
        formData.append('compare_methods', compareMethods);

        if (evaluationFile) {
            formData.append('evaluation_file', evaluationFile);
        }

        const response = await api.post('/evaluate', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    } catch (error) {
        console.error('Evaluation failed:', error);
        throw error;
    }
};

export const getDocuments = async () => {
    try {
        const response = await api.get('/documents');
        return response.data;
    } catch (error) {
        console.error('Failed to fetch documents:', error);
        throw error;
    }
};

export const analyzeEvaluation = async (query, evaluationResults) => {
    try {
        const response = await api.post('/analyze_evaluation', {
            query,
            evaluation_results: evaluationResults
        });
        return response.data;
    } catch (error) {
        console.error('Analysis failed:', error);
        throw error;
    }
};

export default api;
