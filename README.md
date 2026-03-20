# EngramFlow (Project OpenMind)

A non-parametric memory architecture that mimics human learning by updating a Synaptic Knowledge Graph instead of model parameters.

## Architecture

*   **Backend (`backend/`)**: Python-based API and architecture management.
    *   `src/graph/`: Nodes, Edges, and Graph space management.
    *   `src/memory/`: Engram Trace operations.
    *   `src/llm/`: Interactions with Gemini models for extraction and embeddings.
*   **Frontend (`frontend/`)**: React-based web interface for 3D/2D visualization of the "Shared Mind UI" and manual modification.
