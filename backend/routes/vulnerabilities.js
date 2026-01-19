const express = require('express');
const router = express.Router();
const vulnController = require('../controllers/vulnController');
const healerController = require('../controllers/healerController');
const { authenticate, authenticateAgent, authenticateBoth } = require('../middleware/auth');

// Vulnerability search endpoints - accepts BOTH agent API key and user JWT
router.get('/search', authenticateBoth, vulnController.searchVulnerabilities);
router.get('/stats', authenticate, vulnController.getVulnerabilityStats);
router.get('/:cveId', authenticate, vulnController.getVulnerabilityById);

// Healer endpoints (for users)
router.post('/fix', authenticate, healerController.fixContainer);
router.post('/rollback', authenticate, healerController.rollbackContainer);
router.get('/backups', authenticate, healerController.listBackups);

module.exports = router;
