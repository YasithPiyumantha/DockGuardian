const mongoose = require('mongoose');

const scanResultSchema = new mongoose.Schema({
  scanId: {
    type: String,
    required: true,
    unique: true
  },
  agentId: {
    type: String,
    required: true,
    ref: 'Agent'
  },
  containerId: {
    type: String,
    required: true
  },
  containerName: {
    type: String,
    required: true
  },
  image: {
    type: String,
    required: true
  },
  scanType: {
    type: String,
    enum: ['full', 'quick', 'scheduled'],
    default: 'full'
  },
  vulnerabilities: [{
    cveId: String,
    package: String,
    version: String,
    severity: String,
    cvssScore: Number,
    description: String,
    fixAvailable: Boolean,
    fixedVersion: String
  }],
  cisBenchmarks: [{
    checkId: String,
    title: String,
    description: String,
    status: {
      type: String,
      enum: ['PASS', 'FAIL', 'WARN', 'INFO']
    },
    severity: String,
    remediation: String
  }],
  threatScore: {
    total: {
      type: Number,
      min: 0,
      max: 100
    },
    vulnerabilityScore: Number,
    exploitabilityScore: Number,
    impactScore: Number,
    cisComplianceScore: Number,
    riskLevel: {
      type: String,
      enum: ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'MINIMAL']
    }
  },
  statistics: {
    totalVulnerabilities: Number,
    critical: Number,
    high: Number,
    medium: Number,
    low: Number,
    cisPassedChecks: Number,
    cisFailedChecks: Number,
    packagesScanned: Number
  },
  scanDuration: Number,
  scanDate: {
    type: Date,
    default: Date.now
  },
  status: {
    type: String,
    enum: ['completed', 'failed', 'in_progress'],
    default: 'completed'
  }
});

// Index for faster queries
scanResultSchema.index({ agentId: 1, scanDate: -1 });
scanResultSchema.index({ containerId: 1, scanDate: -1 });

module.exports = mongoose.model('ScanResult', scanResultSchema);
