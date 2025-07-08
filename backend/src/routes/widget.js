const express = require('express');
const { body, query } = require('express-validator');
const WidgetController = require('../controllers/widgetController');

const router = express.Router();

// Validation rules
const registerValidation = [
  body('email').isEmail().normalizeEmail(),
  body('privacy_accepted').isBoolean(),
  body('terms_accepted').isBoolean(),
  body('source_website').optional().trim(),
];

const chatValidation = [
  body('email').isEmail().normalizeEmail(),
  body('question').trim().isLength({ min: 1, max: 10000 }),
  body('session_id').optional().isUUID(),
  body('source_website').optional().trim(),
];

const getMessagesValidation = [
  // sessionId is validated in controller
];

const getSessionsValidation = [
  query('email').isEmail().normalizeEmail(),
];

// Routes
router.post('/register/', registerValidation, WidgetController.register);
router.post('/chat/', chatValidation, WidgetController.chat);
router.get('/messages/:sessionId', getMessagesValidation, WidgetController.getMessages);
router.get('/sessions/', getSessionsValidation, WidgetController.getSessions);

module.exports = router;