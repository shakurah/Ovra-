# BOE MCP Chat Integration

## Overview

This document describes the complete integration of the BOE (Boletín Oficial del Estado) MCP server with the chat service. The integration provides real-time access to Spanish legal information through the chat interface.

## Integration Flow

### 1. User Query Processing

```
User Query → Chat Endpoint → MCP Agent Service → BOE MCP Server
```

### 2. Response Flow

```
BOE Raw Data → Stream to User → OpenAI Summary → Stream Summary → Complete
```

### 3. Detailed Flow

1. **User sends query** via `/api/v1/chat/stream/` endpoint
2. **Legal query detection**: System checks if query needs legal information
3. **BOE MCP query**: If legal, formats query for BOE MCP server
4. **Stream BOE response**: Raw BOE data is streamed to user first
5. **Generate summary**: OpenAI analyzes BOE data and creates summary
6. **Stream summary**: Summary is streamed to user after BOE data
7. **Complete response**: User receives both raw data and analysis

## Key Components

### 1. MCP Agent Service (`app/services/mcp_agent_service.py`)

**Purpose**: Handles BOE MCP server communication and response processing

**Key Methods**:
- `_is_legal_query()`: Detects if query needs legal information
- `_format_boe_query()`: Formats user query for BOE MCP server
- `_format_summarization_prompt()`: Creates prompt for OpenAI summary
- `query_boe_and_summarize()`: Main method that orchestrates the flow

**Legal Keywords Detected**:
```python
[
    'ley', 'law', 'legal', 'normativa', 'regulation',
    'boe', 'boletín oficial', 'decreto', 'decree',
    'impuesto', 'tax', 'fiscal', 'tributario', 'iva', 'vat',
    'irpf', 'income tax', 'artista', 'artist', 'cultural',
    'profesional', 'freelance', 'autónomo', 'self-employed',
    'derechos de autor', 'copyright', 'propiedad intelectual',
    'intellectual property', 'facturación', 'billing', 'invoice'
]
```

### 2. Chat Endpoint (`app/api/v1/endpoints/chat.py`)

**Purpose**: Provides streaming chat interface with MCP integration

**Key Features**:
- Automatic MCP service detection
- Fallback to regular chat if MCP unavailable
- Server-Sent Events (SSE) streaming
- Comprehensive logging and error handling

### 3. Response Format

The integration provides a structured response format:

```markdown
## 📋 Información del BOE (Boletín Oficial del Estado)

[Raw BOE data streamed in chunks]

---

## 🤖 Resumen y Análisis

[OpenAI-generated summary and analysis]
```

## Configuration

### Environment Variables

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini

# BOE MCP Configuration
BOE_API_BASE=https://www.boe.es/buscar/
```

### MCP Configuration (`boe_mcp_config.json`)

```json
{
  "mcpServers": {
    "boe_mcp": {
      "command": "uvx",
      "args": ["boe_mcp"]
    }
  }
}
```

## API Usage

### Streaming Chat Endpoint

**Endpoint**: `POST /api/v1/chat/stream/`

**Request**:
```json
{
  "message": "¿Cuáles son las tarifas de impuestos sobre salarios para 2025?",
  "conversation_id": "optional_session_id",
  "model": "gpt-4o-mini",
  "temperature": 0.7,
  "max_tokens": 2000
}
```

**Response** (Server-Sent Events):
```
data: {"content": "## 📋 Información del BOE...\n\n", "conversation_id": "session_123", "is_complete": false, "mcp_used": true}

data: {"content": "[BOE content chunk]", "conversation_id": "session_123", "is_complete": false, "mcp_used": true}

data: {"content": "\n\n---\n\n## 🤖 Resumen y Análisis\n\n", "conversation_id": "session_123", "is_complete": false, "mcp_used": true}

data: {"content": "[Summary chunk]", "conversation_id": "session_123", "is_complete": true, "mcp_used": true}

data: [DONE]
```

### Health Check

**Endpoint**: `GET /api/v1/chat/health/`

**Response**:
```json
{
  "status": "healthy",
  "service": "chat",
  "model": "gpt-4o-mini",
  "mcp_boe_integration": "available"
}
```

## Testing

### 1. Unit Tests

```bash
# Test MCP integration
python3 test_mcp_boe_integration.py

# Test chat demo
python3 demo_chat_integration.py
```

### 2. Endpoint Testing

```bash
# Test streaming endpoint
python3 test_chat_endpoint.py
```

### 3. Manual Testing

```bash
# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Test with curl
curl -X POST "http://localhost:8000/api/v1/chat/stream/" \
  -H "Authorization: Bearer your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "¿Cuáles son las deducciones fiscales para artistas en 2024?",
    "conversation_id": "test_session"
  }'
```

## Error Handling

### 1. MCP Service Unavailable

```
**Aviso**: Servicio de consulta legal temporal no disponible. 
Respondiendo con conocimiento general...
```

### 2. BOE Query Failed

```
**Aviso**: Error al consultar la base de datos legal. 
Respondiendo con conocimiento general...
```

### 3. No BOE Data Found

```
**Información**: No se encontró información específica en el BOE 
para esta consulta. Te ayudo con conocimiento general sobre el tema.
```

### 4. Non-Legal Query

```
**Información**: Esta consulta no requiere acceso al BOE. 
Respondiendo con conocimiento general...
```

## Performance Considerations

### 1. Streaming Optimization

- **BOE chunks**: 200 characters with smart breaking points
- **Summary chunks**: 50 characters with smart breaking points
- **Buffer management**: Prevents memory issues with large responses

### 2. Timeout Handling

- **MCP queries**: 30-second timeout
- **OpenAI summarization**: 60-second timeout
- **Graceful fallback**: Regular chat service if MCP fails

### 3. Caching Recommendations

- Cache frequently asked BOE queries
- Implement Redis for session management
- Cache OpenAI summaries for identical BOE responses

## Security

### 1. API Key Management

- OpenAI API key stored in environment variables
- No API keys logged or exposed in responses
- Secure key rotation procedures

### 2. Input Validation

- Query length limits (max 1000 characters)
- Content filtering for inappropriate queries
- Rate limiting per user/session

### 3. Data Privacy

- No user queries stored permanently
- BOE data is public information
- Compliance with GDPR for EU users

## Monitoring and Logging

### 1. Key Metrics

- MCP service availability
- Query processing time
- Success/failure rates
- User satisfaction ratings

### 2. Log Levels

```python
# Info: Normal operations
logger.info(f"Querying BOE MCP for: {request.message[:100]}...")

# Warning: Fallback scenarios
logger.warning("MCP service unavailable, using fallback")

# Error: Failures
logger.error(f"BOE MCP query failed: {error}")
```

### 3. Health Monitoring

- `/api/v1/chat/health/` endpoint
- MCP service status checks
- OpenAI API connectivity

## Deployment

### 1. Dependencies

```bash
# Install MCP dependencies
pip install mcp-use langchain-openai python-dotenv aiofiles

# Install BOE MCP server
uvx install boe_mcp
```

### 2. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Configure API keys
vim .env
```

### 3. Service Start

```bash
# Development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Troubleshooting

### 1. Common Issues

**MCP Service Not Starting**:
```bash
# Check uvx installation
uvx --version

# Reinstall BOE MCP
uvx install --force boe_mcp
```

**OpenAI API Errors**:
```bash
# Check API key
echo $OPENAI_API_KEY

# Test API connectivity
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models
```

**Streaming Issues**:
- Check client SSE support
- Verify Content-Type headers
- Test with curl for debugging

### 2. Debug Mode

```python
# Enable debug logging
import logging
logging.getLogger("mcp_agent").setLevel(logging.DEBUG)
```

## Future Enhancements

### 1. Planned Features

- **Multi-language support**: English, Catalan, Basque
- **Document attachments**: PDF analysis integration
- **Voice queries**: Speech-to-text integration
- **Legal citations**: Automatic reference formatting

### 2. Performance Improvements

- **Parallel processing**: Simultaneous BOE query and summary generation
- **Smart caching**: ML-based cache invalidation
- **Load balancing**: Multiple MCP server instances

### 3. Integration Expansions

- **Other legal databases**: EUR-Lex, national courts
- **Document management**: Legal document storage
- **Workflow automation**: Legal process automation

## Support

For technical support or questions about the BOE MCP integration:

1. Check the logs in `/var/log/ovra_ai/`
2. Review the health endpoint status
3. Test individual components with provided scripts
4. Consult this documentation for configuration details

---

**Last Updated**: January 2025  
**Version**: 1.0.0  
**Maintainer**: OVRA AI Development Team