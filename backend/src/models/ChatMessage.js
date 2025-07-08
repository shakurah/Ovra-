const prisma = require('../config/prisma');

class ChatMessage {
  static async create({ sessionId, role, content }) {
    return await prisma.chatMessage.create({
      data: {
        sessionId,
        role,
        content,
      },
      select: {
        id: true,
        sessionId: true,
        role: true,
        content: true,
        createdAt: true,
      },
    });
  }

  static async findBySessionId(sessionId) {
    return await prisma.chatMessage.findMany({
      where: { sessionId },
      select: {
        id: true,
        sessionId: true,
        role: true,
        content: true,
        createdAt: true,
      },
      orderBy: {
        createdAt: 'asc',
      },
    });
  }

  static async deleteBySessionId(sessionId) {
    return await prisma.chatMessage.deleteMany({
      where: { sessionId },
    });
  }
}

module.exports = ChatMessage;