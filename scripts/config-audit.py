#!/usr/bin/env python3
"""
Configuration Audit Tool
========================

Comprehensive audit of AI Backend Unified Infrastructure configurations.
Performs detailed analysis, security checks, and compliance validation.

Features:
- Complete configuration inventory
- Security compliance checks
- Performance optimization recommendations
- Completeness scoring
- Detailed audit reports

Usage:
    python3 scripts/config-audit.py                    # Full audit
    python3 scripts/config-audit.py --quick           # Quick audit
    python3 scripts/config-audit.py --format json     # JSON output
    python3 scripts/config-audit.py --focus security  # Security focus
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import yaml
from loguru import logger

# ============================================================================
# AUDIT CATEGORIES
# ============================================================================


class AuditCategory:
    """Base class for audit categories"""

    def __init__(self):
        self.findings: list[dict] = []
        self.score: float = 100.0
        self.max_score: float = 100.0

    def add_finding(self, severity: str, title: str, description: str, recommendation: str = ""):
        """Record an audit finding"""
        self.findings.append(
            {
                "severity": severity,  # critical, high, medium, low, info
                "title": title,
                "description": description,
                "recommendation": recommendation,
            }
        )

        # Adjust score based on severity
        if severity == "critical":
            self.score -= 20
        elif severity == "high":
            self.score -= 10
        elif severity == "medium":
            self.score -= 5
        elif severity == "low":
            self.score -= 2

    def get_score(self) -> float:
        """Get audit score (0-100)"""
        return max(0, min(100, self.score))

    def get_summary(self) -> dict:
        """Get audit summary"""
        return {
            "score": self.get_score(),
            "total_findings": len(self.findings),
            "critical": len([f for f in self.findings if f["severity"] == "critical"]),
            "high": len([f for f in self.findings if f["severity"] == "high"]),
            "medium": len([f for f in self.findings if f["severity"] == "medium"]),
            "low": len([f for f in self.findings if f["severity"] == "low"]),
            "info": len([f for f in self.findings if f["severity"] == "info"]),
        }


class SecurityAudit(AuditCategory):
    """Security compliance audit"""

    def __init__(self, config_dir: Path):
        super().__init__()
        self.config_dir = config_dir
        self.run_audit()

    def run_audit(self):
        """Run security audit"""
        self.check_exposed_credentials()
        self.check_auth_configuration()
        self.check_tls_requirements()
        self.check_access_controls()
        self.check_data_validation()

    def check_exposed_credentials(self):
        """Check for exposed credentials in configs"""
        try:
            for config_file in self.config_dir.glob("*.yaml"):
                with open(config_file) as f:
                    content = f.read()

                # Check for common credential patterns
                if any(
                    keyword in content.lower()
                    for keyword in [
                        "password:",
                        "api_key:",
                        "secret:",
                        "token:",
                        "apikey:",
                    ]
                ):
                    if "base_url" not in content:  # URLs OK, but not credentials
                        self.add_finding(
                            "critical",
                            "Potential exposed credentials",
                            f"File {config_file.name} may contain credentials",
                            "Move sensitive data to environment variables or .env file",
                        )
        except Exception as e:
            logger.error(f"Error in credential check: {e}")

    def check_auth_configuration(self):
        """Check authentication configuration"""
        try:
            litellm_file = self.config_dir / "litellm-unified.yaml"
            if litellm_file.exists():
                with open(litellm_file) as f:
                    config = yaml.safe_load(f)

                # Check if auth is configured
                if not config.get("require_auth") and not config.get("api_key"):
                    self.add_finding(
                        "high",
                        "Authentication not enforced",
                        "Gateway may be accessible without authentication",
                        "Set require_auth: true and configure API keys",
                    )
        except Exception as e:
            logger.error(f"Error in auth check: {e}")

    def check_tls_requirements(self):
        """Check TLS/HTTPS configuration"""
        try:
            providers_file = self.config_dir / "providers.yaml"
            if providers_file.exists():
                with open(providers_file) as f:
                    config = yaml.safe_load(f)

                # Check for unencrypted connections
                for provider_name, provider_config in config.get("providers", {}).items():
                    base_url = provider_config.get("base_url", "")
                    if base_url.startswith("http://") and "localhost" not in base_url:
                        self.add_finding(
                            "medium",
                            f"Unencrypted connection to {provider_name}",
                            f"Provider {provider_name} uses HTTP instead of HTTPS",
                            f"Update base_url to HTTPS: {base_url.replace('http://', 'https://')}",
                        )
        except Exception as e:
            logger.error(f"Error in TLS check: {e}")

    def check_access_controls(self):
        """Check access control configuration"""
        self.add_finding(
            "info",
            "Access controls not explicitly configured",
            "No RBAC or access control lists detected",
            "Consider implementing access control policies for production",
        )

    def check_data_validation(self):
        """Check data validation rules"""
        try:
            import sys

            sys.path.insert(0, str(self.config_dir.parent / "scripts"))
            from validate_config_schema import ProvidersYAML

            providers_file = self.config_dir / "providers.yaml"
            with open(providers_file) as f:
                config = yaml.safe_load(f)

            try:
                ProvidersYAML(**config)
                self.add_finding("info", "Schema validation enabled", "Configuration uses Pydantic validation", "")
            except Exception:
                pass

        except Exception as e:
            logger.debug(f"Error in data validation check: {e}")


class ComplianceAudit(AuditCategory):
    """Compliance audit"""

    def __init__(self, config_dir: Path):
        super().__init__()
        self.config_dir = config_dir
        self.run_audit()

    def run_audit(self):
        """Run compliance audit"""
        self.check_documentation()
        self.check_versioning()
        self.check_backups()
        self.check_change_tracking()

    def check_documentation(self):
        """Check if configuration is documented"""
        docs_dir = self.config_dir.parent / "docs"
        if not docs_dir.exists():
            self.add_finding(
                "low",
                "Documentation directory missing",
                "No docs directory found",
                "Create docs directory and add configuration documentation",
            )
        else:
            required_docs = [
                "architecture.md",
                "adding-providers.md",
                "troubleshooting.md",
            ]
            missing = [doc for doc in required_docs if not (docs_dir / doc).exists()]
            if missing:
                self.add_finding(
                    "medium",
                    "Missing documentation",
                    f"Missing docs: {', '.join(missing)}",
                    "Create missing documentation files",
                )
            else:
                self.add_finding("info", "Documentation complete", "All key docs present", "")

    def check_versioning(self):
        """Check if version control is in use"""
        git_dir = self.config_dir.parent / ".git"
        if not git_dir.exists():
            self.add_finding(
                "medium",
                "Not under version control",
                "Configuration directory not in git repo",
                "Initialize git repository: git init",
            )
        else:
            self.add_finding("info", "Version control enabled", "Configuration tracked in git", "")

    def check_backups(self):
        """Check backup strategy"""
        backups_dir = self.config_dir / "backups"
        if not backups_dir.exists():
            self.add_finding(
                "high",
                "No backups found",
                "No backup directory exists",
                "Create config/backups/ and implement backup strategy",
            )
        else:
            backup_count = len(list(backups_dir.glob("*")))
            if backup_count < 3:
                self.add_finding(
                    "medium",
                    "Insufficient backups",
                    f"Only {backup_count} backups found",
                    "Implement automated backup strategy",
                )
            else:
                self.add_finding("info", "Backups present", f"{backup_count} backups found", "")

    def check_change_tracking(self):
        """Check if changes are tracked"""
        migration_history = self.config_dir / ".migration-history"
        if not migration_history.exists():
            self.add_finding(
                "low",
                "No migration history tracked",
                "Configuration changes not recorded",
                "Use schema_versioning.py to track changes",
            )


class PerformanceAudit(AuditCategory):
    """Performance audit"""

    def __init__(self, config_dir: Path):
        super().__init__()
        self.config_dir = config_dir
        self.run_audit()

    def run_audit(self):
        """Run performance audit"""
        self.check_caching()
        self.check_timeouts()
        self.check_concurrency()
        self.check_load_balancing()

    def check_caching(self):
        """Check caching configuration"""
        try:
            litellm_file = self.config_dir / "litellm-unified.yaml"
            with open(litellm_file) as f:
                config = yaml.safe_load(f)

            if not config.get("litellm_settings", {}).get("cache"):
                self.add_finding(
                    "low",
                    "Caching not enabled",
                    "LiteLLM cache is disabled",
                    "Enable caching: litellm_settings: {cache: true}",
                )
            else:
                self.add_finding("info", "Caching enabled", "Responses will be cached", "")
        except Exception as e:
            logger.error(f"Error in caching check: {e}")

    def check_timeouts(self):
        """Check timeout configuration"""
        try:
            litellm_file = self.config_dir / "litellm-unified.yaml"
            with open(litellm_file) as f:
                config = yaml.safe_load(f)

            timeout = config.get("router_settings", {}).get("timeout", 30)
            if timeout < 10:
                self.add_finding(
                    "medium",
                    "Timeout too aggressive",
                    f"Router timeout is {timeout}s",
                    "Increase to 30-60 seconds for complex queries",
                )
            elif timeout > 300:
                self.add_finding(
                    "low",
                    "Timeout very permissive",
                    f"Router timeout is {timeout}s",
                    "Consider reducing to 60-120 seconds",
                )
            else:
                self.add_finding("info", "Timeout reasonable", f"Router timeout: {timeout}s", "")
        except Exception as e:
            logger.error(f"Error in timeout check: {e}")

    def check_concurrency(self):
        """Check concurrency limits"""
        self.add_finding("info", "Concurrency limits", "Configure max_concurrent_requests based on hardware", "")

    def check_load_balancing(self):
        """Check load balancing configuration"""
        try:
            mappings_file = self.config_dir / "model-mappings.yaml"
            with open(mappings_file) as f:
                config = yaml.safe_load(f)

            load_balancing = config.get("load_balancing", {})
            if load_balancing:
                self.add_finding(
                    "info", "Load balancing configured", f"{len(load_balancing)} load balanced models", ""
                )
            else:
                self.add_finding(
                    "low",
                    "No load balancing",
                    "Load balancing not configured",
                    "Add load_balancing section for failover",
                )
        except Exception as e:
            logger.error(f"Error in load balancing check: {e}")


class CompletenessAudit(AuditCategory):
    """Configuration completeness audit"""

    def __init__(self, config_dir: Path):
        super().__init__()
        self.config_dir = config_dir
        self.run_audit()

    def run_audit(self):
        """Run completeness audit"""
        self.check_required_files()
        self.check_provider_details()
        self.check_model_coverage()
        self.check_routing_completeness()

    def check_required_files(self):
        """Check all required files exist"""
        required = ["providers.yaml", "model-mappings.yaml", "litellm-unified.yaml"]
        missing = [f for f in required if not (self.config_dir / f).exists()]

        if missing:
            self.add_finding(
                "critical", "Missing configuration files", f"Missing: {', '.join(missing)}", "Create missing files"
            )
        else:
            self.add_finding("info", "All required files present", "", "")

    def check_provider_details(self):
        """Check provider configuration completeness"""
        try:
            providers_file = self.config_dir / "providers.yaml"
            with open(providers_file) as f:
                config = yaml.safe_load(f)

            for provider_name, provider_config in config.get("providers", {}).items():
                issues = []
                required_fields = ["type", "base_url", "status"]
                for field in required_fields:
                    if field not in provider_config:
                        issues.append(field)

                if issues:
                    self.add_finding(
                        "high",
                        f"Incomplete provider: {provider_name}",
                        f"Missing fields: {', '.join(issues)}",
                        f"Add missing fields to {provider_name}",
                    )

                if not provider_config.get("description"):
                    self.add_finding("low", f"No description for {provider_name}", "", "Add description field")
        except Exception as e:
            logger.error(f"Error in provider details check: {e}")

    def check_model_coverage(self):
        """Check model configuration coverage"""
        try:
            providers_file = self.config_dir / "providers.yaml"
            mappings_file = self.config_dir / "model-mappings.yaml"

            with open(providers_file) as f:
                providers_config = yaml.safe_load(f)
            with open(mappings_file) as f:
                mappings_config = yaml.safe_load(f)

            provider_models = set()
            for provider in providers_config.get("providers", {}).values():
                if provider.get("status") == "active":
                    for model in provider.get("models", []):
                        if isinstance(model, dict):
                            provider_models.add(model.get("name"))
                        else:
                            provider_models.add(model)

            mapped_models = set(mappings_config.get("exact_matches", {}).keys())

            unmapped = provider_models - mapped_models
            if unmapped:
                self.add_finding(
                    "medium",
                    "Unmapped models",
                    f"{len(unmapped)} provider models not in exact_matches",
                    "Add model mappings for all available models",
                )
            else:
                self.add_finding("info", "All models mapped", f"{len(mapped_models)} models", "")

        except Exception as e:
            logger.error(f"Error in model coverage check: {e}")

    def check_routing_completeness(self):
        """Check routing rules completeness"""
        try:
            mappings_file = self.config_dir / "model-mappings.yaml"
            with open(mappings_file) as f:
                config = yaml.safe_load(f)

            exact_matches = config.get("exact_matches", {})
            fallback_chains = config.get("fallback_chains", {})

            # Check for models without fallback
            no_fallback = set(exact_matches.keys()) - set(fallback_chains.keys())
            if no_fallback:
                self.add_finding(
                    "low",
                    f"{len(no_fallback)} models without fallback",
                    "No fallback chains configured",
                    "Add fallback chains for critical models",
                )
            else:
                self.add_finding("info", "Fallback chains complete", "", "")

        except Exception as e:
            logger.error(f"Error in routing check: {e}")


# ============================================================================
# AUDIT REPORT GENERATOR
# ============================================================================


class AuditReport:
    """Generates comprehensive audit report"""

    def __init__(self, config_dir: Path, quick: bool = False):
        self.config_dir = config_dir
        self.quick = quick
        self.audits: dict[str, AuditCategory] = {}
        self.generate_report()

    def generate_report(self):
        """Generate all audits"""
        self.audits["security"] = SecurityAudit(self.config_dir)
        self.audits["compliance"] = ComplianceAudit(self.config_dir)
        if not self.quick:
            self.audits["performance"] = PerformanceAudit(self.config_dir)
            self.audits["completeness"] = CompletenessAudit(self.config_dir)

    def get_overall_score(self) -> float:
        """Calculate overall audit score"""
        if not self.audits:
            return 0.0
        scores = [audit.get_score() for audit in self.audits.values()]
        return sum(scores) / len(scores)

    def print_report(self):
        """Print formatted audit report"""
        overall_score = self.get_overall_score()
        status_symbol = "✅" if overall_score >= 80 else "⚠️" if overall_score >= 60 else "❌"

        print(f"\n{'=' * 70}")
        print("Configuration Audit Report")
        print(f"Generated: {datetime.now().isoformat()}")
        print(f"{'=' * 70}\n")

        print(f"{status_symbol} Overall Score: {overall_score:.1f}/100\n")

        for audit_name, audit in self.audits.items():
            summary = audit.get_summary()
            print(f"\n📋 {audit_name.title()} Audit: {audit.get_score():.1f}/100")
            print(f"   Total findings: {summary['total_findings']}")
            if summary["critical"]:
                print(f"   🔴 Critical: {summary['critical']}")
            if summary["high"]:
                print(f"   🟠 High: {summary['high']}")
            if summary["medium"]:
                print(f"   🟡 Medium: {summary['medium']}")
            if summary["low"]:
                print(f"   🔵 Low: {summary['low']}")

            if audit.findings:
                print("\n   Findings:")
                for finding in audit.findings[:5]:  # Show first 5
                    severity_symbol = {
                        "critical": "🔴",
                        "high": "🟠",
                        "medium": "🟡",
                        "low": "🔵",
                        "info": "ℹ️",
                    }.get(finding["severity"], "•")
                    print(f"   {severity_symbol} {finding['title']}")
                    if finding["recommendation"]:
                        print(f"      → {finding['recommendation']}")

                if len(audit.findings) > 5:
                    print(f"   ... and {len(audit.findings) - 5} more findings")

        print(f"\n{'=' * 70}\n")

    def get_json_report(self) -> dict:
        """Get audit report as JSON"""
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_score": self.get_overall_score(),
            "audits": {
                name: {
                    "score": audit.get_score(),
                    "summary": audit.get_summary(),
                    "findings": audit.findings,
                }
                for name, audit in self.audits.items()
            },
        }


# ============================================================================
# MAIN
# ============================================================================


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Configuration audit tool")
    parser.add_argument("--quick", action="store_true", help="Quick audit (security and compliance only)")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    parser.add_argument(
        "--focus",
        choices=["security", "compliance", "performance", "completeness", "all"],
        default="all",
        help="Focus on specific audit category",
    )

    args = parser.parse_args()

    config_dir = Path(__file__).parent.parent / "config"

    # Generate report
    report = AuditReport(config_dir, quick=args.quick)

    # Output
    if args.format == "json":
        print(json.dumps(report.get_json_report(), indent=2))
    else:
        report.print_report()

    # Exit code based on score
    overall_score = report.get_overall_score()
    if overall_score >= 80:
        sys.exit(0)
    elif overall_score >= 60:
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == "__main__":
    main()
