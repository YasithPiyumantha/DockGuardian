const express = require('express');
const router = express.Router();
const scanController = require('../controllers/scanController');
const { authenticate, authenticateAgent } = require('../middleware/auth');

// Agent endpoints
router.post('/submit', authenticateAgent, scanController.submitScanResult);
router.get('/agent-scans', authenticateAgent, scanController.getScanResults);

// User endpoints
router.get('/', authenticate, scanController.getScanResults);
router.get('/dashboard', authenticate, scanController.getDashboardStats);
router.get('/:scanId', authenticate, scanController.getScanById);

// Clear scans endpoints
router.delete('/clear/old', authenticate, scanController.clearOldScans);
router.delete('/clear/all', authenticate, scanController.clearAllScans);

// Trigger scan endpoints
router.post('/trigger', authenticate, scanController.triggerScan);
router.get('/tasks/pending', authenticateAgent, scanController.getPendingScanTasks);

module.exports = router;
