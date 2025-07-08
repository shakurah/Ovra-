const express = require('express');
const { PrismaClient } = require('@prisma/client');

const router = express.Router();
const prisma = new PrismaClient();

// List marketing emails
router.get('/', async (req, res) => {
  try {
    const emails = await prisma.marketingEmail.findMany({
      orderBy: { createdAt: 'desc' }
    });
    
    res.render('admin/marketing', {
      title: 'Marketing Emails',
      user: req.session.adminUser,
      emails
    });
  } catch (error) {
    console.error('Marketing error:', error);
    res.status(500).send('Marketing error');
  }
});

// Delete marketing email
router.get('/:id/delete', async (req, res) => {
  try {
    await prisma.marketingEmail.delete({
      where: { id: req.params.id }
    });
    
    res.redirect('/admin/marketing');
  } catch (error) {
    console.error('Delete marketing email error:', error);
    res.redirect('/admin/marketing');
  }
});

module.exports = router;