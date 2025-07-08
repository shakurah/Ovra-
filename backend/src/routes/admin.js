const express = require('express');
const bcrypt = require('bcryptjs');
const { PrismaClient } = require('@prisma/client');
const { adminAuthMiddleware } = require('../middleware/adminAuth');
const session = require('express-session');
const path = require('path');

const router = express.Router();
const prisma = new PrismaClient();

// Set view engine and views directory
router.set('view engine', 'pug');
router.set('views', path.join(__dirname, '../views/admin'));

// Serve static files from AdminLTE
router.use('/assets', express.static(path.join(__dirname, '../../node_modules/adminlte')));

// Session middleware for admin
router.use(session({
  secret: process.env.ADMIN_SESSION_SECRET || 'admin-secret-key-change-in-production',
  resave: false,
  saveUninitialized: false,
  cookie: {
    secure: process.env.NODE_ENV === 'production',
    httpOnly: true,
    maxAge: 24 * 60 * 60 * 1000 // 24 hours
  }
}));

// Admin authentication middleware
const requireAdmin = (req, res, next) => {
  if (req.session.adminUser) {
    next();
  } else {
    res.redirect('/admin/login');
  }
};

// Login form
router.get('/login', (req, res) => {
  res.render('login', { 
    title: 'Admin Login',
    error: req.query.error
  });
});

// Login handler
router.post('/login', async (req, res) => {
  try {
    const { email, password } = req.body;
    const user = await adminAuthMiddleware(email, password);
    
    if (user) {
      req.session.adminUser = user;
      res.redirect('/admin/dashboard');
    } else {
      res.redirect('/admin/login?error=Invalid credentials');
    }
  } catch (error) {
    console.error('Login error:', error);
    res.redirect('/admin/login?error=Login failed');
  }
});

// Dashboard
router.get('/dashboard', requireAdmin, async (req, res) => {
  try {
    const stats = {
      userCount: await prisma.user.count(),
      chatSessionCount: await prisma.chatSession.count(),
      messageCount: await prisma.chatMessage.count(),
      marketingEmailCount: await prisma.marketingEmail.count(),
      widgetSessionCount: await prisma.widgetSession.count(),
      widgetMessageCount: await prisma.widgetMessage.count(),
    };
    
    res.render('dashboard', {
      title: 'Dashboard',
      user: req.session.adminUser,
      stats
    });
  } catch (error) {
    console.error('Dashboard error:', error);
    res.status(500).send('Dashboard error');
  }
});

// Users management
router.get('/users', requireAdmin, async (req, res) => {
  try {
    const users = await prisma.user.findMany({
      orderBy: { createdAt: 'desc' }
    });
    
    res.render('users', {
      title: 'Users Management',
      user: req.session.adminUser,
      users
    });
  } catch (error) {
    console.error('Users error:', error);
    res.status(500).send('Users error');
  }
});

// Edit user
router.get('/users/:id/edit', requireAdmin, async (req, res) => {
  try {
    const user = await prisma.user.findUnique({
      where: { id: req.params.id }
    });
    
    if (!user) {
      return res.redirect('/admin/users');
    }
    
    res.render('user-edit', {
      title: 'Edit User',
      user: req.session.adminUser,
      editUser: user
    });
  } catch (error) {
    console.error('Edit user error:', error);
    res.redirect('/admin/users');
  }
});

// Update user
router.post('/users/:id/edit', requireAdmin, async (req, res) => {
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
router.get('/users/:id/delete', requireAdmin, async (req, res) => {
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

// Chat sessions
router.get('/sessions', requireAdmin, async (req, res) => {
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
    
    res.render('sessions', {
      title: 'Chat Sessions',
      user: req.session.adminUser,
      sessions
    });
  } catch (error) {
    console.error('Sessions error:', error);
    res.status(500).send('Sessions error');
  }
});

// Session details
router.get('/sessions/:id', requireAdmin, async (req, res) => {
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
    
    res.render('session-detail', {
      title: 'Session Details',
      user: req.session.adminUser,
      session
    });
  } catch (error) {
    console.error('Session detail error:', error);
    res.redirect('/admin/sessions');
  }
});

// Marketing emails
router.get('/marketing', requireAdmin, async (req, res) => {
  try {
    const emails = await prisma.marketingEmail.findMany({
      orderBy: { createdAt: 'desc' }
    });
    
    res.render('marketing', {
      title: 'Marketing Emails',
      user: req.session.adminUser,
      emails
    });
  } catch (error) {
    console.error('Marketing error:', error);
    res.status(500).send('Marketing error');
  }
});

// Logout
router.get('/logout', (req, res) => {
  req.session.destroy();
  res.redirect('/admin/login');
});

// Root redirect
router.get('/', (req, res) => {
  res.redirect('/admin/dashboard');
});

module.exports = router;