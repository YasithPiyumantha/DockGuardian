const Vulnerability = require('../models/Vulnerability');

exports.searchVulnerabilities = async (req, res) => {
  try {
    const { package: packageName, severity, limit = 100 } = req.query;

    const filter = {};
    
    if (packageName) {
      filter['affectedPackages.product'] = new RegExp(packageName, 'i');
    }
    
    if (severity) {
      filter.severity = severity.toUpperCase();
    }

    const vulnerabilities = await Vulnerability.find(filter)
      .limit(parseInt(limit))
      .sort({ cvssScore: -1 });

    res.json({
      vulnerabilities,
      total: vulnerabilities.length
    });
  } catch (error) {
    console.error('Search vulnerabilities error:', error);
    res.status(500).json({ error: 'Failed to search vulnerabilities' });
  }
};

exports.getVulnerabilityById = async (req, res) => {
  try {
    const { cveId } = req.params;
    const vulnerability = await Vulnerability.findOne({ cveId });

    if (!vulnerability) {
      return res.status(404).json({ error: 'Vulnerability not found' });
    }

    res.json({ vulnerability });
  } catch (error) {
    console.error('Get vulnerability error:', error);
    res.status(500).json({ error: 'Failed to fetch vulnerability' });
  }
};

exports.getVulnerabilityStats = async (req, res) => {
  try {
    const total = await Vulnerability.countDocuments();
    
    const bySeverity = await Vulnerability.aggregate([
      {
        $group: {
          _id: '$severity',
          count: { $sum: 1 }
        }
      }
    ]);

    const stats = {
      total,
      bySeverity: bySeverity.reduce((acc, item) => {
        acc[item._id] = item.count;
        return acc;
      }, {})
    };

    res.json({ stats });
  } catch (error) {
    console.error('Get vulnerability stats error:', error);
    res.status(500).json({ error: 'Failed to fetch vulnerability stats' });
  }
};
