const express = require('express');
const { PrismaClient } = require('@prisma/client');

const router = express.Router();
const prisma = new PrismaClient();

// Dashboard
router.get('/', async (req, res) => {
  try {
    const stats = {
      userCount: await prisma.user.count(),
      chatSessionCount: await prisma.chatSession.count(),
      messageCount: await prisma.chatMessage.count(),
      marketingEmailCount: await prisma.marketingEmail.count(),
      widgetSessionCount: await prisma.widgetSession.count(),
      widgetMessageCount: await prisma.widgetMessage.count(),
    };
    
    res.render('admin/dashboard', {
      title: 'Dashboard',
      user: req.session.adminUser,
      stats
    });
  } catch (error) {
    console.error('Dashboard error:', error);
    res.status(500).send('Dashboard error');
  }
});

module.exports = router;