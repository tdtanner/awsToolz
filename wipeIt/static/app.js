// State management
let currentResources = {};
let currentProfile = '';
let currentRegion = '';
let activeTab = '';

// DOM elements
const startScreen = document.getElementById('start-screen');
const resourceScreen = document.getElementById('resource-screen');
const profileInput = document.getElementById('profile');
const regionInput = document.getElementById('region');
const startButton = document.getElementById('start-inventory');
const loading = document.getElementById('loading');
const errorDiv = document.getElementById('error');
const accountInfo = document.getElementById('account-info');
const tabsContainer = document.getElementById('tabs');
const tabContent = document.getElementById('tab-content');
const selectAllBtn = document.getElementById('select-all');
const deselectAllBtn = document.getElementById('deselect-all');
const burnButton = document.getElementById('burn-button');
const refreshButton = document.getElementById('refresh-inventory');
const deletionResults = document.getElementById('deletion-results');
const resultsContent = document.getElementById('results-content');

// Resource type display names
const resourceTypeNames = {
    'lambda': 'Lambda Functions',
    'api_gateway': 'API Gateway',
    'sqs': 'SQS Queues',
    'ec2': 'EC2 Instances',
    'cloudwatch_logs': 'CloudWatch Logs',
    'ebs': 'EBS Volumes',
    's3': 'S3 Buckets'
};

// Event listeners
startButton.addEventListener('click', runInventory);
selectAllBtn.addEventListener('click', selectAll);
deselectAllBtn.addEventListener('click', deselectAll);
burnButton.addEventListener('click', confirmAndBurn);
refreshButton.addEventListener('click', runInventory);

// Run inventory
async function runInventory() {
    const profile = profileInput.value.trim() || 'default';
    const region = regionInput.value.trim() || 'us-east-1';

    currentProfile = profile;
    currentRegion = region;

    showLoading(true);
    hideError();

    try {
        const response = await fetch('/api/inventory', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ profile, region })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to run inventory');
        }

        currentResources = data.resources;
        displayResources();
        showResourceScreen();

    } catch (error) {
        showError(error.message);
    } finally {
        showLoading(false);
    }
}

// Display resources in tabs
function displayResources() {
    accountInfo.textContent = `Profile: ${currentProfile} | Region: ${currentRegion}`;

    // Clear existing tabs and content
    tabsContainer.innerHTML = '';
    tabContent.innerHTML = '';

    // Create tabs for each resource type
    let firstTab = true;
    for (const [type, resources] of Object.entries(currentResources)) {
        if (resources.length === 0) continue;

        // Create tab button
        const tab = document.createElement('button');
        tab.className = `tab ${firstTab ? 'active' : ''}`;
        tab.dataset.type = type;
        tab.innerHTML = `
            ${resourceTypeNames[type] || type}
            <span class="count">${resources.length}</span>
        `;
        tab.addEventListener('click', () => switchTab(type));
        tabsContainer.appendChild(tab);

        // Create tab pane
        const pane = document.createElement('div');
        pane.className = `tab-pane ${firstTab ? 'active' : ''}`;
        pane.dataset.type = type;
        pane.innerHTML = createResourceList(type, resources);
        tabContent.appendChild(pane);

        if (firstTab) {
            activeTab = type;
            firstTab = false;
        }
    }

    // Show message if no resources found
    if (tabsContainer.children.length === 0) {
        tabContent.innerHTML = '<div class="empty-state">No resources found in this region.</div>';
    }
}

// Create resource list HTML
function createResourceList(type, resources) {
    if (resources.length === 0) {
        return '<div class="empty-state">No resources found.</div>';
    }

    const items = resources.map(resource => `
        <div class="resource-item">
            <input type="checkbox" id="${type}-${resource.id}" data-type="${type}" data-id="${resource.id}">
            <label for="${type}-${resource.id}">
                ${resource.name}
                ${resource.state ? `<span class="resource-meta">${resource.state}</span>` : ''}
                ${resource.runtime ? `<span class="resource-meta">${resource.runtime}</span>` : ''}
                ${resource.size ? `<span class="resource-meta">${resource.size}</span>` : ''}
            </label>
        </div>
    `).join('');

    return `<div class="resource-list">${items}</div>`;
}

// Switch between tabs
function switchTab(type) {
    // Update tab buttons
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.type === type);
    });

    // Update tab panes
    document.querySelectorAll('.tab-pane').forEach(pane => {
        pane.classList.toggle('active', pane.dataset.type === type);
    });

    activeTab = type;
}

// Select all in current tab
function selectAll() {
    const activePane = document.querySelector('.tab-pane.active');
    if (activePane) {
        activePane.querySelectorAll('input[type="checkbox"]').forEach(cb => {
            cb.checked = true;
        });
    }
}

// Deselect all in current tab
function deselectAll() {
    const activePane = document.querySelector('.tab-pane.active');
    if (activePane) {
        activePane.querySelectorAll('input[type="checkbox"]').forEach(cb => {
            cb.checked = false;
        });
    }
}

// Get selected resources
function getSelectedResources() {
    const selections = {};

    document.querySelectorAll('input[type="checkbox"]:checked').forEach(cb => {
        const type = cb.dataset.type;
        const id = cb.dataset.id;

        if (!selections[type]) {
            selections[type] = [];
        }
        selections[type].push(id);
    });

    return selections;
}

// Confirm and burn
function confirmAndBurn() {
    const selections = getSelectedResources();
    const totalCount = Object.values(selections).reduce((sum, arr) => sum + arr.length, 0);

    if (totalCount === 0) {
        alert('Please select at least one resource to delete.');
        return;
    }

    const confirmation = confirm(
        `⚠️ WARNING ⚠️\n\n` +
        `You are about to DELETE ${totalCount} resource(s).\n\n` +
        `This action CANNOT be undone!\n\n` +
        `Are you absolutely sure you want to continue?`
    );

    if (confirmation) {
        burnResources(selections);
    }
}

// Burn resources
async function burnResources(selections) {
    burnButton.disabled = true;
    burnButton.textContent = 'Burning...';
    deletionResults.classList.add('hidden');

    try {
        const response = await fetch('/api/delete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ selections })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to delete resources');
        }

        displayResults(data.results);

        // Refresh inventory after deletion
        setTimeout(() => {
            runInventory();
        }, 2000);

    } catch (error) {
        alert(`Error: ${error.message}`);
    } finally {
        burnButton.disabled = false;
        burnButton.textContent = '🔥 Burn It All Down...';
    }
}

// Display deletion results
function displayResults(results) {
    resultsContent.innerHTML = results.map(result => `
        <div class="result-item ${result.status === 'failed' ? 'failed' : ''}">
            <div class="result-resource">${result.resource}</div>
            <div class="result-status">
                ${result.status === 'deleted' ? '✅ Deleted' : '❌ Failed'}
                ${result.type ? ` (${resourceTypeNames[result.type] || result.type})` : ''}
            </div>
            ${result.error ? `<div class="result-error">Error: ${result.error}</div>` : ''}
        </div>
    `).join('');

    deletionResults.classList.remove('hidden');
}

// UI helpers
function showLoading(show) {
    loading.classList.toggle('hidden', !show);
    startButton.disabled = show;
}

function showError(message) {
    errorDiv.textContent = message;
    errorDiv.classList.remove('hidden');
}

function hideError() {
    errorDiv.classList.add('hidden');
}

function showResourceScreen() {
    startScreen.classList.remove('active');
    resourceScreen.classList.add('active');
}
