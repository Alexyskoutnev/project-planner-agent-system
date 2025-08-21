# Simple Project Planning Frontend

A React TypeScript application for AI-powered project planning.

## Features

- **Simple chat interface** - Chat with AI to describe your project
- **Live document updates** - Watch the project document build as you chat
- **Mock API** - Works out-of-the-box with simulated responses
- **Clean & focused** - No complex agent workflows or user management

## Getting Started

```bash
# Install dependencies
npm install

# Start development server (uses mock API by default)
npm start

# Open http://localhost:3000 to view the app
```

## Architecture

- **ProjectRoom** - Split-screen layout with chat and document
- **ChatInterface** - Simple messaging with AI assistant
- **DocumentViewer** - Live-updating project document
- **JoinForm** - Entry point to start or join a project

## Simple API

The app uses two simple API endpoints:

```typescript
// Send a chat message and get AI response
POST /chat
{
  message: string,
  projectId: string
}
Response: {
  response: string,
  document?: string  // Updated document if available
}

// Get current document state
GET /document/:projectId
Response: {
  document: string
}
```

## Mock API

By default, uses a mock API that simulates realistic AI responses and progressive document building. To connect to a real backend, set `REACT_APP_USE_MOCK=false`.

## Usage

1. Enter a project ID (or use default)
2. Start chatting about your project
3. Watch the document update as you provide more details
4. Continue refining until you have a complete project plan

## Available Scripts

### `npm start`
Runs the app in development mode. Open [http://localhost:3000](http://localhost:3000) to view it.

### `npm test`
Launches the test runner in interactive watch mode.

### `npm run build`
Builds the app for production to the `build` folder.
