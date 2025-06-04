# Image Search Components

This folder groups the pieces that make up the `ModernImageSearch` feature.  Breaking the large component into smaller parts makes the code easier to reason about and enables focused tests for each unit.

## Components

- **SearchControls** – handles folder selection and search form logic.
- **FolderBadges** – displays the list of selected folders.
- **ImageModal** – shows a selected image with actions.
- **IndexingStatusBanner** – progress banner shown while the backend is indexing.

## Testing Suggestions

- Use [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/) with Jest to render each component in isolation.
- Mock network requests and WebSocket events to verify state updates without relying on the backend.
- Test the main `ModernImageSearch` component with the subcomponents mocked so only its orchestration logic is exercised.

## Further Improvements

- Move utility helpers (e.g. WebSocket handling or scoring colour logic) into their own modules.
- Consider introducing a state management library if the component tree grows more complex.

