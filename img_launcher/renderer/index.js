const searchInput = document.getElementById('search');
const resultsDiv  = document.getElementById('results');
const selectBtn   = document.getElementById('select-folder');

// WebSocket connection for real-time notifications
let ws = null;
let isIndexingComplete = false;

// Initialize WebSocket connection
function initWebSocket() {
  try {
    ws = new WebSocket('ws://localhost:8000/ws');
    
    ws.onopen = () => {
      console.log('WebSocket connected');
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleWebSocketMessage(data);
    };
    
    ws.onclose = () => {
      console.log('WebSocket disconnected');
      // Attempt to reconnect after 5 seconds
      setTimeout(initWebSocket, 5000);
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  } catch (error) {
    console.error('Failed to initialize WebSocket:', error);
    // Retry connection after 5 seconds
    setTimeout(initWebSocket, 5000);
  }
}

// Handle WebSocket messages
function handleWebSocketMessage(data) {
  switch (data.type) {
    case 'indexing_completed':
      showIndexingComplete(data.total_indexed);
      break;
    case 'indexing_started':
      resetIndexingState();
      break;
    case 'indexing_progress':
      updateIndexingProgress(data);
      break;
    case 'indexing_error':
      console.error('Indexing error:', data.error);
      resetIndexingState();
      break;
  }
}

// Show indexing complete state
function showIndexingComplete(totalIndexed) {
  isIndexingComplete = true;
  
  // Update placeholder text
  searchInput.placeholder = 'Indexing complete - Type to search images';
  
  // Add CSS class for green styling
  selectBtn.classList.add('indexing-complete');
  
  // Clear results area
  resultsDiv.innerHTML = '';
  
  console.log(`Indexing completed: ${totalIndexed} images indexed`);
}

// Reset indexing state (when user starts searching or new indexing begins)
function resetIndexingState() {
  if (isIndexingComplete) {
    isIndexingComplete = false;
    
    // Reset placeholder text
    searchInput.placeholder = 'Type to search images...';
    
    // Remove CSS class for green styling
    selectBtn.classList.remove('indexing-complete');
  }
}

// Update indexing progress
function updateIndexingProgress(data) {
  resultsDiv.innerHTML = `Indexing: ${data.processed}/${data.total} images (${data.percentage}%)`;
}

// Initialize WebSocket when page loads
initWebSocket();

// Helper to clear input & results, then collapse window
function clearAndCollapse() {
  searchInput.value = '';
  resultsDiv.innerHTML = '';
  resetIndexingState(); // Reset the indexing complete state
  window.launcherAPI.collapseWindow();
}

// On Alt+S toggle: clear & collapse
window.launcherAPI.onClear(() => {
  clearAndCollapse();
});

// ENTER → expand & perform search
searchInput.addEventListener('keydown', async (e) => {
  if (e.key !== 'Enter') return;
  const query = searchInput.value.trim();
  if (!query) return;

  // Reset indexing complete state when user starts searching
  resetIndexingState();

  window.launcherAPI.expandWindow();
  resultsDiv.innerHTML = 'Searching…';

  try {
    const res = await fetch('http://localhost:8000/search/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    });
    const items = await res.json();
    displayResults(items);
  } catch (err) {
    console.error('Search error:', err);
    resultsDiv.innerHTML = 'Error during search';
  }
});

// INPUT change → if empty, clear results & collapse
searchInput.addEventListener('input', () => {
  // Reset indexing complete state when user starts typing
  if (searchInput.value.trim() !== '' && isIndexingComplete) {
    resetIndexingState();
  }
  
  if (searchInput.value.trim() === '') {
    resultsDiv.innerHTML = '';
    setTimeout(() => window.launcherAPI.collapseWindow(), 0);
  }
});

// Render thumbnails + accuracy
function displayResults(items) {
  if (!items.length) {
    resultsDiv.innerHTML = '<div style="color:#bbb">No results</div>';
    return;
  }

  resultsDiv.innerHTML = items.map(item => `
    <div class="result" data-path="${item.path}">
      <img src="${item.full_url}" alt="" />
      <div class="caption">${(item.score * 100).toFixed(1)}%</div>
    </div>
  `).join('');
}

// Click thumbnail → open via backend
resultsDiv.addEventListener('click', async (e) => {
  const card = e.target.closest('.result');
  if (!card) return;
  const filePath = card.dataset.path;

  try {
    await fetch('http://localhost:8000/open-image/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: filePath })
    });
  } catch (err) {
    console.error('Open-image error:', err);
  }
});

// Select Folder → show picker, index backend, remount, then feedback
selectBtn.addEventListener('click', async () => {
  const result = await window.launcherAPI.selectFolder();
  if (result.canceled || !result.filePaths.length) return;

  const folderPath = result.filePaths[0];
  
  // Reset any previous indexing complete state
  resetIndexingState();
  
  // Show initial indexing message
  resultsDiv.innerHTML = 'Indexing folder…';

  try {
    // Set the folder in backend
    const resp1 = await fetch('http://localhost:8000/folders', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ folders: [folderPath] })
    });
    if (!resp1.ok) throw new Error(await resp1.text());

    // Start async indexing (this will send WebSocket notifications)
    await fetch('http://localhost:8000/update-images/', { method: 'POST' });
    
    // Note: Completion will be handled via WebSocket message
    // The showIndexingComplete function will update the UI when done
    
  } catch (err) {
    console.error(err);
    resultsDiv.innerHTML = 'Failed to index folder';
    resetIndexingState();
  }
});
