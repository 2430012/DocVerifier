document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const fileNameDisplay = document.getElementById('file-name');
    const form = document.getElementById('verify-form');
    const analyzeBtn = document.getElementById('analyze-btn');
    const loading = document.getElementById('loading');
    const emptyState = document.getElementById('empty-state');
    const resultsContainer = document.getElementById('results-container');
    const elementsList = document.getElementById('elements-list');
    
    let currentFiles = [];

    // Drag and Drop Handlers
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.add('dragover'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.remove('dragover'), false);
    });

    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    });

    fileInput.addEventListener('change', function() {
        handleFiles(this.files);
    });

function handleFiles(files) {
        if (files.length > 0) {
            currentFiles = Array.from(files); // Guardamos todos los archivos
            fileNameDisplay.textContent = `${currentFiles.length} archivo(s) seleccionado(s)`;
            fileNameDisplay.style.color = 'var(--success)';
            
            // Auto-detectar lenguaje basado en el primer archivo
            const ext = currentFiles[0].name.split('.').pop().toLowerCase();
            const langSelect = document.getElementById('language');
            if(ext === 'py') langSelect.value = 'python';
            if(ext === 'java') langSelect.value = 'java';
            if(ext === 'cpp' || ext === 'cc' || ext === 'h' || ext === 'hpp') langSelect.value = 'cpp';
            if(ext === 'kt') langSelect.value = 'kotlin';
        }
    }

    // Form Submit
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        if (currentFiles.length === 0) {
            alert('Please select files first.');
            return;
        }

        const language = document.getElementById('language').value;
        const semantic = document.getElementById('semantic').checked;

        const formData = new FormData();
        // Adjuntamos TODOS los archivos al FormData con la llave "files"
        currentFiles.forEach(file => {
            formData.append('files', file); 
        });
        formData.append('language', language);
        formData.append('semantic', semantic);

        // UI State
        analyzeBtn.disabled = true;
        loading.classList.remove('hidden');
        emptyState.classList.add('hidden');
        resultsContainer.classList.add('hidden');

        try {
            const response = await fetch('/api/verify', {
                method: 'POST',
                body: formData
            });
            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Failed to analyze file');
            }

            const data = await response.json();
            renderResults(data);
            
        } catch (error) {
            alert('Error: ' + error.message);
            emptyState.classList.remove('hidden');
        } finally {
            analyzeBtn.disabled = false;
            loading.classList.add('hidden');
        }
    });

    function renderResults(results) {
        if (results.length === 0) {
            alert("No documentable elements found.");
            emptyState.classList.remove('hidden');
            return;
        }

        resultsContainer.classList.remove('hidden');
        elementsList.innerHTML = '';

        let totalCov = 0, totalComp = 0, totalCoh = 0;

        results.forEach(res => {
            totalCov += res.metrics.coverage;
            totalComp += res.metrics.completeness;
            totalCoh += res.metrics.coherence;

            const card = document.createElement('div');
            card.className = 'element-card';

            const covClass = getColorClass(res.metrics.coverage);
            const compClass = getColorClass(res.metrics.completeness);
            
            let issuesHtml = '';
            if (res.metrics.issues && res.metrics.issues.length > 0) {
                const lis = res.metrics.issues.map(i => `<li>${i}</li>`).join('');
                issuesHtml = `
                    <div class="issues-list">
                        <h4><i data-lucide="alert-triangle" style="width:16px;height:16px"></i> Documentation Issues</h4>
                        <ul>${lis}</ul>
                    </div>
                `;
            } else {
                issuesHtml = `
                    <div class="no-issues">
                        <i data-lucide="check-circle" style="width:18px;height:18px"></i> Perfect documentation!
                    </div>
                `;
            }

            let semHtml = '';
            if (res.metrics.semantic_similarity !== null) {
                const semClass = getColorClass(res.metrics.semantic_similarity);
                semHtml = `
                    <div class="metric">
                        <span class="metric-label">Semantic Sim</span>
                        <span class="metric-val ${semClass}">${(res.metrics.semantic_similarity * 100).toFixed(0)}%</span>
                    </div>
                `;
            }

            card.innerHTML = `
                <div class="element-header">
                    <div class="element-title">
                        <span class="element-type" style="background:var(--secondary); color:#000; margin-right:5px;">
                        <i data-lucide="file-code" style="width:12px;height:12px"></i> ${res.file_name}</span>
                        <span class="element-type">${res.type}</span>
                        <span class="element-name">${res.element}</span>
                    </div>
                    <div class="element-line">
                        <i data-lucide="hash" style="width:14px;height:14px"></i> Line ${res.line}
                    </div>
                </div>
                <div class="element-metrics">
                    <div class="metric">
                        <span class="metric-label">Coverage</span>
                        <span class="metric-val ${covClass}">${(res.metrics.coverage * 100).toFixed(0)}%</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Completeness</span>
                        <span class="metric-val ${compClass}">${(res.metrics.completeness * 100).toFixed(0)}%</span>
                    </div>
                    ${semHtml}
                </div>
                ${issuesHtml}
            `;
            elementsList.appendChild(card);
        });

        // Re-init icons for new DOM elements
        lucide.createIcons();

        // Update top stats
        const len = results.length;
        document.getElementById('stat-cov').textContent = `${((totalCov / len) * 100).toFixed(0)}%`;
        document.getElementById('stat-comp').textContent = `${((totalComp / len) * 100).toFixed(0)}%`;
        document.getElementById('stat-coh').textContent = `${((totalCoh / len) * 100).toFixed(0)}%`;
    }

    function getColorClass(val) {
        if (val >= 0.8) return 'val-good';
        if (val >= 0.5) return 'val-warn';
        return 'val-bad';
    }
});
