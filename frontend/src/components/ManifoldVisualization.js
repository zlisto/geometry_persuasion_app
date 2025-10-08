import React from 'react';
import Plot from 'react-plotly.js';

const ManifoldVisualization = ({ manifoldData, conversationPoints, messages }) => {
  console.log('🔍 DEBUG: ManifoldVisualization render:', {
    hasManifoldData: !!manifoldData,
    conversationPointsCount: conversationPoints?.length || 0,
    conversationPoints: conversationPoints,
    messagesCount: messages?.length || 0
  });
  
  if (!manifoldData) {
    // Show simple conversation plot when no manifold data
    const turns = messages.filter(m => m.role === 'user' || m.role === 'assistant');
    const n = Math.max(turns.length, 1);
    const xVals = Array.from({ length: n }, (_, i) => i + 1);
    const yVals = xVals.slice();
    const roles = turns.map(m => m.role);
    const texts = turns.map(m => m.content);
    
    const data = [{
      x: xVals,
      y: yVals,
      mode: 'lines+markers',
      line: { width: 3, color: '#ff69b4' },
      marker: { size: 10, color: '#ff69b4' },
      name: 'Messages',
      customdata: roles.map((role, i) => [role, texts[i]]),
      hovertemplate: 'Message %{x}<br>%{customdata[0] === "user" ? "Client" : customdata[0] === "assistant" ? "Agent" : customdata[0]}: %{customdata[1]}<extra></extra>'
    }];

    const layout = {
      title: { text: 'Conversation — Messages by Index', font: { size: 28, color: 'black' } },
      xaxis: { 
        title: { text: 'Message index', font: { size: 22, color: 'black' } },
        showgrid: true,
        gridcolor: 'rgba(0,0,0,0.1)',
        zerolinecolor: 'black'
      },
      yaxis: { 
        title: { text: 'Message index', font: { size: 22, color: 'black' } },
        showgrid: true,
        gridcolor: 'rgba(0,0,0,0.1)',
        zerolinecolor: 'black'
      },
      template: 'plotly_white',
      paper_bgcolor: 'white',
      plot_bgcolor: 'white',
      font: { size: 20, color: 'black' },
      margin: { l: 40, r: 20, t: 60, b: 40 },
      height: 600
    };

    return (
      <div className="manifold-container">
        <Plot data={data} layout={layout} useResizeHandler={true} style={{ width: '100%' }} />
        <div className="manifold-info">
          Click 'Compute Topic Manifold' to visualize the topic's persuasion space.
        </div>
      </div>
    );
  }

  // Create manifold plot with conversation points
  const data = [];

  // Add the manifold line
  data.push({
    x: [manifoldData.x0, manifoldData.x1],
    y: [manifoldData.y0, manifoldData.y1],
    mode: 'lines',
    line: { width: 3, color: 'purple', dash: 'dash' },
    name: 'Manifold Line',
    showlegend: false
  });

  // Add v0 point (blue)
  data.push({
    x: [manifoldData.x0],
    y: [manifoldData.y0],
    mode: 'markers',
    marker: { size: 15, color: 'blue', symbol: 'x' },
    name: '1/100 Sentiment',
    hovertemplate: '1/100 Sentiment: (%{x:.2f}, %{y:.2f})<extra></extra>',
    showlegend: false
  });

  // Add v1 point (red)
  data.push({
    x: [manifoldData.x1],
    y: [manifoldData.y1],
    mode: 'markers',
    marker: { size: 15, color: 'red', symbol: 'x' },
    name: '100/100 Sentiment',
    hovertemplate: '100/100 Sentiment: (%{x:.2f}, %{y:.2f})<extra></extra>',
    showlegend: false
  });

  // Add conversation points
  if (conversationPoints && conversationPoints.length > 0) {
    console.log('🔍 DEBUG: Processing conversation points:', conversationPoints);
    
    // Separate user and assistant points, filtering out placeholder points (x=0, y=0)
    const userPoints = conversationPoints.filter(point => point.role === 'user' && (point.x !== 0 || point.y !== 0));
    const assistantPoints = conversationPoints.filter(point => point.role === 'assistant' && (point.x !== 0 || point.y !== 0));
    
    console.log('🔍 DEBUG: Separated points:', {
      userPoints: userPoints.length,
      assistantPoints: assistantPoints.length,
      userPointsData: userPoints,
      assistantPointsData: assistantPoints
    });

    // Add user points (only real coordinates)
    if (userPoints.length > 0) {
        console.log('🔍 DEBUG: Adding user points to plot data');
        data.push({
          x: userPoints.map(point => point.x),
          y: userPoints.map(point => point.y),
          mode: 'lines+markers+text',
          line: { width: 2, color: 'skyblue', dash: 'solid' },
          marker: { size: 20, color: 'green', symbol: 'circle' },
          text: userPoints.map(point => point.message_index.toString()),
          textposition: 'middle center',
          textfont: { color: '#000000', size: 14, family: 'Arial, sans-serif' },
          name: 'Client Messages',
          customdata: userPoints.map(point => point.message_index),
          hovertemplate: 'Message %{customdata}: Client<br>(%{x:.2f}, %{y:.2f})<extra></extra>',
          showlegend: false
        });
    } else {
      console.log('🔍 DEBUG: No user points to add');
    }

    // Add assistant points (only real coordinates)
    if (assistantPoints.length > 0) {
      console.log('🔍 DEBUG: Adding assistant points to plot data');
      data.push({
        x: assistantPoints.map(point => point.x),
        y: assistantPoints.map(point => point.y),
        mode: 'lines+markers+text',
        line: { width: 2, color: 'orange', dash: 'solid' },
          marker: { size: 20, color: 'darkorange', symbol: 'square' },
        text: assistantPoints.map(point => point.message_index.toString()),
        textposition: 'middle center',
        textfont: { color: '#000000', size: 14, family: 'Arial, sans-serif' },
        name: 'Agent Messages',
        customdata: assistantPoints.map(point => point.message_index),
          hovertemplate: 'Message %{customdata}: Agent<br>(%{x:.2f}, %{y:.2f})<extra></extra>',
        showlegend: false
      });
    } else {
      console.log('🔍 DEBUG: No assistant points to add');
    }
  } else {
    console.log('🔍 DEBUG: No conversation points to process');
  }

  const layout = {
    title: { text: 'Topic Manifold', font: { size: 28, color: 'black' } },
    xaxis: { 
      title: { text: 'Sentiment', font: { size: 22, color: 'black' } },
      range: [-1.1, 1.1],
      showgrid: true,
      gridcolor: 'rgba(0,0,0,0.1)',
      zerolinecolor: 'black'
    },
    yaxis: { 
      title: { text: 'Relevance', font: { size: 22, color: 'black' } },
      range: [0, 1.1],
      showgrid: true,
      gridcolor: 'rgba(0,0,0,0.1)',
      zerolinecolor: 'black'
    },
    template: 'plotly_white',
    paper_bgcolor: 'white',
    plot_bgcolor: 'white',
    font: { size: 20, color: 'black' },
    margin: { l: 40, r: 20, t: 60, b: 40 },
    height: 600,
    showlegend: false,
    autosize: true
  };

  return (
    <div className="manifold-container">
      <Plot data={data} layout={layout} useResizeHandler={true} style={{ width: '100%', height: '100%' }} />
    </div>
  );
};

export default ManifoldVisualization;
