const ScanResult = require('../models/ScanResult');
const Agent = require('../models/Agent');
const ThreatScoreCalculator = require('../utils/threatScoreCalculator');
const Task = require('../models/Task');

exports.submitScanResult = async (req, res) => {
  try {
    const {
      scanId,
      agentId,
      containerId,
      containerName,
      image,
      vulnerabilities,
      cisBenchmarks,
      scanDuration,
      packagesScanned,
      scanDate
    } = req.body;

    // Verify agent exists or auto-register
    let agent = await Agent.findOne({ agentId });
    if (!agent) {
      // Auto-register new agent
      agent = new Agent({
        agentId,
        hostname: req.body.hostname || 'unknown',
        ipAddress: req.body.ipAddress || 'unknown',
        apiKey: req.header('X-API-Key'), // Get API key from request header
        status: 'active',
        lastHeartbeat: new Date(),
        metadata: {
          osType: req.body.platform || 'unknown',
          osVersion: req.body.platformVersion || 'unknown',
          dockerVersion: req.body.dockerVersion || 'unknown',
          agentVersion: '1.0.0'
        }
      });
      await agent.save();
      console.log(`Auto-registered new agent: ${agentId}`);
    }

    // Update agent heartbeat
    agent.lastHeartbeat = new Date();
    agent.status = 'active';
    await agent.save();

    // Use threat score from agent, or recalculate if not provided
    const threatScore = req.body.threatScore || ThreatScoreCalculator.calculate(
      vulnerabilities,
      cisBenchmarks
    );

    // Calculate statistics
    const statistics = {
      totalVulnerabilities: vulnerabilities.length,
      critical: vulnerabilities.filter(v => v.severity === 'CRITICAL').length,
      high: vulnerabilities.filter(v => v.severity === 'HIGH').length,
      medium: vulnerabilities.filter(v => v.severity === 'MEDIUM').length,
      low: vulnerabilities.filter(v => v.severity === 'LOW').length,
      cisPassedChecks: cisBenchmarks.filter(c => c.status === 'PASS').length,
      cisFailedChecks: cisBenchmarks.filter(c => c.status === 'FAIL').length,
      packagesScanned: packagesScanned || 0
    };

    // Create scan result
    const scanResult = new ScanResult({
      scanId,
      agentId,
      containerId,
      containerName,
      image,
      vulnerabilities,
      cisBenchmarks,
      threatScore,
      statistics,
      scanDuration,
      scanDate: scanDate ? new Date(scanDate) : new Date(),
      status: 'completed'
    });

    await scanResult.save();

    res.status(201).json({
      message: 'Scan result saved successfully',
      scanId,
      threatScore: threatScore.total,
      riskLevel: threatScore.riskLevel
    });
  } catch (error) {
    console.error('Submit scan error:', error);
    res.status(500).json({ error: 'Failed to save scan result' });
  }
};

exports.getScanResults = async (req, res) => {
  try {
    const { agentId, containerId, limit = 50, skip = 0 } = req.query;

    const filter = {};
    if (agentId) filter.agentId = agentId;
    if (containerId) filter.containerId = containerId;

    const scans = await ScanResult.find(filter)
      .sort({ scanDate: -1 })
      .limit(parseInt(limit))
      .skip(parseInt(skip));

    const total = await ScanResult.countDocuments(filter);

    res.json({
      scans,
      total,
      limit: parseInt(limit),
      skip: parseInt(skip)
    });
  } catch (error) {
    console.error('Get scans error:', error);
    res.status(500).json({ error: 'Failed to fetch scan results' });
  }
};

exports.getScanById = async (req, res) => {
  try {
    const { scanId } = req.params;
    const scan = await ScanResult.findOne({ scanId });

    if (!scan) {
      return res.status(404).json({ error: 'Scan not found' });
    }

    res.json({ scan });
  } catch (error) {
    console.error('Get scan error:', error);
    res.status(500).json({ error: 'Failed to fetch scan' });
  }
};

exports.getDashboardStats = async (req, res) => {
  try {
    const totalScans = await ScanResult.countDocuments();
    const recentScans = await ScanResult.find()
      .sort({ scanDate: -1 })
      .limit(10);

    // Calculate aggregate statistics
    const criticalContainers = await ScanResult.countDocuments({
      'threatScore.riskLevel': 'CRITICAL'
    });

    const highRiskContainers = await ScanResult.countDocuments({
      'threatScore.riskLevel': 'HIGH'
    });

    // Get unique containers
    const uniqueContainers = await ScanResult.distinct('containerId');

    // Average threat score
    const avgThreatScore = await ScanResult.aggregate([
      {
        $group: {
          _id: null,
          avgScore: { $avg: '$threatScore.total' }
        }
      }
    ]);

    res.json({
      totalScans,
      totalContainers: uniqueContainers.length,
      criticalContainers,
      highRiskContainers,
      averageThreatScore: avgThreatScore[0]?.avgScore || 0,
      recentScans
    });
  } catch (error) {
    console.error('Dashboard stats error:', error);
    res.status(500).json({ error: 'Failed to fetch dashboard stats' });
  }
};

exports.clearOldScans = async (req, res) => {
  try {
    const { days = 7 } = req.query;
    
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - parseInt(days));
    
    const result = await ScanResult.deleteMany({
      timestamp: { $lt: cutoffDate }
    });
    
    res.json({
      message: `Cleared ${result.deletedCount} old scans`,
      deletedCount: result.deletedCount
    });
  } catch (error) {
    console.error('Clear scans error:', error);
    res.status(500).json({ error: 'Failed to clear old scans' });
  }
};

exports.clearAllScans = async (req, res) => {
  try {
    const result = await ScanResult.deleteMany({});
    
    res.json({
      message: `Cleared all scans (${result.deletedCount} scans deleted)`,
      deletedCount: result.deletedCount
    });
  } catch (error) {
    console.error('Clear all scans error:', error);
    res.status(500).json({ error: 'Failed to clear scans' });
  }
};

// Trigger scan for selected containers
exports.triggerScan = async (req, res) => {
  try {
    const { containerIds, agentId } = req.body;

    if (!containerIds || !Array.isArray(containerIds) || containerIds.length === 0) {
      return res.status(400).json({ error: 'containerIds array is required' });
    }

    if (!agentId) {
      return res.status(400).json({ error: 'agentId is required' });
    }

    // Verify agent exists
    const agent = await Agent.findOne({ agentId });
    if (!agent) {
      return res.status(404).json({ error: 'Agent not found' });
    }

    // Create scan tasks for each container
    const tasks = [];
    const { v4: uuidv4 } = require('uuid');
    
    for (const containerId of containerIds) {
      const taskId = uuidv4();
      
      const task = new Task({
        taskId,
        taskType: 'scan',
        agentId,
        containerId,
        status: 'pending'
      });
      
      await task.save();
      tasks.push({ taskId, containerId });
    }

    res.status(201).json({
      message: `Created ${tasks.length} scan task(s)`,
      tasks
    });
  } catch (error) {
    console.error('Trigger scan error:', error);
    res.status(500).json({ error: 'Failed to trigger scan' });
  }
};

// Get pending scan tasks for agent
exports.getPendingScanTasks = async (req, res) => {
  try {
    const agentId = req.query.agentId || req.agentId;

    if (!agentId) {
      return res.status(400).json({ error: 'agentId is required' });
    }

    const tasks = await Task.find({
      agentId,
      taskType: 'scan',
      status: 'pending'
    }).sort({ createdAt: 1 });

    res.json({ tasks });
  } catch (error) {
    console.error('Get pending scan tasks error:', error);
    res.status(500).json({ error: 'Failed to fetch pending scan tasks' });
  }
};


