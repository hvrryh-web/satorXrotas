/**
 * SATOR Developer Dashboard - Frontend JavaScript
 * Handles real-time updates, layer navigation, and component interactions.
 */

// Global state
let currentLayer = null;
let refreshInterval = null;
let layersData = [];
let summaryData = null;

// Status colors for CSS classes
const statusColors = {
    healthy: '#22c55e',
    degraded: '#f59e0b',
    critical: '#ef4444',
    unknown: '#64748b',
    maintenance: '#3b82f6'
};

// Initialize dashboard
async function init() {
    await loadLayers();
    await loadSummary();
    
    // Auto-refresh every 30 seconds
    refreshInterval = setInterval(() => {
        loadSummary();
        if (currentLayer) {
            loadLayerContent(currentLayer);
        }
    }, 30000);
    
    // Setup keyboard shortcuts
    document.addEventListener('keydown', handleKeyboard);
}

// Load layers from API
async function loadLayers() {
    try {
        const response = await fetch('/api/layers');
        if (!response.ok) throw new Error('Failed to fetch layers');
        
        layersData = await response.json();
        
        const nav = document.getElementById('layer-nav');
        nav.innerHTML = layersData.map(layer => `
            <li class="layer-item ${layer.id === currentLayer ? 'active' : ''}" 
                data-layer-id="${layer.id}"
                onclick="selectLayer('${layer.id}')">
                <span class="layer-icon">${layer.icon}</span>
                <span class="layer-name">${layer.name}</span>
                <span class="layer-count">${layer.component_count}</span>
            </li>
        `).join('');
        
        // Select first layer by default
        if (!currentLayer && layersData.length > 0) {
            const firstWithComponents = layersData.find(l => l.component_count > 0);
            if (firstWithComponents) {
                selectLayer(firstWithComponents.id);
            } else {
                selectLayer(layersData[0].id);
            }
        }
    } catch (e) {
        console.error('Failed to load layers:', e);
        showError('Failed to load system layers. Please refresh.');
    }
}

// Load dashboard summary
async function loadSummary() {
    try {
        const response = await fetch('/api/summary');
        if (!response.ok) throw new Error('Failed to fetch summary');
        
        summaryData = await response.json();
        
        // Update header status
        const statusBadge = document.getElementById('overall-status');
        if (statusBadge) {
            statusBadge.textContent = summaryData.overall_status;
            statusBadge.className = `status-badge status-${summaryData.overall_status}`;
        }
        
        // Update timestamp
        const lastUpdated = document.getElementById('last-updated');
        if (lastUpdated) {
            const timestamp = new Date(summaryData.timestamp);
            lastUpdated.textContent = 'Updated: ' + timestamp.toLocaleTimeString();
        }
        
        // Update layer indicators in sidebar
        updateLayerIndicators(summaryData.layer_status);
        
    } catch (e) {
        console.error('Failed to load summary:', e);
    }
}

// Update layer status indicators in sidebar
function updateLayerIndicators(layerStatus) {
    if (!layerStatus) return;
    
    document.querySelectorAll('.layer-item[data-layer-id]').forEach(item => {
        const layerId = item.dataset.layerId;
        const status = layerStatus[layerId];
        
        // Remove old status indicators
        const oldIndicator = item.querySelector('.layer-status-indicator');
        if (oldIndicator) oldIndicator.remove();
        
        // Add status indicator if not healthy
        if (status && status !== 'healthy') {
            const indicator = document.createElement('span');
            indicator.className = 'layer-status-indicator';
            indicator.style.cssText = `
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: ${statusColors[status] || statusColors.unknown};
                margin-left: 0.5rem;
            `;
            item.appendChild(indicator);
        }
    });
}

// Select a layer
async function selectLayer(layerId) {
    currentLayer = layerId;
    
    // Update active state in sidebar
    document.querySelectorAll('.layer-item[data-layer-id]').forEach(item => {
        item.classList.toggle('active', item.dataset.layerId === layerId);
    });
    
    // Load layer content
    await loadLayerContent(layerId);
}

// Load components for a layer
async function loadLayerContent(layerId) {
    const content = document.getElementById('content');
    content.innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
            <p>Loading components...</p>
        </div>
    `;
    
    try {
        const response = await fetch(`/api/layers/${layerId}/components`);
        if (!response.ok) throw new Error('Failed to fetch components');
        
        const components = await response.json();
        renderComponents(components, layerId);
    } catch (e) {
        console.error('Failed to load layer content:', e);
        content.innerHTML = `
            <div style="text-align: center; padding: 4rem; color: #ef4444;">
                <p>Error loading components: ${e.message}</p>
                <button onclick="loadLayerContent('${layerId}')" 
                        style="margin-top: 1rem; padding: 0.5rem 1rem; 
                               background: #3b82f6; color: white; border: none; 
                               border-radius: 4px; cursor: pointer;">
                    Retry
                </button>
            </div>
        `;
    }
}

// Render components grid
function renderComponents(components, layerId) {
    const content = document.getElementById('content');
    
    // Calculate stats
    const healthy = components.filter(c => c.status === 'healthy').length;
    const degraded = components.filter(c => c.status === 'degraded').length;
    const critical = components.filter(c => c.status === 'critical').length;
    const unknown = components.filter(c => c.status === 'unknown').length;
    
    const layerName = layersData.find(l => l.id === layerId)?.name || layerId;
    
    content.innerHTML = `
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Total Components</div>
                <div class="stat-value">${components.length}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Healthy</div>
                <div class="stat-value healthy">${healthy}</div>
            </div>
            ${degraded > 0 ? `
            <div class="stat-card">
                <div class="stat-label">Degraded</div>
                <div class="stat-value degraded">${degraded}</div>
            </div>
            ` : ''}
            ${critical > 0 ? `
            <div class="stat-card">
                <div class="stat-label">Critical</div>
                <div class="stat-value critical">${critical}</div>
            </div>
            ` : ''}
            ${unknown > 0 ? `
            <div class="stat-card">
                <div class="stat-label">Unknown</div>
                <div class="stat-value" style="color: #64748b;">${unknown}</div>
            </div>
            ` : ''}
        </div>
        
        <h2 class="section-title">
            ${layersData.find(l => l.id === layerId)?.icon || '📦'} 
            ${layerName} Components
        </h2>
        
        ${components.length === 0 ? `
            <div style="text-align: center; padding: 3rem; color: #64748b;">
                <p>No components registered for this layer.</p>
            </div>
        ` : `
            <div class="components-grid">
                ${components.map(comp => renderComponentCard(comp)).join('')}
            </div>
        `}
    `;
}

// Render a single component card
function renderComponentCard(comp) {
    const statusColor = statusColors[comp.status] || statusColors.unknown;
    const lastCheck = comp.last_check 
        ? new Date(comp.last_check).toLocaleString() 
        : 'Never';
    
    return `
        <div class="component-card" onclick="showComponentDetails('${comp.component.component_id}')">
            <div class="component-header">
                <div>
                    <div class="component-name">${escapeHtml(comp.component.name)}</div>
                    <div class="component-description">
                        ${escapeHtml(comp.component.description || '')}
                    </div>
                </div>
                <div class="component-status status-indicator-${comp.status}" 
                     title="Status: ${comp.status}"></div>
            </div>
            
            <ul class="checks-list">
                ${comp.checks.map(check => renderCheckItem(check)).join('')}
            </ul>
            
            <div style="margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid #2a2a35; 
                        font-size: 0.75rem; color: #64748b;">
                Last check: ${lastCheck}
            </div>
        </div>
    `;
}

// Render a single check item
function renderCheckItem(check) {
    const statusColor = statusColors[check.status] || statusColors.unknown;
    let valueDisplay = '';
    
    if (check.actual_value !== null && check.actual_value !== undefined) {
        const unit = check.check_type === 'latency' ? 'ms' : '';
        valueDisplay = `<span class="check-value">${Math.round(check.actual_value)}${unit}</span>`;
    }
    
    const message = check.message ? `
        <div class="check-message">${escapeHtml(check.message)}</div>
    ` : '';
    
    return `
        <li class="check-item">
            <div class="check-status status-indicator-${check.status}"></div>
            <span class="check-name">${escapeHtml(check.name)}</span>
            ${valueDisplay}
        </li>
        ${message}
    `;
}

// Show component details modal
async function showComponentDetails(componentId) {
    try {
        const response = await fetch(`/api/components/${componentId}/checks`);
        if (!response.ok) throw new Error('Failed to fetch component details');
        
        const data = await response.json();
        const modal = document.getElementById('modal');
        const title = document.getElementById('modal-title');
        const body = document.getElementById('modal-body');
        
        title.textContent = data.component.name;
        
        const timestamp = new Date(data.timestamp).toLocaleString();
        
        body.innerHTML = `
            <div style="margin-bottom: 1.5rem;">
                <p style="color: #64748b; margin-bottom: 0.5rem;">
                    ${escapeHtml(data.component.description || 'No description')}
                </p>
                <p style="font-size: 0.875rem; color: #94a3b8;">
                    ID: <code>${data.component.component_id}</code> | 
                    Layer: ${data.component.layer} |
                    Last check: ${timestamp}
                </p>
            </div>
            
            <h3 style="font-size: 1rem; margin-bottom: 1rem;">Health Checks</h3>
            
            ${data.checks.map(check => `
                <div style="background: #1e1e28; border-radius: 6px; padding: 1rem; margin-bottom: 0.75rem;">
                    <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.5rem;">
                        <div class="status-indicator-${check.status}" 
                             style="width: 10px; height: 10px; border-radius: 50%;"></div>
                        <strong>${escapeHtml(check.name)}</strong>
                        <span style="margin-left: auto; font-size: 0.75rem; text-transform: uppercase; 
                                     padding: 0.125rem 0.5rem; border-radius: 4px; background: #2a2a35;">
                            ${check.check_type}
                        </span>
                    </div>
                    
                    ${check.message ? `
                        <p style="color: #94a3b8; font-size: 0.875rem; margin-bottom: 0.5rem;">
                            ${escapeHtml(check.message)}
                        </p>
                    ` : ''}
                    
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); 
                                gap: 0.75rem; font-size: 0.875rem; margin-top: 0.75rem;">
                        ${check.response_time_ms ? `
                            <div>
                                <span style="color: #64748b;">Response:</span>
                                <span>${Math.round(check.response_time_ms)}ms</span>
                            </div>
                        ` : ''}
                        ${check.actual_value !== null ? `
                            <div>
                                <span style="color: #64748b;">Value:</span>
                                <span>${Math.round(check.actual_value * 100) / 100}</span>
                            </div>
                        ` : ''}
                        ${check.warning_threshold ? `
                            <div>
                                <span style="color: #64748b;">Warning:</span>
                                <span>${check.warning_threshold}</span>
                            </div>
                        ` : ''}
                        ${check.critical_threshold ? `
                            <div>
                                <span style="color: #64748b;">Critical:</span>
                                <span>${check.critical_threshold}</span>
                            </div>
                        ` : ''}
                        ${check.consecutive_failures > 0 ? `
                            <div>
                                <span style="color: #64748b;">Failures:</span>
                                <span style="color: #ef4444;">${check.consecutive_failures}</span>
                            </div>
                        ` : ''}
                    </div>
                </div>
            `).join('')}
            
            ${data.checks.length === 0 ? `
                <p style="color: #64748b; text-align: center; padding: 2rem;">
                    No health checks available for this component.
                </p>
            ` : ''}
        `;
        
        modal.classList.add('active');
    } catch (e) {
        console.error('Failed to load component details:', e);
        alert('Failed to load component details: ' + e.message);
    }
}

// Close modal
function closeModal(event) {
    if (!event || event.target.id === 'modal' || event.target.classList.contains('modal-close')) {
        document.getElementById('modal').classList.remove('active');
    }
}

// Show maintenance view
function showMaintenance() {
    const modal = document.getElementById('modal');
    const title = document.getElementById('modal-title');
    const body = document.getElementById('modal-body');
    
    title.textContent = '🔧 Maintenance Windows';
    body.innerHTML = `
        <div style="text-align: center; padding: 3rem; color: #64748b;">
            <p>Maintenance scheduling coming soon.</p>
            <p style="font-size: 0.875rem; margin-top: 1rem;">
                View and schedule system maintenance windows.
            </p>
        </div>
    `;
    modal.classList.add('active');
}

// Show alerts view
function showAlerts() {
    const modal = document.getElementById('modal');
    const title = document.getElementById('modal-title');
    const body = document.getElementById('modal-body');
    
    title.textContent = '🔔 Active Alerts';
    body.innerHTML = `
        <div style="text-align: center; padding: 3rem; color: #64748b;">
            <p>Alert management coming soon.</p>
            <p style="font-size: 0.875rem; margin-top: 1rem;">
                View and manage system alerts and notifications.
            </p>
        </div>
    `;
    modal.classList.add('active');
}

// Show metrics view
function showMetrics() {
    const modal = document.getElementById('modal');
    const title = document.getElementById('modal-title');
    const body = document.getElementById('modal-body');
    
    title.textContent = '📈 System Metrics';
    body.innerHTML = `
        <div style="text-align: center; padding: 3rem; color: #64748b;">
            <p>Metrics visualization coming soon.</p>
            <p style="font-size: 0.875rem; margin-top: 1rem;">
                View historical metrics and performance trends.
            </p>
        </div>
    `;
    modal.classList.add('active');
}

// Keyboard shortcuts
function handleKeyboard(e) {
    // ESC to close modal
    if (e.key === 'Escape') {
        closeModal();
    }
    
    // R to refresh
    if (e.key === 'r' || e.key === 'R') {
        if (currentLayer) {
            loadLayerContent(currentLayer);
        }
        loadSummary();
    }
    
    // Number keys to switch layers
    if (e.key >= '1' && e.key <= '7') {
        const index = parseInt(e.key) - 1;
        if (layersData[index]) {
            selectLayer(layersData[index].id);
        }
    }
}

// Utility: Escape HTML to prevent XSS
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Utility: Show error message
function showError(message) {
    const content = document.getElementById('content');
    if (content) {
        content.innerHTML = `
            <div style="text-align: center; padding: 4rem; color: #ef4444;">
                <p>${escapeHtml(message)}</p>
            </div>
        `;
    }
}

// Initialize on load
document.addEventListener('DOMContentLoaded', init);

// Handle visibility change - pause/resume updates
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        // Pause updates when tab is hidden
        if (refreshInterval) {
            clearInterval(refreshInterval);
            refreshInterval = null;
        }
    } else {
        // Resume updates when tab is visible
        if (!refreshInterval) {
            refreshInterval = setInterval(() => {
                loadSummary();
                if (currentLayer) {
                    loadLayerContent(currentLayer);
                }
            }, 30000);
            // Immediate refresh on visibility
            loadSummary();
            if (currentLayer) {
                loadLayerContent(currentLayer);
            }
        }
    }
});

// Export functions for global access
window.selectLayer = selectLayer;
window.showComponentDetails = showComponentDetails;
window.closeModal = closeModal;
window.showMaintenance = showMaintenance;
window.showAlerts = showAlerts;
window.showMetrics = showMetrics;
