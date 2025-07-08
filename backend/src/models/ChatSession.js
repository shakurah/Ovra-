const prisma = require('../config/prisma');

class ChatSession {
  static async create({ userId, title = 'New Chat' }) {
    return await prisma.chatSession.create({
      data: {
        userId,
        title,
      },
      select: {
        id: true,
        userId: true,
        title: true,
        isActive: true,
        createdAt: true,
        updatedAt: true,
      },
    });
  }

  static async findByUserId(userId) {
    return await prisma.chatSession.findMany({
      where: { 
        userId,
        isActive: true 
      },
      select: {
        id: true,
        userId: true,
        title: true,
        isActive: true,
        createdAt: true,
        updatedAt: true,
      },
      orderBy: {
        updatedAt: 'desc',
      },
    });
  }

  static async findById(id) {
    return await prisma.chatSession.findUnique({
      where: { id },
      select: {
        id: true,
        userId: true,
        title: true,
        isActive: true,
        createdAt: true,
        updatedAt: true,
      },
    });
  }

  static async updateTitle(id, title) {
    return await prisma.chatSession.update({
      where: { id },
      data: { title },
      select: {
        id: true,
        userId: true,
        title: true,
        isActive: true,
        createdAt: true,
        updatedAt: true,
      },
    });
  }

  static async delete(id) {
    return await prisma.chatSession.update({
      where: { id },
      data: { isActive: false },
    });
  }
}

module.exports = ChatSession;