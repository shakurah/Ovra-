# BOE MCP Integration Test

This directory contains a comprehensive test suite for integrating the BOE (Boletín Oficial del Estado) MCP server with our chat application using the `mcp-use` library.

## Overview

The test demonstrates:
- **BOE MCP Server Integration**: Connect to Spanish official gazette API through MCP
- **mcp-use Library**: Use the mcp-use library to manage MCP connections
- **Streaming Responses**: Test real-time streaming of BOE responses
- **OpenAI Summarization**: Process BOE responses through OpenAI for better user experience
- **Tax Rate Queries**: Specifically test Spanish salary tax rates for 2025

## Files

- `test_mcp_boe_integration.py` - Main test script
- `mcp_test_requirements.txt` - Python dependencies for MCP testing
- `setup_mcp_test.sh` - Automated setup script
- `boe_mcp_config.json` - MCP server configuration
- `MCP_INTEGRATION_README.md` - This documentation

## Quick Start

### 1. Automated Setup

```bash
# Run the setup script to install all dependencies
./setup_mcp_test.sh
```

### 2. Manual Setup (Alternative)

```bash
# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install BOE MCP server
uvx install boe_mcp

# Install Python dependencies
pip install -r mcp_test_requirements.txt
```

### 3. Configure Environment

Ensure your `.env` file contains:
```env
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4o-mini
```

### 4. Run the Test

```bash
python3 test_mcp_boe_integration.py
```

## Test Features

### 1. BOE MCP Queries
The test executes multiple queries related to Spanish tax legislation:
- IRPF tax rates for salaries in 2025
- Withholding tax tables for employees
- Tax deductions available in IRPF 2025

### 2. Streaming Responses
Tests the streaming capability of mcp-use library:
- Real-time response chunks from BOE MCP
- Progressive display of results
- Complete response aggregation

### 3. OpenAI Summarization
Processes BOE responses through OpenAI to:
- Summarize complex legal text
- Extract key tax rates and information
- Provide practical recommendations
- Format results for better readability

### 4. Result Persistence
Saves comprehensive test results including:
- All query responses from BOE MCP
- Streaming test results
- OpenAI summaries
- Timestamps and configuration

## Expected Output

The test will produce:

1. **Console Output**: Real-time progress and results
2. **JSON Results File**: Complete test results saved as `boe_mcp_test_results_YYYYMMDD_HHMMSS.json`

### Sample Console Output
```
🚀 Starting BOE MCP Integration Test
==================================================
Timestamp: 2024-01-15 10:30:00
==================================================

🔧 Initializing BOE MCP client...
🤖 Initializing OpenAI LLM...
🚀 Creating MCP Agent...
✅ Initialization complete!

📋 Testing BOE MCP with salary tax rates query...

🔍 Query 1: Buscar legislación consolidada sobre tipos impositivos de IRPF para salarios en 2025
--------------------------------------------------------------------------------
📄 Raw BOE MCP Response 1:
[BOE response content...]

🌊 Testing streaming responses from BOE MCP...
📡 Streaming response:
[Streaming content...]

🧠 Generating OpenAI summary of BOE responses...
📊 OpenAI Summary:
[Summarized tax information...]

💾 Results saved to: boe_mcp_test_results_20240115_103000.json
✅ BOE MCP Integration Test completed successfully!
```

## Integration with Chat Application

This test serves as a foundation for integrating BOE MCP into the main chat application:

### 1. Service Integration
The `BOEMCPTester` class can be adapted into a service:
```python
# In app/services/boe_mcp_service.py
class BOEMCPService:
    async def query_tax_legislation(self, query: str) -> str:
        # Use the tested MCP integration
        pass
```

### 2. API Endpoint
Create endpoints to expose BOE functionality:
```python
# In app/api/v1/boe.py
@router.post("/query")
async def query_boe(query: str):
    # Use BOE MCP service
    pass
```

### 3. Chat Integration
Integrate with existing chat service:
```python
# In app/services/chat_service.py
class ChatService:
    async def process_message_with_boe(self, message: str):
        # 1. Send query to BOE MCP
        # 2. Stream BOE responses
        # 3. Summarize with OpenAI
        # 4. Return to chat
        pass
```

## Dependencies

### Core MCP Libraries
- `mcp-use>=0.1.0` - Main MCP integration library
- `langchain-openai>=0.1.0` - OpenAI integration
- `langchain>=0.2.0` - LangChain framework

### BOE MCP Server
- `boe_mcp` - Spanish BOE MCP server (installed via uvx)
- `uv` - Package manager for Python

### Utilities
- `python-dotenv` - Environment variable management
- `aiohttp` - Async HTTP client
- `orjson` - Fast JSON processing

## Troubleshooting

### Common Issues

1. **uv not found**
   ```bash
   # Install uv manually
   pip install uv
   ```

2. **BOE MCP server not responding**
   ```bash
   # Test BOE MCP directly
   uvx boe_mcp
   ```

3. **OpenAI API errors**
   - Verify OPENAI_API_KEY in .env
   - Check API quota and billing

4. **Import errors**
   ```bash
   # Reinstall dependencies
   pip install -r mcp_test_requirements.txt
   ```

### Debug Mode

To run with additional debugging:
```python
# Add to test script
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Next Steps

1. **Production Integration**: Adapt the test code for production use
2. **Error Handling**: Add comprehensive error handling for production
3. **Caching**: Implement caching for BOE responses
4. **Rate Limiting**: Add rate limiting for BOE API calls
5. **Monitoring**: Add logging and monitoring for MCP interactions

## Contributing

When modifying the MCP integration:
1. Test changes with this script first
2. Update configuration files as needed
3. Document any new dependencies
4. Ensure backward compatibility

---

**Note**: This test requires an active internet connection to access the BOE API and OpenAI services.