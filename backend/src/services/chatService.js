const ChatSession = require('../models/ChatSession');
const ChatMessage = require('../models/ChatMessage');
const openaiService = require('./openaiService');
const boeSearchService = require('./boeSearchService');

class ChatService {
  static async createSession(userId, title) {
    return await ChatSession.create({ userId, title });
  }

  static async getUserSessions(userId) {
    return await ChatSession.findByUserId(userId);
  }

  static async getSessionById(sessionId) {
    return await ChatSession.findById(sessionId);
  }

  static async updateSessionTitle(sessionId, title) {
    return await ChatSession.updateTitle(sessionId, title);
  }

  static async deleteSession(sessionId) {
    await ChatMessage.deleteBySessionId(sessionId);
    await ChatSession.delete(sessionId);
  }

  static async addMessage(sessionId, role, content) {
    return await ChatMessage.create({ sessionId, role, content });
  }

  static async getSessionMessages(sessionId) {
    return await ChatMessage.findBySessionId(sessionId);
  }

  static async sendMessage(sessionId, userMessage) {
    // Add user message
    await this.addMessage(sessionId, 'user', userMessage);
    
    try {
      // Enhance search query with OpenAI
      const enhancedTerms = await openaiService.enhanceSearchQuery(userMessage);
      
      // Perform BOE search with enhanced terms
      const boeResults = await boeSearchService.performMultipleSearches(userMessage, enhancedTerms);
      const formattedResults = boeSearchService.formatResultsForAI(boeResults);
      
      // Process message through OpenAI service with BOE results
      const aiResponse = await openaiService.processMessage(userMessage, formattedResults);
      
      // Add AI response
      const assistantMessage = await this.addMessage(sessionId, 'assistant', aiResponse);
      
      return assistantMessage;
    } catch (error) {
      console.error('Error in BOE search, falling back to standard response:', error);
      
      // Fallback to standard OpenAI response if BOE search fails
      const aiResponse = await openaiService.processMessage(userMessage);
      const assistantMessage = await this.addMessage(sessionId, 'assistant', aiResponse);
      
      return assistantMessage;
    }
  }

  static async *streamMessage(sessionId, userMessage) {
    // Add user message
    await this.addMessage(sessionId, 'user', userMessage);
    
    let fullResponse = '';
    
    try {
      // Enhance search query with OpenAI
      const enhancedTerms = await openaiService.enhanceSearchQuery(userMessage);
      
      // Perform BOE search with enhanced terms
      const boeResults = await boeSearchService.performMultipleSearches(userMessage, enhancedTerms);
      const formattedResults = boeSearchService.formatResultsForAI(boeResults);
      
      // Stream response from OpenAI service with BOE results
      for await (const chunk of openaiService.streamMessage(userMessage, formattedResults)) {
        fullResponse += chunk;
        yield chunk;
      }
    } catch (error) {
      console.error('Error in BOE search, falling back to standard streaming:', error);
      
      // Fallback to standard OpenAI streaming if BOE search fails
      for await (const chunk of openaiService.streamMessage(userMessage)) {
        fullResponse += chunk;
        yield chunk;
      }
    }
    
    // Add complete AI response to database
    await this.addMessage(sessionId, 'assistant', fullResponse);
  }

  static async generateAIResponse(userMessage) {
    // Placeholder AI response - replace with actual AI service
    const responses = [
      "I understand your message. How can I help you further?",
      "That's an interesting point. Let me think about that...",
      "I'd be happy to help you with that question.",
      "Could you provide more details about what you're looking for?",
      "Based on what you've shared, here's my response..."
    ];
    
    return responses[Math.floor(Math.random() * responses.length)];
  }
}

module.exports = ChatService;