const Agent = require('../models/Agent');
const Task = require('../models/Task');
const { v4: uuidv4 } = require('uuid');

const fixContainer = async (req, res) => {
  try {
    console.log('=== FIX CONTAINER REQUEST ===');
    console.log('Request body:', JSON.stringify(req.body, null, 2));
    
    const { containerId, issueType, agentId } = req.body;
    
    if (!containerId || !issueType || !agentId) {
      console.log('❌ Missing required fields');
      return res.status(400).json({ 
        error: 'containerId, issueType, and agentId are required',
        received: { containerId, issueType, agentId }
      });
    }

    const agent = await Agent.findOne({ agentId });
    
    if (!agent) {
      console.log('❌ Agent not found:', agentId);
      return res.status(404).json({ error: 'Agent not found' });
    }

    console.log('✅ Agent found, creating task');

    const task = new Task({
      taskId: uuidv4(),
      agentId,
      containerId,
      issueType,
      status: 'pending'
    });

    await task.save();

    console.log('✅ Task created:', task.taskId);

    res.json({
      message: 'Healing task created',
      taskId: task.taskId,
      status: 'pending',
      containerId,
      issueType
    });

  } catch (error) {
    console.error('❌ Fix container error:', error.message);
    res.status(500).json({ 
      error: 'Failed to create healing task',
      details: error.message
    });
  }
};

const getPendingTasks = async (req, res) => {
  try {
    const { agentId } = req.params;
    
    const tasks = await Task.find({
      agentId,
      status: 'pending'
    }).sort({ createdAt: 1 });

    res.json({ tasks });

  } catch (error) {
    console.error('❌ Get pending tasks error:', error);
    res.status(500).json({ 
      error: 'Failed to get pending tasks',
      details: error.message
    });
  }
};

const updateTaskStatus = async (req, res) => {
  try {
    const { taskId } = req.params;
    const { status, result, error } = req.body;

    console.log('📝 Updating task:', taskId, 'Status:', status);
    if (result) console.log('Result:', JSON.stringify(result));

    const updateData = { status };
    
    if (status === 'running') {
      updateData.startedAt = new Date();
    } else if (status === 'completed' || status === 'failed') {
      updateData.completedAt = new Date();
    }

    if (result) updateData.result = result;
    if (error) updateData.error = error;

    const task = await Task.findOneAndUpdate(
      { taskId },
      updateData,
      { new: true }
    );

    if (!task) {
      return res.status(404).json({ error: 'Task not found' });
    }

    console.log('✅ Task updated:', taskId);

    res.json({ task });

  } catch (error) {
    console.error('❌ Update task error:', error);
    res.status(500).json({ 
      error: 'Failed to update task',
      details: error.message
    });
  }
};

const getTaskStatus = async (req, res) => {
  try {
    const { taskId } = req.params;

    const task = await Task.findOne({ taskId });

    if (!task) {
      return res.status(404).json({ error: 'Task not found' });
    }

    res.json({ task });

  } catch (error) {
    console.error('❌ Get task status error:', error);
    res.status(500).json({ 
      error: 'Failed to get task status',
      details: error.message
    });
  }
};

const rollbackContainer = async (req, res) => {
  try {
    const { backupFile, agentId } = req.body;
    
    if (!backupFile) {
      return res.status(400).json({ error: 'backupFile is required' });
    }

    const agent = await Agent.findOne({ agentId });
    if (!agent) {
      return res.status(404).json({ error: 'Agent not found' });
    }

    const task = new Task({
      taskId: uuidv4(),
      agentId,
      containerId: 'rollback',
      issueType: `rollback:${backupFile}`,
      status: 'pending'
    });

    await task.save();

    res.json({
      message: 'Rollback task created',
      taskId: task.taskId,
      status: 'pending',
      backupFile
    });

  } catch (error) {
    console.error('Rollback error:', error);
    res.status(500).json({ 
      error: 'Failed to create rollback task',
      details: error.message
    });
  }
};

const listBackups = async (req, res) => {
  try {
    const { agentId } = req.query;
    
    console.log('📋 Getting backup history for agent:', agentId);
    
    const tasks = await Task.find({
      agentId,
      status: 'completed'
    }).sort({ completedAt: -1 }).limit(50);

    console.log(`Found ${tasks.length} completed tasks`);

    const backups = [];
    
    for (const task of tasks) {
      if (task.result) {
        let backupPath = null;
        
        if (typeof task.result === 'string') {
          try {
            const parsed = JSON.parse(task.result);
            backupPath = parsed.backup;
          } catch (e) {
            // Not JSON, skip
          }
        } else if (task.result.backup) {
          backupPath = task.result.backup;
        } else if (task.result.output) {
          try {
            const parsed = JSON.parse(task.result.output);
            backupPath = parsed.backup;
          } catch (e) {
            // Not JSON, skip
          }
        }
        
        if (backupPath) {
          const filename = backupPath.split('/').pop();
          backups.push({
            filename: filename,
            taskId: task.taskId,
            containerId: task.containerId,
            issueType: task.issueType,
            created: task.completedAt,
            path: backupPath
          });
        }
      }
    }

    console.log(`✅ Found ${backups.length} backups`);

    res.json({ backups });

  } catch (error) {
    console.error('List backups error:', error);
    res.status(500).json({ 
      error: 'Failed to list backups',
      details: error.message
    });
  }
};

const deleteBackup = async (req, res) => {
  try {
    const { taskId } = req.params;
    
    console.log('🗑️  Deleting backup task:', taskId);
    
    const task = await Task.findOneAndDelete({ taskId });

    if (!task) {
      return res.status(404).json({ error: 'Backup not found' });
    }

    console.log('✅ Backup deleted:', taskId);

    res.json({ 
      success: true,
      message: 'Backup deleted successfully' 
    });

  } catch (error) {
    console.error('Delete backup error:', error);
    res.status(500).json({ 
      error: 'Failed to delete backup',
      details: error.message
    });
  }
};

module.exports = { 
  fixContainer, 
  rollbackContainer, 
  listBackups,
  deleteBackup,
  getPendingTasks,
  updateTaskStatus,
  getTaskStatus
};
