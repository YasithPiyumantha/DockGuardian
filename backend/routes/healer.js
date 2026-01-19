const express = require('express');
const router = express.Router();
const healerController = require('../controllers/healerController');
const { authenticate } = require('../middleware/auth');

// Existing routes
router.post('/fix', authenticate, healerController.fixContainer);
router.post('/rollback', authenticate, healerController.rollbackContainer);
router.get('/backups', healerController.listBackups);
router.delete('/backups/:taskId', authenticate, healerController.deleteBackup);  // NEW

// Task-based routes
router.get('/tasks/:agentId/pending', healerController.getPendingTasks);
router.put('/tasks/:taskId/status', healerController.updateTaskStatus);
router.get('/tasks/:taskId', authenticate, healerController.getTaskStatus);

module.exports = router;
