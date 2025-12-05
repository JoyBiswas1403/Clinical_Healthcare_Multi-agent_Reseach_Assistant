/**
 * Clinical Guideline Research Assistant - Frontend JavaScript
 */

const API_BASE = 'http://localhost:8888';

// DOM Elements
const topicInput = document.getElementById('topicInput');
const searchBtn = document.getElementById('searchBtn');
const progressSection = document.getElementById('progressSection');
const resultsSection = document.getElementById('resultsSection');
const errorSection = document.getElementById('errorSection');

// Set topic from quick-pick buttons
function setTopic(topic) {
    topicInput.value = topic;
    topicInput.focus();
}

// Hide error section
function hideError() {
    errorSection.classList.add('hidden');
}

// Show error
function showError(message) {
    document.getElementById('errorMessage').textContent = message;
    errorSection.classList.remove('hidden');
    progressSection.classList.add('hidden');
}

// Update step status
function updateStep(stepNum, status) {
    const step = document.getElementById(`step${stepNum}`);
    const statusEl = document.getElementById(`step${stepNum}Status`);

    step.classList.remove('active', 'complete');

    if (status === 'active') {
        step.classList.add('active');
        statusEl.textContent = '⏳';
    } else if (status === 'complete') {
        step.classList.add('complete');
        statusEl.textContent = '✓';
    } else {
        statusEl.textContent = '⏳';
    }
}

// Format brief text with highlighted citations
function formatBrief(text) {
    return text.replace(/\[(\d+)\]/g, '<span class="citation">[$1]</span>');
}

// Display results
function displayResults(data) {
    const brief = data.research_brief || {};

    // Brief
    const briefContent = document.getElementById('briefContent');
    briefContent.innerHTML = formatBrief(brief.executive_brief || 'No brief generated.');
    document.getElementById('wordCount').textContent = `${brief.word_count || 0} words`;

    // Sources
    const sources = brief.sources || [];
    const sourcesList = document.getElementById('sourcesList');
    document.getElementById('sourceCount').textContent = `${sources.length} sources`;

    sourcesList.innerHTML = sources.slice(0, 5).map((src, i) => `
        <div class="source-item">
            <span class="source-number">${i + 1}</span>
            <div class="source-info">
                <div class="source-title">${src.title || 'Unknown Title'}</div>
                <div class="source-authors">${src.authors || 'Unknown Authors'}</div>
            </div>
        </div>
    `).join('');

    // Risk Flags
    const risks = brief.risk_flags || [];
    const risksCard = document.getElementById('risksCard');
    const risksList = document.getElementById('risksList');

    if (risks.length > 0) {
        risksCard.classList.remove('hidden');
        risksList.innerHTML = risks.map(risk => `
            <div class="risk-item ${risk.severity || 'medium'}">
                <span class="risk-severity ${risk.severity || 'medium'}">${risk.severity || 'MEDIUM'}</span>
                <span class="risk-text">${risk.description || 'No description'}</span>
            </div>
        `).join('');
    } else {
        risksCard.classList.add('hidden');
    }

    // Metrics
    document.getElementById('metricTime').textContent = `${(data.metrics?.total_time_seconds || 0).toFixed(1)}s`;
    document.getElementById('metricDocs').textContent = data.metrics?.documents_retrieved || 0;
    document.getElementById('metricCitations').textContent = sources.length;

    // Show results
    resultsSection.classList.remove('hidden');
}

// Main research function
async function runResearch() {
    const topic = topicInput.value.trim();

    if (!topic) {
        showError('Please enter a research topic.');
        return;
    }

    // Reset UI
    searchBtn.disabled = true;
    errorSection.classList.add('hidden');
    resultsSection.classList.add('hidden');
    progressSection.classList.remove('hidden');

    // Reset steps
    updateStep(1, 'pending');
    updateStep(2, 'pending');
    updateStep(3, 'pending');
    document.getElementById('progressText').textContent = 'Starting research...';

    try {
        // Call API
        const response = await fetch(`${API_BASE}/api/research`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ topic })
        });

        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }

        const data = await response.json();

        // Update all steps to complete
        updateStep(1, 'complete');
        updateStep(2, 'complete');
        updateStep(3, 'complete');
        document.getElementById('progressText').textContent = 'Research complete!';

        // Wait a moment then show results
        setTimeout(() => {
            progressSection.classList.add('hidden');
            displayResults(data);
        }, 500);

    } catch (error) {
        console.error('Research error:', error);
        showError(`Failed to run research: ${error.message}. Make sure the API server is running.`);
    } finally {
        searchBtn.disabled = false;
    }
}

// Event listeners
topicInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        runResearch();
    }
});

// Initialize
console.log('Clinical Guideline Research Assistant loaded');
