const express = require('express');
const { PrismaClient } = require('@prisma/client');

const router = express.Router();
const prisma = new PrismaClient();

// List messages
router.get('/', async (req, res) => {
  try {
    const messages = await prisma.chatMessage.findMany({
      orderBy: { createdAt: 'desc' },
      take: 100
    });
    
    res.render('admin/messages', {
      title: 'Chat Messages',
      user: req.session.adminUser,
      messages
    });
  } catch (error) {
    console.error('Messages error:', error);
    res.status(500).send('Messages error');
  }
});

// View message
router.get('/:id', async (req, res) => {
  try {
    const message = await prisma.chatMessage.findUnique({
      where: { id: req.params.id },
      include: {
        session: {
          include: {
            user: {
              select: { email: true, firstName: true, lastName: true }
            }
          }
        }
      }
    });
    
    if (!message) {
      return res.redirect('/admin/messages');
    }
    
    res.render('admin/message-detail', {
      title: 'Message Details',
      user: req.session.adminUser,
      message
    });
  } catch (error) {
    console.error('View message error:', error);
    res.redirect('/admin/messages');
  }
});

// Edit message form
router.get('/:id/edit', async (req, res) => {
  try {
    const message = await prisma.chatMessage.findUnique({
      where: { id: req.params.id },
      include: {
        session: {
          include: {
            user: {
              select: { email: true, firstName: true, lastName: true }
            }
          }
        }
      }
    });
    
    if (!message) {
      return res.redirect('/admin/messages');
    }
    
    res.render('admin/message-edit', {
      title: 'Edit Message',
      user: req.session.adminUser,
      message
    });
  } catch (error) {
    console.error('Edit message error:', error);
    res.redirect('/admin/messages');
  }
});

// Update message
router.post('/:id/edit', async (req, res) => {
  try {
    const { content } = req.body;
    
    await prisma.chatMessage.update({
      where: { id: req.params.id },
      data: { content }
    });
    
    res.redirect('/admin/messages');
  } catch (error) {
    console.error('Update message error:', error);
    res.redirect('/admin/messages');
  }
});

// Delete message
router.get('/:id/delete', async (req, res) => {
  try {
    await prisma.chatMessage.delete({
      where: { id: req.params.id }
    });
    
    res.redirect('/admin/messages');
  } catch (error) {
    console.error('Delete message error:', error);
    res.redirect('/admin/messages');
  }
});

module.exports = router;