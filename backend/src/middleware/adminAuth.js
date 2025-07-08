const { PrismaClient } = require('@prisma/client');
const bcrypt = require('bcryptjs');

const prisma = new PrismaClient();

const adminAuthMiddleware = async (email, password) => {
  try {
    // Find user by email
    const user = await prisma.user.findUnique({
      where: { email }
    });

    if (!user) {
      return false;
    }

    // Check if user is superuser
    if (!user.isSuperuser) {
      return false;
    }

    // Check if user is active
    if (!user.isActive) {
      return false;
    }

    // Verify password
    const isValidPassword = await bcrypt.compare(password, user.passwordHash);
    if (!isValidPassword) {
      return false;
    }

    return user;
  } catch (error) {
    console.error('Admin authentication error:', error);
    return false;
  }
};

module.exports = { adminAuthMiddleware };