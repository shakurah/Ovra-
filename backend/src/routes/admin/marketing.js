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

// View marketing email
router.get('/:id', async (req, res) => {
  try {
    const email = await prisma.marketingEmail.findUnique({
      where: { id: req.params.id }
    });
    
    if (!email) {
      return res.redirect('/admin/marketing');
    }
    
    res.render('admin/marketing-detail', {
      title: 'Marketing Email Details',
      user: req.session.adminUser,
      email
    });
  } catch (error) {
    console.error('View marketing email error:', error);
    res.redirect('/admin/marketing');
  }
});

// Edit marketing email form
router.get('/:id/edit', async (req, res) => {
  try {
    const email = await prisma.marketingEmail.findUnique({
      where: { id: req.params.id }
    });
    
    if (!email) {
      return res.redirect('/admin/marketing');
    }
    
    res.render('admin/marketing-edit', {
      title: 'Edit Marketing Email',
      user: req.session.adminUser,
      email
    });
  } catch (error) {
    console.error('Edit marketing email error:', error);
    res.redirect('/admin/marketing');
  }
});

// Update marketing email
router.post('/:id/edit', async (req, res) => {
  try {
    const { email, sourceWebsite, privacyAccepted, termsAccepted, isActive } = req.body;
    
    await prisma.marketingEmail.update({
      where: { id: req.params.id },
      data: {
        email,
        sourceWebsite: sourceWebsite || null,
        privacyAccepted: privacyAccepted === 'on',
        termsAccepted: termsAccepted === 'on',
        isActive: isActive === 'on'
      }
    });
    
    res.redirect('/admin/marketing');
  } catch (error) {
    console.error('Update marketing email error:', error);
    res.redirect('/admin/marketing');
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