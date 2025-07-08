const express = require('express');
const session = require('express-session');
const path = require('path');
const { router: authRouter, requireAdmin } = require('./admin/auth');
const dashboardRouter = require('./admin/dashboard');
const usersRouter = require('./admin/users');
const sessionsRouter = require('./admin/sessions');
const messagesRouter = require('./admin/messages');
const marketingRouter = require('./admin/marketing');
const widgetRouter = require('./admin/widget');

const router = express.Router();

// Serve static files from AdminLTE
router.use('/assets', express.static(path.join(__dirname, '../../node_modules/adminlte')));

// Session middleware for admin
router.use(session({
  secret: process.env.ADMIN_SESSION_SECRET || 'admin-secret-key-change-in-production',
  resave: false,
  saveUninitialized: false,
  name: 'adminjs.sid',
  cookie: {
    secure: false, // Allow non-HTTPS for development
    httpOnly: true,
    maxAge: 24 * 60 * 60 * 1000, // 24 hours
    sameSite: 'lax'
  }
}));

// Auth routes (login, logout)
router.use('/', authRouter);

// Protected routes
router.use('/dashboard', requireAdmin, dashboardRouter);
router.use('/users', requireAdmin, usersRouter);
router.use('/sessions', requireAdmin, sessionsRouter);
router.use('/messages', requireAdmin, messagesRouter);
router.use('/marketing', requireAdmin, marketingRouter);
router.use('/widget-sessions', requireAdmin, widgetRouter);
router.use('/widget-messages', requireAdmin, widgetRouter);

// Root redirect
router.get('/', (req, res) => {
  res.redirect('/admin/dashboard');
});

module.exports = router;