const express = require('express');
const { adminAuthMiddleware } = require('../../middleware/adminAuth');

const router = express.Router();

// Admin authentication middleware
const requireAdmin = (req, res, next) => {
  console.log('Session check:', req.session.adminUser ? 'authenticated' : 'not authenticated');
  if (req.session.adminUser) {
    next();
  } else {
    res.redirect('/admin/login');
  }
};

// Login form
router.get('/login', (req, res) => {
  res.render('admin/login', { 
    title: 'Admin Login',
    error: req.query.error
  });
});

// Login handler
router.post('/login', async (req, res) => {
  try {
    const { email, password } = req.body;
    console.log('Login attempt:', { email, password: password ? '[REDACTED]' : 'empty' });
    
    const user = await adminAuthMiddleware(email, password);
    console.log('Auth result:', user ? 'success' : 'failed');
    
    if (user) {
      req.session.adminUser = user;
      console.log('Session set:', req.session.adminUser ? 'success' : 'failed');
      
      // Save session explicitly
      req.session.save((err) => {
        if (err) {
          console.error('Session save error:', err);
        } else {
          console.log('Session saved successfully');
        }
        res.redirect('/admin/dashboard');
      });
    } else {
      res.redirect('/admin/login?error=Invalid credentials');
    }
  } catch (error) {
    console.error('Login error:', error);
    res.redirect('/admin/login?error=Login failed');
  }
});

// Logout
router.get('/logout', (req, res) => {
  req.session.destroy();
  res.redirect('/admin/login');
});

module.exports = { router, requireAdmin };