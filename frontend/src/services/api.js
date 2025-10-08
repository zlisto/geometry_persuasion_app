import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

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
  try {
    const response = await api.post('/chat', {
      messages: messages.map(msg => ({
        role: msg.role,
        content: msg.content
      })),
      manifold_data: manifoldData
    });
    return response.data;
  } catch (error) {
    console.error('Error sending chat message:', error);
    throw new Error(error.response?.data?.detail || 'Failed to send message');
  }
};

export const computeConversationPoint = async (messages, manifoldData, role) => {
  try {
    const response = await api.post('/compute-conversation-point', {
      messages: messages.map(msg => ({
        role: msg.role,
        content: msg.content
      })),
      manifold_data: manifoldData,
      role: role
    });
    return response.data;
  } catch (error) {
    console.error('Error computing conversation point:', error);
    throw new Error(error.response?.data?.detail || 'Failed to compute conversation point');
  }
};
