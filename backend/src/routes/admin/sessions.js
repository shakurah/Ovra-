const express = require('express');
const { PrismaClient } = require('@prisma/client');

const router = express.Router();
const prisma = new PrismaClient();

// List sessions
router.get('/', async (req, res) => {
  try {
    const sessions = await prisma.chatSession.findMany({
      include: {
        user: {
          select: { email: true }
        }
      },
      orderBy: { createdAt: 'desc' },
      take: 100
    });
    
    res.render('admin/sessions', {
      title: 'Chat Sessions',
      user: req.session.adminUser,
      sessions
    });
  } catch (error) {
    console.error('Sessions error:', error);
    res.status(500).send('Sessions error');
  }
});

// View session
router.get('/:id', async (req, res) => {
  try {
    const session = await prisma.chatSession.findUnique({
      where: { id: req.params.id },
      include: {
        user: {
          select: { email: true, firstName: true, lastName: true }
        },
        messages: {
          orderBy: { createdAt: 'asc' }
        }
      }
    });
    
    if (!session) {
      return res.redirect('/admin/sessions');
    }
    
    res.render('admin/session-detail', {
      title: 'Session Details',
      user: req.session.adminUser,
      session
    });
  } catch (error) {
    console.error('Session detail error:', error);
    res.redirect('/admin/sessions');
  }
});

// Delete session
router.get('/:id/delete', async (req, res) => {
  try {
    await prisma.chatSession.delete({
      where: { id: req.params.id }
    });
    
    res.redirect('/admin/sessions');
  } catch (error) {
    console.error('Delete session error:', error);
    res.redirect('/admin/sessions');
  }
});

module.exports = router;