const express = require('express');
const { PrismaClient } = require('@prisma/client');

const router = express.Router();
const prisma = new PrismaClient();

// List widget sessions
router.get('/sessions', async (req, res) => {
  try {
    const widgetSessions = await prisma.widgetSession.findMany({
      include: {
        marketingEmail: {
          select: { email: true }
        }
      },
      orderBy: { createdAt: 'desc' },
      take: 100
    });
    
    res.render('admin/widget-sessions', {
      title: 'Widget Sessions',
      user: req.session.adminUser,
      widgetSessions
    });
  } catch (error) {
    console.error('Widget sessions error:', error);
    res.status(500).send('Widget sessions error');
  }
});

// Delete widget session
router.get('/sessions/:id/delete', async (req, res) => {
  try {
    await prisma.widgetSession.delete({
      where: { id: req.params.id }
    });
    
    res.redirect('/admin/widget-sessions');
  } catch (error) {
    console.error('Delete widget session error:', error);
    res.redirect('/admin/widget-sessions');
  }
});

// List widget messages
router.get('/messages', async (req, res) => {
  try {
    const widgetMessages = await prisma.widgetMessage.findMany({
      orderBy: { createdAt: 'desc' },
      take: 100
    });
    
    res.render('admin/widget-messages', {
      title: 'Widget Messages',
      user: req.session.adminUser,
      widgetMessages
    });
  } catch (error) {
    console.error('Widget messages error:', error);
    res.status(500).send('Widget messages error');
  }
});

// Delete widget message
router.get('/messages/:id/delete', async (req, res) => {
  try {
    await prisma.widgetMessage.delete({
      where: { id: req.params.id }
    });
    
    res.redirect('/admin/widget-messages');
  } catch (error) {
    console.error('Delete widget message error:', error);
    res.redirect('/admin/widget-messages');
  }
});

module.exports = router;