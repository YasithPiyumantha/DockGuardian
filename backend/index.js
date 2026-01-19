require('dotenv').config();
const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const authRoutes = require('./routes/auth');
const scanRoutes = require('./routes/scan');
const healerRoutes = require('./routes/healer');
const vulnRoutes = require('./routes/vulnerabilities');

const app = express();

// Middleware
app.use(cors({
  origin: true,
  credentials: true
}));
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));

// Health check
app.get('/health', (req, res) => {
  const dbStatus = mongoose.connection.readyState === 1 ? 'connected' : 'disconnected';
  res.json({ 
    status: 'healthy', 
    timestamp: new Date().toISOString(),
    database: dbStatus
  });
});

// Routes
app.use('/api/auth', authRoutes);
app.use('/api/scans', scanRoutes);
app.use('/api/healer', healerRoutes);
app.use('/api/vulnerabilities', vulnRoutes);

// Error handling middleware
app.use((err, req, res, next) => {
  console.error('Error:', err);
  res.status(500).json({ 
    error: 'Internal server error',
    message: process.env.NODE_ENV === 'development' ? err.message : undefined
  });
});

// Get PORT from environment
const PORT = process.env.PORT || 8080;

// Start server
app.listen(PORT, '0.0.0.0', () => {
  console.log('Server running on port ' + PORT);
  console.log('Environment: ' + (process.env.NODE_ENV || 'development'));
  console.log('Attempting MongoDB connection...');
  
  // MongoDB connection
  mongoose.connect(process.env.MONGODB_URI, {
    useNewUrlParser: true,
    useUnifiedTopology: true,
    serverSelectionTimeoutMS: 5000,
    socketTimeoutMS: 45000,
  })
  .then(() => {
    console.log('Connected to MongoDB');
  })
  .catch(err => {
    console.error('MongoDB connection error:', err.message);
    console.log('Server running without database connection');
  });
});
