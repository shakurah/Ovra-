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