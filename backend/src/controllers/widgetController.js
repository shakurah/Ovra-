const { validationResult } = require('express-validator');
const WidgetService = require('../services/widgetService');

class WidgetController {
  static async register(req, res, next) {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ 
          is_success: false,
          message: 'Validation errors',
          errors: errors.array() 
        });
      }

      const { email, privacy_accepted, terms_accepted, source_website } = req.body;

      if (!email || !privacy_accepted || !terms_accepted) {
        return res.status(400).json({
          is_success: false,
          message: 'Email, privacy acceptance, and terms acceptance are required'
        });
      }

      const marketingEmail = await WidgetService.registerEmail(
        email,
        source_website,
        privacy_accepted,
        terms_accepted
      );

      res.status(200).json({
        is_success: true,
        message: 'Email registered successfully',
        data: {
          email: marketingEmail.email,
          id: marketingEmail.id
        }
      });
    } catch (error) {
      console.error('Widget registration error:', error);
      res.status(500).json({
        is_success: false,
        message: 'Internal server error',
        error_code: 'INTERNAL_ERROR'
      });
    }
  }

  static async chat(req, res, next) {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ 
          is_success: false,
          message: 'Validation errors',
          errors: errors.array() 
        });
      }

      const { email, question, session_id, source_website } = req.body;

      if (!email || !question) {
        return res.status(400).json({
          is_success: false,
          message: 'Email and question are required'
        });
      }

      try {
        const response = await WidgetService.sendMessage(
          email,
          question,
          session_id,
          source_website
        );

        res.status(200).json({
          is_success: true,
          message: 'Message sent successfully',
          data: response
        });
      } catch (serviceError) {
        if (serviceError.message === 'Email not registered') {
          return res.status(400).json({
            is_success: false,
            message: 'Email not registered. Please register first.',
            error_code: 'USER_NOT_REGISTERED'
          });
        }
        throw serviceError;
      }
    } catch (error) {
      console.error('Widget chat error:', error);
      res.status(500).json({
        is_success: false,
        message: 'Internal server error',
        error_code: 'INTERNAL_ERROR'
      });
    }
  }

  static async getMessages(req, res, next) {
    try {
      const { sessionId } = req.params;

      if (!sessionId) {
        return res.status(400).json({
          is_success: false,
          message: 'Session ID is required'
        });
      }

      const messages = await WidgetService.getSessionMessages(sessionId);

      res.status(200).json({
        is_success: true,
        data: {
          messages
        }
      });
    } catch (error) {
      console.error('Widget get messages error:', error);
      res.status(500).json({
        is_success: false,
        message: 'Internal server error',
        error_code: 'INTERNAL_ERROR'
      });
    }
  }

  static async getSessions(req, res, next) {
    try {
      const { email } = req.query;

      if (!email) {
        return res.status(400).json({
          is_success: false,
          message: 'Email is required'
        });
      }

      const sessions = await WidgetService.getEmailSessions(email);

      res.status(200).json({
        is_success: true,
        data: {
          sessions
        }
      });
    } catch (error) {
      console.error('Widget get sessions error:', error);
      res.status(500).json({
        is_success: false,
        message: 'Internal server error',
        error_code: 'INTERNAL_ERROR'
      });
    }
  }
}

module.exports = WidgetController;