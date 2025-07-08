const { PrismaClient } = require('@prisma/client');
const OpenAIService = require('./openaiService');
const BoeSearchService = require('./boeSearchService');

const prisma = new PrismaClient();

class WidgetService {
  static async registerEmail(email, sourceWebsite, privacyAccepted, termsAccepted) {
    try {
      // Check if email already exists
      let marketingEmail = await prisma.marketingEmail.findUnique({
        where: { email }
      });

      if (marketingEmail) {
        // Update existing email record
        marketingEmail = await prisma.marketingEmail.update({
          where: { email },
          data: {
            sourceWebsite,
            privacyAccepted,
            termsAccepted,
            isActive: true,
            updatedAt: new Date()
          }
        });
      } else {
        // Create new email record
        marketingEmail = await prisma.marketingEmail.create({
          data: {
            email,
            sourceWebsite,
            privacyAccepted,
            termsAccepted,
            isActive: true
          }
        });
      }

      return marketingEmail;
    } catch (error) {
      console.error('Error registering email:', error);
      throw error;
    }
  }

  static async getOrCreateSession(email, sessionId = null) {
    try {
      // First get the marketing email
      const marketingEmail = await prisma.marketingEmail.findUnique({
        where: { email }
      });

      if (!marketingEmail) {
        throw new Error('Email not registered');
      }

      let session;

      if (sessionId) {
        // Try to find existing session
        session = await prisma.widgetSession.findFirst({
          where: {
            id: sessionId,
            marketingEmailId: marketingEmail.id,
            isActive: true
          }
        });
      }

      if (!session) {
        // Create new session
        session = await prisma.widgetSession.create({
          data: {
            marketingEmailId: marketingEmail.id,
            isActive: true
          }
        });
      }

      return session;
    } catch (error) {
      console.error('Error getting or creating session:', error);
      throw error;
    }
  }

  static async sendMessage(email, question, sessionId = null, sourceWebsite = null) {
    try {
      // Get or create session
      const session = await this.getOrCreateSession(email, sessionId);

      // Save user message
      const userMessage = await prisma.widgetMessage.create({
        data: {
          sessionId: session.id,
          role: 'user',
          content: question
        }
      });

      // Get chat history for context
      const messages = await prisma.widgetMessage.findMany({
        where: {
          sessionId: session.id
        },
        orderBy: {
          createdAt: 'asc'
        },
        take: 20 // Last 20 messages for context
      });

      // Prepare conversation context
      const conversationHistory = messages.map(msg => ({
        role: msg.role,
        content: msg.content
      }));

      // Search BOE for relevant information
      const boeResults = await BoeSearchService.search(question);

      // Generate response using OpenAI
      const response = await OpenAIService.generateResponse(
        question,
        conversationHistory,
        boeResults
      );

      // Save assistant message
      const assistantMessage = await prisma.widgetMessage.create({
        data: {
          sessionId: session.id,
          role: 'assistant',
          content: response.answer,
          metadata: JSON.stringify({
            citations: response.citations || [],
            sources: response.sources || []
          })
        }
      });

      return {
        chat_id: assistantMessage.id,
        session_id: session.id,
        answer: response.answer,
        citations: response.citations || [],
        sources: response.sources || []
      };
    } catch (error) {
      console.error('Error sending message:', error);
      throw error;
    }
  }

  static async getSessionMessages(sessionId) {
    try {
      const messages = await prisma.widgetMessage.findMany({
        where: {
          sessionId: sessionId
        },
        orderBy: {
          createdAt: 'asc'
        }
      });

      return messages.map(msg => ({
        id: msg.id,
        role: msg.role,
        content: msg.content,
        metadata: msg.metadata ? JSON.parse(msg.metadata) : null,
        timestamp: msg.createdAt
      }));
    } catch (error) {
      console.error('Error getting session messages:', error);
      throw error;
    }
  }

  static async getEmailSessions(email) {
    try {
      const marketingEmail = await prisma.marketingEmail.findUnique({
        where: { email },
        include: {
          sessions: {
            where: { isActive: true },
            orderBy: { createdAt: 'desc' }
          }
        }
      });

      return marketingEmail ? marketingEmail.sessions : [];
    } catch (error) {
      console.error('Error getting email sessions:', error);
      throw error;
    }
  }
}

module.exports = WidgetService;