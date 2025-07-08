const express = require('express');
const { body } = require('express-validator');
const ChatController = require('../controllers/chatController');
const authMiddleware = require('../middleware/auth');

const router = express.Router();

// Conditional auth middleware - allows widget requests without auth
const conditionalAuthMiddleware = (req, res, next) => {
  // If request has email but no Authorization header, allow it (widget request)
  if (req.body.email && !req.headers.authorization) {
    return next();
  }
  // Otherwise, require authentication
  return authMiddleware(req, res, next);
};

// Validation rules
const createSessionValidation = [
  body('title').optional().trim().isLength({ min: 1, max: 255 }),
];

const updateSessionValidation = [
  body('title').trim().isLength({ min: 1, max: 255 }),
];

const sendMessageValidation = [
  body('message').trim().isLength({ min: 1, max: 10000 }),
];

// Routes with auth middleware
router.post('/sessions', authMiddleware, createSessionValidation, ChatController.createSession);
router.get('/sessions', authMiddleware, ChatController.getSessions);
router.get('/sessions/:sessionId', authMiddleware, ChatController.getSession);
router.put('/sessions/:sessionId', authMiddleware, updateSessionValidation, ChatController.updateSession);
router.delete('/sessions/:sessionId', authMiddleware, ChatController.deleteSession);
router.post('/sessions/:sessionId/messages', authMiddleware, sendMessageValidation, ChatController.sendMessage);
router.post('/sessions/:sessionId/stream', authMiddleware, sendMessageValidation, ChatController.streamMessage);

// Frontend-compatible routes with conditional auth (allows widget requests)
router.post('/stream/', conditionalAuthMiddleware, sendMessageValidation, ChatController.streamMessage);
router.post('/message/', conditionalAuthMiddleware, sendMessageValidation, ChatController.sendMessage);

module.exports = router;