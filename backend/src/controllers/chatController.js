const { validationResult } = require('express-validator');
const ChatService = require('../services/chatService');

class ChatController {
  static async createSession(req, res, next) {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
      }

      const { title } = req.body;
      const session = await ChatService.createSession(req.user.id, title);
      
      res.status(201).json({
        message: 'Chat session created successfully',
        session,
      });
    } catch (error) {
      next(error);
    }
  }

  static async getSessions(req, res, next) {
    try {
      const sessions = await ChatService.getUserSessions(req.user.id);
      res.json({ sessions });
    } catch (error) {
      next(error);
    }
  }

  static async getSession(req, res, next) {
    try {
      const { sessionId } = req.params;
      const session = await ChatService.getSessionById(sessionId);
      
      if (!session) {
        return res.status(404).json({ error: 'Session not found' });
      }

      if (session.userId !== req.user.id) {
        return res.status(403).json({ error: 'Access denied' });
      }

      const messages = await ChatService.getSessionMessages(sessionId);
      
      res.json({
        session,
        messages,
      });
    } catch (error) {
      next(error);
    }
  }

  static async updateSession(req, res, next) {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
      }

      const { sessionId } = req.params;
      const { title } = req.body;
      
      const session = await ChatService.getSessionById(sessionId);
      if (!session) {
        return res.status(404).json({ error: 'Session not found' });
      }

      if (session.userId !== req.user.id) {
        return res.status(403).json({ error: 'Access denied' });
      }

      const updatedSession = await ChatService.updateSessionTitle(sessionId, title);
      
      res.json({
        message: 'Session updated successfully',
        session: updatedSession,
      });
    } catch (error) {
      next(error);
    }
  }

  static async deleteSession(req, res, next) {
    try {
      const { sessionId } = req.params;
      const session = await ChatService.getSessionById(sessionId);
      
      if (!session) {
        return res.status(404).json({ error: 'Session not found' });
      }

      if (session.userId !== req.user.id) {
        return res.status(403).json({ error: 'Access denied' });
      }

      await ChatService.deleteSession(sessionId);
      
      res.json({ message: 'Session deleted successfully' });
    } catch (error) {
      next(error);
    }
  }

  static async sendMessage(req, res, next) {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
      }

      const { sessionId } = req.params;
      const { message, email, source_website } = req.body;
      
      // Check if this is a widget request (has email but no user auth)
      if (email && !req.user) {
        // Handle widget chat through widget service
        const WidgetService = require('../services/widgetService');
        try {
          const widgetResponse = await WidgetService.sendMessage(
            email,
            message,
            req.body.conversation_id,
            source_website
          );
          
          return res.json({
            message: {
              id: widgetResponse.chat_id,
              role: 'assistant',
              content: widgetResponse.answer,
              timestamp: new Date().toISOString(),
              metadata: {
                legal_references: widgetResponse.citations || []
              }
            },
            conversation_id: widgetResponse.session_id,
            usage: null
          });
        } catch (widgetError) {
          if (widgetError.message === 'Email not registered') {
            return res.status(400).json({ error: 'Email not registered' });
          }
          throw widgetError;
        }
      }

      // Regular authenticated user chat
      const session = await ChatService.getSessionById(sessionId);
      if (!session) {
        return res.status(404).json({ error: 'Session not found' });
      }

      if (session.userId !== req.user.id) {
        return res.status(403).json({ error: 'Access denied' });
      }

      const response = await ChatService.sendMessage(sessionId, message);
      
      res.json({
        message: 'Message sent successfully',
        response,
      });
    } catch (error) {
      next(error);
    }
  }

  static async streamMessage(req, res, next) {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
      }

      const { sessionId } = req.params;
      const { message, conversation_id } = req.body;
      
      // Use sessionId from params or conversation_id from body
      const actualSessionId = sessionId || conversation_id;
      
      let session = null;
      if (actualSessionId && actualSessionId !== 'undefined') {
        session = await ChatService.getSessionById(actualSessionId);
        if (!session) {
          return res.status(404).json({ error: 'Session not found' });
        }
        if (session.userId !== req.user.id) {
          return res.status(403).json({ error: 'Access denied' });
        }
      } else {
        // Create new session if no sessionId provided
        session = await ChatService.createSession(req.user.id, 'New Chat');
      }

      // Set up SSE headers
      res.writeHead(200, {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Cache-Control'
      });

      // Send initial connection message
      res.write('data: {"type": "connected"}\n\n');

      try {
        // Stream the response
        for await (const chunk of ChatService.streamMessage(session.id, message)) {
          const data = JSON.stringify({
            type: 'chunk',
            content: chunk,
            conversation_id: session.id
          });
          res.write(`data: ${data}\n\n`);
        }

        // Send completion message
        res.write(`data: ${JSON.stringify({
          type: 'completed',
          conversation_id: session.id,
          is_complete: true
        })}\n\n`);
        res.end();
      } catch (streamError) {
        const errorData = JSON.stringify({
          type: 'error',
          error: streamError.message
        });
        res.write(`data: ${errorData}\n\n`);
        res.end();
      }
    } catch (error) {
      next(error);
    }
  }
}

module.exports = ChatController;