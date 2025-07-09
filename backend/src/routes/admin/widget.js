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

// View widget session
router.get('/sessions/:id', async (req, res) => {
  try {
    const session = await prisma.widgetSession.findUnique({
      where: { id: req.params.id },
      include: {
        marketingEmail: {
          select: { email: true }
        },
        messages: {
          orderBy: { createdAt: 'asc' }
        }
      }
    });
    
    if (!session) {
      return res.redirect('/admin/widget-sessions');
    }
    
    res.render('admin/widget-session-detail', {
      title: 'Widget Session Details',
      user: req.session.adminUser,
      session
    });
  } catch (error) {
    console.error('View widget session error:', error);
    res.redirect('/admin/widget/sessions');
  }
});

// Edit widget session form
router.get('/sessions/:id/edit', async (req, res) => {
  try {
    const session = await prisma.widgetSession.findUnique({
      where: { id: req.params.id },
      include: {
        marketingEmail: {
          select: { email: true }
        }
      }
    });
    
    if (!session) {
      return res.redirect('/admin/widget-sessions');
    }
    
    res.render('admin/widget-session-edit', {
      title: 'Edit Widget Session',
      user: req.session.adminUser,
      session
    });
  } catch (error) {
    console.error('Edit widget session error:', error);
    res.redirect('/admin/widget/sessions');
  }
});

// Update widget session
router.post('/sessions/:id/edit', async (req, res) => {
  try {
    const { isActive } = req.body;
    
    await prisma.widgetSession.update({
      where: { id: req.params.id },
      data: {
        isActive: isActive === 'on'
      }
    });
    
    res.redirect('/admin/widget/sessions');
  } catch (error) {
    console.error('Update widget session error:', error);
    res.redirect('/admin/widget/sessions');
  }
});

// Delete widget session
router.get('/sessions/:id/delete', async (req, res) => {
  try {
    await prisma.widgetSession.delete({
      where: { id: req.params.id }
    });
    
    res.redirect('/admin/widget/sessions');
  } catch (error) {
    console.error('Delete widget session error:', error);
    res.redirect('/admin/widget/sessions');
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

// View widget message
router.get('/messages/:id', async (req, res) => {
  try {
    const message = await prisma.widgetMessage.findUnique({
      where: { id: req.params.id },
      include: {
        session: {
          include: {
            marketingEmail: {
              select: { email: true }
            }
          }
        }
      }
    });
    
    if (!message) {
      return res.redirect('/admin/widget-messages');
    }
    
    res.render('admin/widget-message-detail', {
      title: 'Widget Message Details',
      user: req.session.adminUser,
      message
    });
  } catch (error) {
    console.error('View widget message error:', error);
    res.redirect('/admin/widget/messages');
  }
});

// Edit widget message form
router.get('/messages/:id/edit', async (req, res) => {
  try {
    const message = await prisma.widgetMessage.findUnique({
      where: { id: req.params.id },
      include: {
        session: {
          include: {
            marketingEmail: {
              select: { email: true }
            }
          }
        }
      }
    });
    
    if (!message) {
      return res.redirect('/admin/widget-messages');
    }
    
    res.render('admin/widget-message-edit', {
      title: 'Edit Widget Message',
      user: req.session.adminUser,
      message
    });
  } catch (error) {
    console.error('Edit widget message error:', error);
    res.redirect('/admin/widget/messages');
  }
});

// Update widget message
router.post('/messages/:id/edit', async (req, res) => {
  try {
    const { content } = req.body;
    
    await prisma.widgetMessage.update({
      where: { id: req.params.id },
      data: { content }
    });
    
    res.redirect('/admin/widget/messages');
  } catch (error) {
    console.error('Update widget message error:', error);
    res.redirect('/admin/widget/messages');
  }
});

// Delete widget message
router.get('/messages/:id/delete', async (req, res) => {
  try {
    await prisma.widgetMessage.delete({
      where: { id: req.params.id }
    });
    
    res.redirect('/admin/widget/messages');
  } catch (error) {
    console.error('Delete widget message error:', error);
    res.redirect('/admin/widget/messages');
  }
});

module.exports = router;