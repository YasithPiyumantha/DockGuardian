/**
 * Advanced Threat Score Calculator
 * Calculates a weighted threat score based on 4 components:
 * 1. Vulnerability Score (40%) - Based on CVE severity
 * 2. Exploitability Score (30%) - Based on exploit availability
 * 3. Impact Score (20%) - Based on CVSS impact metrics
 * 4. CIS Compliance Score (10%) - Based on benchmark failures
 */

class ThreatScoreCalculator {
  
  // Component weights
  static WEIGHTS = {
    vulnerability: 0.4,
    exploitability: 0.3,
    impact: 0.2,
    cisCompliance: 0.1
  };

  // Severity values
  static SEVERITY_VALUES = {
    'CRITICAL': 10,
    'HIGH': 7.5,
    'MEDIUM': 5,
    'LOW': 2.5,
    'NONE': 0
  };

  /**
   * Calculate vulnerability score based on CVE severities
   */
  static calculateVulnerabilityScore(vulnerabilities) {
    if (!vulnerabilities || vulnerabilities.length === 0) {
      return 0;
    }

    const severityCounts = {
      CRITICAL: 0,
      HIGH: 0,
      MEDIUM: 0,
      LOW: 0
    };

    vulnerabilities.forEach(vuln => {
      const severity = vuln.severity?.toUpperCase() || 'LOW';
      if (severityCounts.hasOwnProperty(severity)) {
        severityCounts[severity]++;
      }
    });

    // Weighted score: Critical has highest impact
    const weightedScore = (
      (severityCounts.CRITICAL * 10) +
      (severityCounts.HIGH * 7) +
      (severityCounts.MEDIUM * 4) +
      (severityCounts.LOW * 1)
    );

    // Normalize to 0-100 scale (cap at 100)
    const maxPossibleScore = vulnerabilities.length * 10;
    const score = Math.min(100, (weightedScore / maxPossibleScore) * 100);

    return Math.round(score * 10) / 10;
  }

  /**
   * Calculate exploitability score
   */
  static calculateExploitabilityScore(vulnerabilities) {
    if (!vulnerabilities || vulnerabilities.length === 0) {
      return 0;
    }

    const exploitableCount = vulnerabilities.filter(vuln => 
      vuln.exploitAvailable === true
    ).length;

    const criticalExploitable = vulnerabilities.filter(vuln =>
      vuln.exploitAvailable === true && vuln.severity === 'CRITICAL'
    ).length;

    // Higher weight for exploitable critical vulnerabilities
    const score = (
      (criticalExploitable * 15) +
      (exploitableCount * 8)
    ) / vulnerabilities.length;

    return Math.min(100, Math.round(score * 10) / 10);
  }

  /**
   * Calculate impact score based on CVSS metrics
   */
  static calculateImpactScore(vulnerabilities) {
    if (!vulnerabilities || vulnerabilities.length === 0) {
      return 0;
    }

    const impactValues = {
      'HIGH': 10,
      'MEDIUM': 5,
      'LOW': 2,
      'NONE': 0
    };

    let totalImpact = 0;
    let validCount = 0;

    vulnerabilities.forEach(vuln => {
      if (vuln.metadata) {
        const confidentiality = impactValues[vuln.metadata.confidentialityImpact?.toUpperCase()] || 0;
        const integrity = impactValues[vuln.metadata.integrityImpact?.toUpperCase()] || 0;
        const availability = impactValues[vuln.metadata.availabilityImpact?.toUpperCase()] || 0;
        
        totalImpact += (confidentiality + integrity + availability) / 3;
        validCount++;
      }
    });

    if (validCount === 0) {
      // Fallback to CVSS score
      const avgCvss = vulnerabilities.reduce((sum, vuln) => 
        sum + (vuln.cvssScore || 0), 0
      ) / vulnerabilities.length;
      return Math.round(avgCvss * 10);
    }

    return Math.min(100, Math.round((totalImpact / validCount) * 10));
  }

  /**
   * Calculate CIS compliance score
   */
  static calculateCISComplianceScore(cisBenchmarks) {
    if (!cisBenchmarks || cisBenchmarks.length === 0) {
      return 0;
    }

    const failedChecks = cisBenchmarks.filter(check => 
      check.status === 'FAIL'
    ).length;

    const criticalFailures = cisBenchmarks.filter(check =>
      check.status === 'FAIL' && check.severity === 'CRITICAL'
    ).length;

    // Penalize failures, especially critical ones
    const score = (
      (failedChecks * 5) +
      (criticalFailures * 10)
    );

    return Math.min(100, Math.round(score * 10) / 10);
  }

  /**
   * Determine risk level based on total score
   */
  static determineRiskLevel(totalScore) {
    if (totalScore >= 80) return 'CRITICAL';
    if (totalScore >= 60) return 'HIGH';
    if (totalScore >= 40) return 'MEDIUM';
    if (totalScore >= 20) return 'LOW';
    return 'MINIMAL';
  }

  /**
   * Calculate complete threat score
   */
  static calculate(vulnerabilities, cisBenchmarks) {
    const vulnScore = this.calculateVulnerabilityScore(vulnerabilities);
    const exploitScore = this.calculateExploitabilityScore(vulnerabilities);
    const impactScore = this.calculateImpactScore(vulnerabilities);
    const cisScore = this.calculateCISComplianceScore(cisBenchmarks);

    // Weighted total
    const totalScore = (
      (vulnScore * this.WEIGHTS.vulnerability) +
      (exploitScore * this.WEIGHTS.exploitability) +
      (impactScore * this.WEIGHTS.impact) +
      (cisScore * this.WEIGHTS.cisCompliance)
    );

    const finalScore = Math.round(totalScore * 10) / 10;

    return {
      total: finalScore,
      vulnerabilityScore: vulnScore,
      exploitabilityScore: exploitScore,
      impactScore: impactScore,
      cisComplianceScore: cisScore,
      riskLevel: this.determineRiskLevel(finalScore),
      breakdown: {
        vulnerability: `${vulnScore} × ${this.WEIGHTS.vulnerability} = ${Math.round(vulnScore * this.WEIGHTS.vulnerability * 10) / 10}`,
        exploitability: `${exploitScore} × ${this.WEIGHTS.exploitability} = ${Math.round(exploitScore * this.WEIGHTS.exploitability * 10) / 10}`,
        impact: `${impactScore} × ${this.WEIGHTS.impact} = ${Math.round(impactScore * this.WEIGHTS.impact * 10) / 10}`,
        cisCompliance: `${cisScore} × ${this.WEIGHTS.cisCompliance} = ${Math.round(cisScore * this.WEIGHTS.cisCompliance * 10) / 10}`
      }
    };
  }
}

module.exports = ThreatScoreCalculator;
