const express = require('express');
const bcrypt = require('bcryptjs');
const { PrismaClient } = require('@prisma/client');

const router = express.Router();
const prisma = new PrismaClient();

// List users
router.get('/', async (req, res) => {
  try {
    const users = await prisma.user.findMany({
      orderBy: { createdAt: 'desc' }
    });
    
    res.render('admin/users', {
      title: 'Users Management',
      user: req.session.adminUser,
      users
    });
  } catch (error) {
    console.error('Users error:', error);
    res.status(500).send('Users error');
  }
});

// Create user form
router.get('/create', (req, res) => {
  res.render('admin/user-create', {
    title: 'Create User',
    user: req.session.adminUser
  });
});

// Create user
router.post('/create', async (req, res) => {
  try {
    const { email, firstName, lastName, password, isActive, isSuperuser } = req.body;
    const passwordHash = await bcrypt.hash(password, 10);
    
    await prisma.user.create({
      data: {
        email,
        firstName: firstName || null,
        lastName: lastName || null,
        passwordHash,
        isActive: isActive === 'on',
        isSuperuser: isSuperuser === 'on'
      }
    });
    
    res.redirect('/admin/users');
  } catch (error) {
    console.error('Create user error:', error);
    res.redirect('/admin/users/create');
  }
});

// View user
router.get('/:id', async (req, res) => {
  try {
    const viewUser = await prisma.user.findUnique({
      where: { id: req.params.id }
    });
    
    if (!viewUser) {
      return res.redirect('/admin/users');
    }
    
    res.render('admin/user-detail', {
      title: 'User Details',
      user: req.session.adminUser,
      viewUser
    });
  } catch (error) {
    console.error('View user error:', error);
    res.redirect('/admin/users');
  }
});

// Edit user form
router.get('/:id/edit', async (req, res) => {
  try {
    const editUser = await prisma.user.findUnique({
      where: { id: req.params.id }
    });
    
    if (!editUser) {
      return res.redirect('/admin/users');
    }
    
    res.render('admin/user-edit', {
      title: 'Edit User',
      user: req.session.adminUser,
      editUser
    });
  } catch (error) {
    console.error('Edit user error:', error);
    res.redirect('/admin/users');
  }
});

// Update user
router.post('/:id/edit', async (req, res) => {
  try {
    const { email, firstName, lastName, isActive, isSuperuser } = req.body;
    
    await prisma.user.update({
      where: { id: req.params.id },
      data: {
        email,
        firstName: firstName || null,
        lastName: lastName || null,
        isActive: isActive === 'on',
        isSuperuser: isSuperuser === 'on'
      }
    });
    
    res.redirect('/admin/users');
  } catch (error) {
    console.error('Update user error:', error);
    res.redirect('/admin/users');
  }
});

// Delete user
router.get('/:id/delete', async (req, res) => {
  try {
    await prisma.user.delete({
      where: { id: req.params.id }
    });
    
    res.redirect('/admin/users');
  } catch (error) {
    console.error('Delete user error:', error);
    res.redirect('/admin/users');
  }
});

module.exports = router;