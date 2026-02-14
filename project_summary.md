# Project Overview: CET6 Web Learning Platform

## 1. Project Goal
The platform provides an interactive environment for studying CET6 (College English Test Band 6) past exam papers. It integrates document reading, tool-based annotation (highlighting, drawing), vocabulary management, and essay writing.

## 2. System Architecture

### 2.1 Backend (Python/FastAPI)
- **Framework**: FastAPI
- **Entry Point**: `backend/main.py`
- **Data Source**: Local file system (`cet6document/` directory) containing exam papers organized by Year/Month.
- **Persistence**:
  - `vocabulary.json`: Stores user vocabulary.
  - `backend/data/annotations/`: JSON storage for document annotations (strokes, highlights).
  - `backend/data/essays/`: Markdown storage for user essays/notes per document.
- **Key Responsibilities**:
  - Serve file structure and content.
  - Manage user data (vocabulary, annotations, essays).
  - Proxy simplified dictionary lookups.

### 2.2 Frontend (Vue 3 + Vite)
- **Framework**: Vue 3 (Composition API)
- **Styling**: CSS (Scoped)
- **Key Components**:
  - `App.vue`: Main layout orchestration, state management (current view, tool selection), and sidebar/markdown toggling.
  - `DocumentViewer.vue`: Renders simulated PDF text layers and provides a canvas overlay for user annotations (drawing, highlighting).
  - `SideToolbar.vue`: Floating toolbar for tool selection inside the viewer.
  - `TopToolbar.vue`: Navigation, view switching, paper selection.
  - `WordBook.vue`: Vocabulary list management.
- **External Libs**: `marked` (for Markdown rendering), `axios` (HTTP client - implied usage).

## 3. Current Workflow & Issues

### 3.1 Document Viewing
- **Flow**: User selects a paper -> Backend parses text -> Frontend renders lines.
- **Issue**: Annotations (Canvas drawings) are strictly in-memory. Reloading the page or switching papers loses all highlights.

### 3.2 Essay / Note Taking
- **Flow**: User toggles "Essay Writer" -> Overlays a basic text area.
- **Issue 1 (UX)**: Layout is poor; it covers the document. User wants split-screen (Left: Doc, Right: Editor+Preview).
- **Issue 2 (Persistence)**: Text logs are not saved to the backend. No auto-save or manual save triggers.

### 3.3 Vocabulary
- **Flow**: Select text/Click -> Add to Word Book -> Saved to `vocabulary.json`.
- **Status**: Functional persistence.

## 4. Implemented Features (Update)

### 4.1 Persistence Layer Expansion (COMPLETED)
- Created `backend/data` to isolate user data.
- Implemented endpoints `GET/POST /api/v1/user/annotations` for saving strokes.
- Implemented endpoints `GET/POST /api/v1/user/essay` for saving markdown notes.

### 4.2 Split-Screen Writing Environment (COMPLETED)
- Refactored `App.vue` to use a split-screen layout when Essay mode is active.
- Implemented autosave (2s delay) and manual save button for essays.
- Annotations and Essays are now automatically loaded when switching documents.
