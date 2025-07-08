#!/bin/bash

# BOE MCP Integration Test Setup Script
# This script installs dependencies and prepares the environment for testing

set -e  # Exit on any error

echo "🚀 Setting up BOE MCP Integration Test Environment"
echo "================================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is required but not installed."
    exit 1
fi

echo "✅ pip3 found: $(pip3 --version)"

# Install uv package manager if not present
echo "📦 Checking for uv package manager..."
if ! command -v uv &> /dev/null; then
    echo "📥 Installing uv package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Add uv to PATH for current session
    export PATH="$HOME/.cargo/bin:$PATH"
    
    if ! command -v uv &> /dev/null; then
        echo "⚠️  uv installation may require shell restart. Trying pip install..."
        pip3 install uv
    fi
else
    echo "✅ uv package manager found"
fi

# Install uvx if not present (needed for BOE MCP)
echo "📦 Checking for uvx..."
if ! command -v uvx &> /dev/null; then
    echo "📥 Installing uvx..."
    pip3 install uvx
else
    echo "✅ uvx found"
fi

# Install BOE MCP server
echo "📥 Installing BOE MCP server..."
uvx install boe_mcp || pip3 install boe_mcp

# Install MCP testing dependencies
echo "📥 Installing MCP testing dependencies..."
pip3 install -r mcp_test_requirements.txt

# Verify .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Please ensure OPENAI_API_KEY is set."
    echo "Creating sample .env file..."
    cat > .env << EOF
# OpenAI API Key (required)
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4o-mini
EOF
    echo "📝 Please edit .env file with your actual OpenAI API key"
else
    echo "✅ .env file found"
fi

# Verify BOE MCP config exists
if [ ! -f "boe_mcp_config.json" ]; then
    echo "📝 Creating BOE MCP configuration..."
    cat > boe_mcp_config.json << EOF
{
  "mcpServers": {
    "boe_mcp": {
      "command": "uvx",
      "args": [
        "boe_mcp"
      ]
    }
  }
}
EOF
else
    echo "✅ BOE MCP configuration found"
fi

echo ""
echo "🎉 Setup completed successfully!"
echo "================================================="
echo "To run the BOE MCP integration test:"
echo "  python3 test_mcp_boe_integration.py"
echo ""
echo "To test individual components:"
echo "  # Test BOE MCP server directly:"
echo "  uvx boe_mcp"
echo ""
echo "  # Test mcp-use installation:"
echo "  python3 -c 'from mcp_use import MCPAgent, MCPClient; print(\"mcp-use imported successfully\")'"
echo ""
echo "Make sure your OPENAI_API_KEY is set in the .env file!"