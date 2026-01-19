const jwt = require('jsonwebtoken');
const User = require('../models/User');

exports.authenticate = async (req, res, next) => {
  try {
    const token = req.header('Authorization')?.replace('Bearer ', '');
    
    if (!token) {
      return res.status(401).json({ error: 'Authentication required' });
    }

    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    const user = await User.findById(decoded.userId);
    
    if (!user) {
      return res.status(401).json({ error: 'User not found' });
    }

    req.user = user;
    req.token = token;
    next();
  } catch (error) {
    res.status(401).json({ error: 'Invalid authentication token' });
  }
};

exports.authenticateAgent = (req, res, next) => {
  const apiKey = req.header('X-API-Key');
  
  if (!apiKey) {
    return res.status(401).json({ error: 'API key required' });
  }

  if (apiKey !== process.env.AGENT_API_KEY) {
    return res.status(403).json({ error: 'Invalid API key' });
  }

  next();
};

// Dual authentication - accepts both JWT token AND API key
exports.authenticateBoth = async (req, res, next) => {
  try {
    // Check for API key first (for agents)
    const apiKey = req.header('X-API-Key');
    if (apiKey && apiKey === process.env.AGENT_API_KEY) {
      req.authenticated = 'agent';
      return next();
    }

    // Then check for JWT token (for users)
    const token = req.header('Authorization')?.replace('Bearer ', '');
    if (!token) {
      return res.status(401).json({ error: 'Authentication required' });
    }

    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    const user = await User.findById(decoded.userId);
    
    if (!user) {
      return res.status(401).json({ error: 'User not found' });
    }

    req.user = user;
    req.token = token;
    req.authenticated = 'user';
    next();
  } catch (error) {
    res.status(401).json({ error: 'Invalid authentication' });
  }
};

exports.requireAdmin = async (req, res, next) => {
  if (req.user.role !== 'admin') {
    return res.status(403).json({ error: 'Admin access required' });
  }
  next();
};
