const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const path = require('path');

const config = require('./config');
const authRoutes = require('./routes/auth');
const chatRoutes = require('./routes/chat');
const widgetRoutes = require('./routes/widget');
const adminRoutes = require('./routes/admin');
const { errorHandler } = require('./middleware/errorHandler');

const app = express();

// Set view engine
app.set('view engine', 'pug');
app.set('views', path.join(__dirname, 'views'));

// Security middleware
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com", "https://cdn.jsdelivr.net"],
      scriptSrc: ["'self'", "'unsafe-inline'", "'unsafe-eval'", "https://cdn.jsdelivr.net"],
      imgSrc: ["'self'", "data:", "https:"],
      fontSrc: ["'self'", "https://fonts.gstatic.com", "https://cdn.jsdelivr.net"],
      upgradeInsecureRequests: null, // Disable upgrade-insecure-requests for HTTP
    },
  },
  crossOriginOpenerPolicy: false, // Disable for HTTP connections
  crossOriginResourcePolicy: false, // Disable for HTTP connections
  originAgentCluster: false, // Disable for HTTP connections
  hsts: false, // Disable HSTS for HTTP connections
}));
app.use(cors({
  origin: function (origin, callback) {
    // Allow requests with no origin (like mobile apps or curl requests)
    if (!origin) return callback(null, true);
    
    // Always allow localhost for development
    if (origin.includes('localhost') || origin.includes('127.0.0.1')) {
      return callback(null, true);
    }
    
    // For production, you might want to maintain a whitelist
    // For now, allowing all origins for widget embedding
    return callback(null, true);
  },
  credentials: true,
}));

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
});
app.use(limiter);

// Body parsing middleware
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// Admin panel routes
app.use('/admin', adminRoutes);

// Routes
app.use('/api/auth', authRoutes);
app.use('/api/v1/chat', chatRoutes);
app.use('/api/chat', chatRoutes); // API prefix for frontend
app.use('/chat', chatRoutes); // Also support direct /chat for frontend
app.use('/widget', widgetRoutes); // Widget routes for chat widget
app.use('/api/widget', widgetRoutes); // API prefix for widget routes

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'OK', timestamp: new Date().toISOString() });
});

// Error handling middleware
app.use(errorHandler);

app.listen(config.port, () => {
  console.log(`Server running on port ${config.port} in ${config.nodeEnv} mode`);
  console.log(`Admin panel available at: http://localhost:${config.port}/admin`);
});