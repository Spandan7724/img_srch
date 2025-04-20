const searchInput = document.getElementById('search');
const resultsDiv  = document.getElementById('results');
const selectBtn   = document.getElementById('select-folder');

// Helper to clear input & results, then collapse window
function clearAndCollapse() {
  searchInput.value = '';
  resultsDiv.innerHTML = '';
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
  resultsDiv.innerHTML = 'Indexing folder…';

  try {
    const resp1 = await fetch('http://localhost:8000/folders', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ folders: [folderPath] })
    });
    if (!resp1.ok) throw new Error(await resp1.text());

    await fetch('http://localhost:8000/update-images/', { method: 'POST' });
    resultsDiv.innerHTML = 'Folder indexed – ready to search';

    setTimeout(clearAndCollapse, 1000);
  } catch (err) {
    console.error(err);
    resultsDiv.innerHTML = 'Failed to index folder';
  }
});
