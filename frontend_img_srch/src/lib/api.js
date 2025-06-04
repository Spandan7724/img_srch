"use client";

export const searchImages = async (query) => {
  const response = await fetch('http://localhost:8000/search/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query })
  });
  if (!response.ok) {
    throw new Error('Search failed');
  }
  return response.json();
};

export const sendFolders = async (folders) => {
  const folderResponse = await fetch('http://localhost:8000/folders', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ folders })
  });
  if (!folderResponse.ok) {
    const errorData = await folderResponse.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to update folders on server');
  }
  const updateResponse = await fetch('http://localhost:8000/update-images/', { method: 'POST' });
  if (!updateResponse.ok) {
    throw new Error('Failed to update image directory on backend');
  }
};

export const openFile = async (path) => {
  const response = await fetch('http://localhost:8000/open-file/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path })
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to open file in explorer');
  }
  return response.json();
};

export const openImage = async (path) => {
  const response = await fetch('http://localhost:8000/open-image/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path })
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to open image');
  }
  return response.json();
};
