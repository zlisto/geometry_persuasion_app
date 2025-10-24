import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';

console.log('🔍 DEBUG: API Configuration:', {
  API_BASE_URL: API_BASE_URL,
  NODE_ENV: process.env.NODE_ENV,
  REACT_APP_API_URL: process.env.REACT_APP_API_URL
});

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for debugging
api.interceptors.request.use(
  (config) => {
    console.log('🔍 DEBUG: API Request:', {
      method: config.method,
      url: config.url,
      baseURL: config.baseURL,
      fullURL: `${config.baseURL}${config.url}`,
      data: config.data ? Object.keys(config.data) : 'no data'
    });
    return config;
  },
  (error) => {
    console.error('❌ ERROR: API Request Error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor for debugging
api.interceptors.response.use(
  (response) => {
    console.log('🔍 DEBUG: API Response:', {
      status: response.status,
      url: response.config.url,
      hasData: !!response.data,
      dataKeys: response.data ? Object.keys(response.data) : 'no data'
    });
    return response;
  },
  (error) => {
    console.error('❌ ERROR: API Response Error:', {
      status: error.response?.status,
      url: error.config?.url,
      message: error.message,
      data: error.response?.data
    });
    return Promise.reject(error);
  }
);

export const computeManifold = async (topic, systemTail) => {
  try {
    const response = await api.post('/compute-manifold', {
      topic,
      system_tail: systemTail
    });
    return response.data;
  } catch (error) {
    console.error('Error computing manifold:', error);
    throw new Error(error.response?.data?.detail || 'Failed to compute manifold');
  }
};

export const sendChatMessage = async (messages, manifoldData) => {
  console.log('🔍 DEBUG: sendChatMessage called with:', {
    messageCount: messages.length,
    hasManifoldData: !!manifoldData,
    manifoldDataKeys: manifoldData ? Object.keys(manifoldData) : 'none'
  });
  
  try {
    const requestData = {
      messages: messages.map(msg => ({
        role: msg.role,
        content: msg.content
      })),
      manifold_data: manifoldData
    };
    
    console.log('🔍 DEBUG: Sending request to /chat:', {
      messageCount: requestData.messages.length,
      hasManifoldData: !!requestData.manifold_data
    });
    
    const response = await api.post('/chat', requestData);
    
    console.log('🔍 DEBUG: Chat response received:', {
      status: response.status,
      hasData: !!response.data,
      hasResponse: !!response.data?.response,
      hasConversationPoint: !!response.data?.conversation_point,
      conversationPoint: response.data?.conversation_point
    });
    
    return response.data;
  } catch (error) {
    console.error('❌ ERROR: Error sending chat message:', error);
    console.error('❌ ERROR: Error details:', error.response?.data);
    console.error('❌ ERROR: Error status:', error.response?.status);
    throw new Error(error.response?.data?.detail || 'Failed to send message');
  }
};

