"""
WebSocket consumers for real-time chat functionality.
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from apps.chat.services import ChatService
from apps.chat.models import ChatSession

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for streaming chat responses.
    """
    
    async def connect(self):
        """Accept WebSocket connection."""
        await self.accept()
        
        # Send welcome message
        await self.send(json.dumps({
            'type': 'connection',
            'message': 'Connected to Ovra AI Tax Assistant'
        }))
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        logger.info(f"WebSocket disconnected with code: {close_code}")
    
    async def receive(self, text_data):
        """
        Handle incoming WebSocket messages.
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'chat':
                await self.handle_chat_message(data)
            else:
                await self.send(json.dumps({
                    'type': 'error',
                    'message': f'Unknown message type: {message_type}'
                }))
                
        except json.JSONDecodeError:
            await self.send(json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            logger.error(f"Error in WebSocket receive: {str(e)}", exc_info=True)
            await self.send(json.dumps({
                'type': 'error',
                'message': 'An error occurred processing your request'
            }))
    
    async def handle_chat_message(self, data):
        """
        Handle chat messages and stream responses.
        """
        question = data.get('question')
        session_id = data.get('session_id')
        
        if not question:
            await self.send(json.dumps({
                'type': 'error',
                'message': 'Question is required'
            }))
            return
        
        # Send acknowledgment
        await self.send(json.dumps({
            'type': 'chat_start',
            'message': 'Processing your question...'
        }))
        
        try:
            # TODO: Implement streaming when OpenAI integration is complete
            # For now, send a mock streamed response
            
            # Mock streaming response
            response_parts = [
                "According to current Spanish legislation, ",
                "in response to your question: ",
                f'"{question}" ',
                "\n\nThe general VAT rate in Spain is 21%, ",
                "as established by article 21 of the VAT Law.",
                "\n\nThis information is updated according to current regulations."
            ]
            
            # Stream each part
            for i, part in enumerate(response_parts):
                await self.send(json.dumps({
                    'type': 'chat_stream',
                    'content': part,
                    'index': i
                }))
                # Small delay to simulate streaming
                import asyncio
                await asyncio.sleep(0.1)
            
            # Send completion message
            await self.send(json.dumps({
                'type': 'chat_complete',
                'message': 'Response completed',
                'citations': [{
                    "law": "Ley del IVA",
                    "article_num": "21",
                    "source_url": "https://www.boe.es/buscar/act.php?id=BOE-A-1992-28740#a21"
                }]
            }))
            
        except Exception as e:
            logger.error(f"Error in chat message handling: {str(e)}", exc_info=True)
            await self.send(json.dumps({
                'type': 'error',
                'message': 'Failed to process your question'
            })) 