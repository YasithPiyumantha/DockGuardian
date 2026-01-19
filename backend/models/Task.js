const mongoose = require('mongoose');

const taskSchema = new mongoose.Schema({
  taskId: {
    type: String,
    required: true,
    unique: true
  },
  taskType: {  // NEW FIELD
    type: String,
    enum: ['heal', 'scan'],
    required: true,
    default: 'heal'
  },
  agentId: {
    type: String,
    required: true
  },
  containerId: {
    type: String,
    required: true
  },
  containerName: {  // NEW FIELD - useful for scan tasks
    type: String,
    required: false
  },
  issueType: {
    type: String,
    required: false  // CHANGED from true to false (not needed for scan tasks)
  },
  status: {
    type: String,
    enum: ['pending', 'running', 'completed', 'failed'],
    default: 'pending'
  },
  result: {
    type: mongoose.Schema.Types.Mixed,
    default: null
  },
  error: {
    type: String,
    default: null
  },
  createdAt: {
    type: Date,
    default: Date.now
  },
  startedAt: {
    type: Date,
    default: null
  },
  completedAt: {
    type: Date,
    default: null
  }
});

module.exports = mongoose.model('Task', taskSchema);
