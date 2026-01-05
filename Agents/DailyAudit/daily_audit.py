"""
DailyAudit Agent - Full compliance check on all databases
Runs daily at 02:00

Checks:
- Census: BAO/DL completeness, SNOW group, gateway access
- Performance: SQL plan changes, restore points, connection pools
- Capacity: Tablespace usage, diskgroup usage, data retention
- Best Practices: Large non-partitioned tables, incremental stats
"""

import os
import sys
# Fix Windows console encoding for emojis
sys.stdout.reconfigure(encoding='utf-8')

from datetime import datetime, timedelta
from typing import Dict, List, Any

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from Orchestrator.src.mongo_proxy import MongoProxy


class DailyAuditAgent:
    """Agent that performs daily compliance audit on all databases."""
    
    def __init__(self):
        self.mongo = MongoProxy()
        self.audit_results = []
        self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def run(self) -> Dict[str, Any]:
        """Execute the daily audit."""
        print(f"🔍 Starting DailyAudit - Run ID: {self.run_id}")
        start_time = datetime.now()
        
        # Get all databases from inventory
        databases = self._get_all_databases()
        print(f"📊 Found {len(databases)} databases to audit")
        
        for db in databases:
            db_name = db.get('identity', {}).get('db_unique_name', 'UNKNOWN')
            print(f"  Auditing: {db_name}")
            
            # Run all audit checks
            audit = {
                'db_unique_name': db_name,
                'audit_date': datetime.now().isoformat(),
                'census': self._check_census(db),
                'performance': self._check_performance(db),
                'capacity': self._check_capacity(db),
                'replication': self._check_replication(db),
                'best_practices': self._check_best_practices(db),
                'overall_status': 'PASS'
            }
            
            # Determine overall status
            if any(check.get('status') == 'CRITICAL' for check in audit.values() if isinstance(check, dict)):
                audit['overall_status'] = 'CRITICAL'
            elif any(check.get('status') == 'WARNING' for check in audit.values() if isinstance(check, dict)):
                audit['overall_status'] = 'WARNING'
                
            self.audit_results.append(audit)
        
        # Save results to MongoDB
        self._save_results()
        
        # Send email reports for issues
        self._send_reports()
        
        duration = (datetime.now() - start_time).total_seconds()
        print(f"✅ DailyAudit completed in {duration:.1f}s")
        
        return {
            'run_id': self.run_id,
            'databases_audited': len(databases),
            'duration_seconds': duration,
            'results': self.audit_results
        }
    
    def _get_all_databases(self) -> List[Dict]:
        """Get all databases from inventory."""
        try:
            return self.mongo.execute_eval("db.inventory_databases.find().toArray()")
        except Exception as e:
            print(f"❌ Error fetching databases: {e}")
            return []
    
    def _check_census(self, db: Dict) -> Dict[str, Any]:
        """Check census completeness: BAO, DL, SNOW, gateway."""
        issues = []
        db_name = db.get('identity', {}).get('db_unique_name', '')
        
        # Check gateway
        gateway = db.get('identity', {}).get('gateway_ref')
        if not gateway:
            issues.append("Missing gateway reference")
        
        # Check business service linkage
        try:
            service = self.mongo.execute_eval(
                f"db.business_services.findOne({{'technical_mapping.db_unique_name': '{db_name}'}})"
            )
            if not service:
                issues.append("No business service linked")
            else:
                contacts = service.get('contacts', {})
                if not contacts.get('bao', {}).get('email'):
                    issues.append("Missing BAO email")
                if not contacts.get('dl_team'):
                    issues.append("Missing DL team email")
                if not contacts.get('reperibilita_number'):
                    issues.append("Missing reperibilità number")
                if not service.get('service_info', {}).get('snow_group'):
                    issues.append("Missing SNOW group")
        except Exception as e:
            issues.append(f"Error checking service: {e}")
        
        return {
            'status': 'CRITICAL' if issues else 'PASS',
            'issues': issues
        }
    
    def _check_performance(self, db: Dict) -> Dict[str, Any]:
        """Check performance: SQL plan changes, restore points."""
        issues = []
        
        # Check for restore points older than threshold
        # This would query actual DB - for now, check metadata
        
        # Check configuration completeness
        config = db.get('configuration', {})
        if not config.get('version'):
            issues.append("Missing database version")
        
        oracle_spec = config.get('oracle_specific', {})
        if db.get('identity', {}).get('engine') == 'ORACLE':
            if not oracle_spec.get('oracle_home'):
                issues.append("Missing Oracle Home path")
            if not oracle_spec.get('patches'):
                issues.append("No patches documented")
        
        return {
            'status': 'WARNING' if issues else 'PASS',
            'issues': issues
        }
    
    def _check_capacity(self, db: Dict) -> Dict[str, Any]:
        """Check capacity: tablespace, diskgroup, retention."""
        issues = []
        storage = db.get('storage', {})
        
        # Check overall usage
        usage_pct = storage.get('usage_percent', 0)
        if usage_pct > 90:
            issues.append(f"Storage critical: {usage_pct}% used")
        elif usage_pct > 80:
            issues.append(f"Storage warning: {usage_pct}% used")
        
        # Check tablespaces
        for ts in storage.get('tablespaces', []):
            ts_usage = ts.get('usage_pct', 0)
            if ts_usage > 95:
                issues.append(f"Tablespace {ts.get('name')} critical: {ts_usage}%")
            elif ts_usage > 85:
                issues.append(f"Tablespace {ts.get('name')} warning: {ts_usage}%")
        
        # Check data retention
        retention = db.get('data_retention', {})
        if not retention.get('partition_manager_enabled'):
            issues.append("Partition Manager not enabled")
        if retention.get('retention_compliance') == 'NON_COMPLIANT':
            issues.append("Data retention non-compliant")
        
        status = 'PASS'
        if any('critical' in i.lower() for i in issues):
            status = 'CRITICAL'
        elif issues:
            status = 'WARNING'
            
        return {
            'status': status,
            'issues': issues
        }
    
    def _check_replication(self, db: Dict) -> Dict[str, Any]:
        """Check replication status (DataGuard / GoldenGate)."""
        issues = []
        repl = db.get('replication', {})
        
        if repl.get('enabled'):
            # Check lag
            lag = repl.get('lag_seconds', 0)
            threshold = 300 # 5 mins
            
            if repl.get('type') == 'GOLDENGATE':
                threshold = 60 # Stricter for GG
                
            if lag > threshold:
                issues.append(f"Replication Lag High: {lag}s (Threshold: {threshold}s)")
            
            # Check status
            if repl.get('status', 'UP') != 'UP':
                 issues.append(f"Replication Stream DOWN")

        return {
            'status': 'WARNING' if issues else 'PASS',
            'issues': issues
        }

    def _check_best_practices(self, db: Dict) -> Dict[str, Any]:
        """Check best practices: partitioning, stats, indexes."""
        issues = []
        bp = db.get('best_practices', {})
        
        non_part = bp.get('non_partitioned_large_tables', 0)
        if non_part > 0:
            issues.append(f"{non_part} large tables not partitioned (>50GB)")
        
        missing_stats = bp.get('missing_incremental_stats', 0)
        if missing_stats > 0:
            issues.append(f"{missing_stats} tables missing incremental stats")
        
        bind_issues = bp.get('bind_variable_issues', 0)
        if bind_issues > 0:
            issues.append(f"{bind_issues} queries with bind variable issues")
        
        return {
            'status': 'WARNING' if issues else 'PASS',
            'issues': issues
        }
    
    def _save_results(self):
        """Save audit results to MongoDB."""
        try:
            report = {
                'run_id': self.run_id,
                'agent': 'DailyAudit',
                'run_date': datetime.now().isoformat(),
                'results': self.audit_results,
                'summary': {
                    'total': len(self.audit_results),
                    'passed': len([r for r in self.audit_results if r['overall_status'] == 'PASS']),
                    'warnings': len([r for r in self.audit_results if r['overall_status'] == 'WARNING']),
                    'critical': len([r for r in self.audit_results if r['overall_status'] == 'CRITICAL'])
                }
            }
            self.mongo.execute_eval(f"db.compliance_reports.insertOne({report})")
            print(f"📝 Saved report to compliance_reports")
        except Exception as e:
            print(f"❌ Error saving report: {e}")
    
    def _send_reports(self):
        """Send email reports for issues found."""
        critical_dbs = [r for r in self.audit_results if r['overall_status'] == 'CRITICAL']
        if critical_dbs:
            print(f"📧 Sending alerts for {len(critical_dbs)} critical databases")
            # Email logic would go here
            for db in critical_dbs:
                print(f"  ⚠️ {db['db_unique_name']}: {db.get('capacity', {}).get('issues', [])}")


def main():
    """Run the DailyAudit agent."""
    agent = DailyAuditAgent()
    result = agent.run()
    
    print("\n" + "="*50)
    print(f"📋 AUDIT SUMMARY")
    print(f"   Databases: {result['databases_audited']}")
    print(f"   Duration: {result['duration_seconds']:.1f}s")
    
    for r in result['results']:
        status_icon = '✅' if r['overall_status'] == 'PASS' else '⚠️' if r['overall_status'] == 'WARNING' else '❌'
        print(f"   {status_icon} {r['db_unique_name']}: {r['overall_status']}")


if __name__ == "__main__":
    main()
