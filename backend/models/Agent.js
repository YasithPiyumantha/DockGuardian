const mongoose = require('mongoose');

const agentSchema = new mongoose.Schema({
  agentId: {
    type: String,
    required: true,
    unique: true
  },
  hostname: {
    type: String,
    required: true
  },
  ipAddress: {
    type: String,
    required: true
  },
  apiKey: {
    type: String,
    required: true
  },
  status: {
    type: String,
    enum: ['active', 'inactive', 'error'],
    default: 'active'
  },
  lastHeartbeat: {
    type: Date,
    default: Date.now
  },
  metadata: {
    osType: String,
    osVersion: String,
    dockerVersion: String,
    agentVersion: String
  },
  createdAt: {
    type: Date,
    default: Date.now
  }
});

module.exports = mongoose.model('Agent', agentSchema);
