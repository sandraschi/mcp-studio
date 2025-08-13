# MCP Studio Frontend DXT Package

This is the DXT (Developer Experience Toolkit) package for the MCP Studio Frontend, a modern React-based interface for managing MCP (Model Control Protocol) servers and tools.

## Prerequisites

- Node.js 16.0.0 or later
- npm 8.0.0 or later
- DXT CLI installed globally
- MCP Studio Backend service

## Installation

1. Install the DXT CLI if you haven't already:
   ```bash
   npm install -g @dxt/cli
   ```

2. Navigate to the package directory:
   ```bash
   cd dxt-frontend
   ```

3. Install dependencies:
   ```bash
   npm install
   ```

## Configuration

### Required Settings

1. Edit the `user_config` section in `manifest.json` to set:
   - `api_url`: The URL of your MCP Studio API server
   - `port`: The port to run the frontend on (default: 3000)

### Environment Variables

Create a `.env` file in the `dxt-frontend` directory with the following variables:

```env
REACT_APP_API_URL=http://localhost:8000
PORT=3000
```

## Building the Package

1. Build the React application:
   ```bash
   cd mcp-studio-react
   npm install
   npm run build
   cd ..
   ```

2. Validate the manifest:
   ```bash
   dxt validate manifest.json
   ```

3. Package the DXT extension:
   ```bash
   dxt pack -o mcp-studio-frontend.dxt
   ```

4. (Optional) Sign the package:
   ```bash
   dxt sign mcp-studio-frontend.dxt --key your-private-key.pem
   ```

## Usage

### Starting the Frontend

```bash
dxt start mcp-studio-frontend.dxt
```

### Accessing the Web Interface

1. Open a web browser
2. Navigate to `http://localhost:3000` (or your configured port)
3. Log in with your credentials

## Development

### Prerequisites

- Node.js 16.0.0 or later
- npm 8.0.0 or later
- DXT CLI

### Setup

1. Install dependencies:
   ```bash
   cd mcp-studio-react
   npm install
   ```

2. Start the development server:
   ```bash
   npm start
   ```

### Building for Production

1. Build the production version:
   ```bash
   npm run build
   ```

2. The build files will be in the `build` directory

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, please contact support@mcp-studio.com
