"""
Rule-Based Optimizer
Deterministic optimization rules
"""
from typing import List, Dict
from models import (
    ProjectProfile, UsagePattern, CostEstimate,
    Recommendation, RiskLevel, ComplexityLevel
)
from config import OPTIMIZATION_RULES, PRICING
import logging

logger = logging.getLogger(__name__)


class RuleBasedOptimizer:
    """Applies deterministic optimization rules"""
    
    def __init__(self):
        self.rules = OPTIMIZATION_RULES
        self.recommendations = []
        self.rec_id_counter = 1
    
    def generate_recommendations(
        self,
        profile: ProjectProfile,
        cost_estimate: CostEstimate,
        usage_pattern: UsagePattern
    ) -> List[Recommendation]:
        """
        Generate rule-based recommendations
        """
        self.recommendations = []
        self.rec_id_counter = 1
        
        # Apply all rule categories
        self._compute_recommendations(profile, cost_estimate, usage_pattern)
        self._database_recommendations(profile, cost_estimate, usage_pattern)
        self._storage_recommendations(profile, cost_estimate, usage_pattern)
        self._network_recommendations(profile, cost_estimate, usage_pattern)
        self._monitoring_recommendations(profile, cost_estimate, usage_pattern)
        
        logger.info(f"Generated {len(self.recommendations)} rule-based recommendations")
        return self.recommendations
    
    def _compute_recommendations(
        self,
        profile: ProjectProfile,
        cost_estimate: CostEstimate,
        usage_pattern: UsagePattern
    ):
        """Compute/EC2 related recommendations"""
        
        # Auto-scaling for variable traffic
        if usage_pattern.scaling_need in ["auto-scale-required", "horizontal-scaling"]:
            self._add_recommendation(
                title="Implement Auto Scaling Group",
                service="EC2",
                description="Replace fixed EC2 instances with Auto Scaling Group to handle variable load",
                savings=cost_estimate.service_costs.EC2 * 0.25,
                risk=RiskLevel.LOW,
                complexity=ComplexityLevel.MEDIUM,
                impact="Reduces costs during low-traffic periods while maintaining performance during peaks",
                steps=[
                    "Create Auto Scaling Group with min 1, max 4 instances",
                    "Set up target tracking scaling policy (CPU 70%)",
                    "Configure scale-in protection for critical instances",
                    "Test scaling behavior with load tests"
                ]
            )
        
        # ARM instances for cost savings
        if profile.current_infra.instance_type.startswith("t3"):
            arm_equivalent = profile.current_infra.instance_type.replace("t3", "t4g")
            if arm_equivalent in PRICING["EC2"]:
                savings = (PRICING["EC2"][profile.current_infra.instance_type] - 
                          PRICING["EC2"][arm_equivalent]) * profile.current_infra.ec2_instances
                
                self._add_recommendation(
                    title="Migrate to ARM-based Graviton Instances",
                    service="EC2",
                    description=f"Switch from {profile.current_infra.instance_type} to {arm_equivalent}",
                    savings=savings,
                    risk=RiskLevel.LOW,
                    complexity=ComplexityLevel.LOW,
                    impact="20% cost reduction with comparable performance",
                    steps=[
                        "Verify application compatibility with ARM64",
                        "Update Docker images to multi-arch builds",
                        f"Launch {arm_equivalent} instances",
                        "Gradually migrate traffic using load balancer"
                    ]
                )
        
        # Spot instances for non-critical workloads
        if "analytics" in profile.features or "batch" in str(profile.features).lower():
            self._add_recommendation(
                title="Use Spot Instances for Background Jobs",
                service="EC2",
                description="Run non-critical batch processing and analytics on spot instances",
                savings=cost_estimate.service_costs.EC2 * 0.40,
                risk=RiskLevel.MEDIUM,
                complexity=ComplexityLevel.MEDIUM,
                impact="Up to 70% cost reduction for interruptible workloads",
                steps=[
                    "Identify fault-tolerant workloads",
                    "Implement checkpointing for long-running jobs",
                    "Create spot fleet request with multiple instance types",
                    "Set up interruption handling"
                ]
            )
        
        # Instance right-sizing based on CPU pattern
        if usage_pattern.cpu_pattern == "moderate-cpu":
            current_type = profile.current_infra.instance_type
            size_map = {"xlarge": "large", "large": "medium", "medium": "small"}
            
            for size, smaller in size_map.items():
                if size in current_type:
                    smaller_type = current_type.replace(size, smaller)
                    if smaller_type in PRICING["EC2"]:
                        savings = (PRICING["EC2"][current_type] - 
                                  PRICING["EC2"][smaller_type]) * profile.current_infra.ec2_instances
                        
                        self._add_recommendation(
                            title="Downsize EC2 Instances",
                            service="EC2",
                            description=f"Reduce instance size from {current_type} to {smaller_type}",
                            savings=savings,
                            risk=RiskLevel.MEDIUM,
                            complexity=ComplexityLevel.LOW,
                            impact="May reduce capacity headroom, monitor closely",
                            steps=[
                                "Monitor current CPU/memory utilization for 1 week",
                                f"Launch test {smaller_type} instance",
                                "Run load tests to verify performance",
                                "Gradually migrate production traffic"
                            ]
                        )
                    break
    
    def _database_recommendations(
        self,
        profile: ProjectProfile,
        cost_estimate: CostEstimate,
        usage_pattern: UsagePattern
    ):
        """Database optimization recommendations"""
        
        if not profile.current_infra.rds:
            return
        
        # Read replicas for read-heavy workloads
        if usage_pattern.db_load == "read-heavy":
            self._add_recommendation(
                title="Add RDS Read Replicas",
                service="RDS",
                description="Offload read queries to read replicas",
                savings=cost_estimate.service_costs.RDS * 0.15,
                risk=RiskLevel.LOW,
                complexity=ComplexityLevel.MEDIUM,
                impact="Reduces primary DB load, improves read performance",
                steps=[
                    "Create 1-2 read replicas in same AZ",
                    "Update application to use replica endpoints for reads",
                    "Implement read/write connection splitting",
                    "Monitor replication lag"
                ]
            )
        
        # Connection pooling
        self._add_recommendation(
            title="Implement Database Connection Pooling",
            service="RDS",
            description="Use RDS Proxy or application-level pooling to reduce connections",
            savings=cost_estimate.service_costs.RDS * 0.10,
            risk=RiskLevel.LOW,
            complexity=ComplexityLevel.LOW,
            impact="Reduces database load and enables smaller instance sizes",
            steps=[
                "Analyze current connection count and patterns",
                "Set up RDS Proxy or configure PgBouncer/HikariCP",
                "Configure max connections based on instance type",
                "Test with production-like load"
            ]
        )
        
        # Storage autoscaling
        self._add_recommendation(
            title="Enable RDS Storage Autoscaling",
            service="RDS",
            description="Automatically scale storage based on usage",
            savings=1500,
            risk=RiskLevel.LOW,
            complexity=ComplexityLevel.LOW,
            impact="Pay only for storage you use, prevents over-provisioning",
            steps=[
                "Enable storage autoscaling in RDS settings",
                "Set maximum storage threshold",
                "Configure scaling threshold (e.g., 90% full)",
                "Monitor storage usage patterns"
            ]
        )
    
    def _storage_recommendations(
        self,
        profile: ProjectProfile,
        cost_estimate: CostEstimate,
        usage_pattern: UsagePattern
    ):
        """Storage optimization recommendations"""
        
        # Lifecycle policies for cold storage
        if usage_pattern.storage_access in ["mixed-hot-cold", "occasional-access"]:
            self._add_recommendation(
                title="Implement S3 Lifecycle Policies",
                service="Storage",
                description="Move infrequently accessed data to cheaper storage tiers",
                savings=cost_estimate.service_costs.Storage * 0.60,
                risk=RiskLevel.LOW,
                complexity=ComplexityLevel.LOW,
                impact="Significant storage cost reduction with minimal impact",
                steps=[
                    "Analyze object access patterns",
                    "Create lifecycle policy: Standard -> IA after 30 days",
                    "Archive to Glacier after 90 days",
                    "Test retrieval times for critical data"
                ]
            )
        
        # Compression for uploads
        if "image uploads" in profile.features or "upload" in str(profile.features).lower():
            self._add_recommendation(
                title="Enable Image Compression and Optimization",
                service="Storage",
                description="Compress and optimize images before storage",
                savings=cost_estimate.service_costs.Storage * 0.30,
                risk=RiskLevel.LOW,
                complexity=ComplexityLevel.MEDIUM,
                impact="Reduces storage and bandwidth costs",
                steps=[
                    "Implement server-side image optimization",
                    "Use WebP format for supported browsers",
                    "Generate multiple resolutions (thumbnails)",
                    "Store compressed versions in S3"
                ]
            )
        
        # S3 Intelligent Tiering
        self._add_recommendation(
            title="Use S3 Intelligent-Tiering",
            service="Storage",
            description="Automatically move objects between access tiers",
            savings=cost_estimate.service_costs.Storage * 0.40,
            risk=RiskLevel.LOW,
            complexity=ComplexityLevel.LOW,
            impact="Automatic cost optimization with no retrieval fees",
            steps=[
                "Enable Intelligent-Tiering on S3 bucket",
                "Configure archive access tiers",
                "Monitor cost savings in Cost Explorer",
                "No application changes required"
            ]
        )
    
    def _network_recommendations(
        self,
        profile: ProjectProfile,
        cost_estimate: CostEstimate,
        usage_pattern: UsagePattern
    ):
        """Network optimization recommendations"""
        
        # CDN for static content
        if not profile.current_infra.cdn:
            frontend = profile.tech_stack.frontend.lower()
            if "react" in frontend or "angular" in frontend or "vue" in frontend:
                self._add_recommendation(
                    title="Enable CloudFront CDN",
                    service="Network",
                    description="Serve static assets through CDN",
                    savings=cost_estimate.service_costs.DataTransfer * 0.50,
                    risk=RiskLevel.LOW,
                    complexity=ComplexityLevel.MEDIUM,
                    impact="Reduces origin load and data transfer costs",
                    steps=[
                        "Create CloudFront distribution",
                        "Configure S3 bucket as origin",
                        "Update DNS records",
                        "Enable compression and caching"
                    ]
                )
        
        # VPC endpoints
        self._add_recommendation(
            title="Use VPC Endpoints for AWS Services",
            service="Network",
            description="Eliminate data transfer costs for AWS service communication",
            savings=cost_estimate.service_costs.DataTransfer * 0.30,
            risk=RiskLevel.LOW,
            complexity=ComplexityLevel.LOW,
            impact="Removes NAT gateway data transfer charges",
            steps=[
                "Create VPC endpoints for S3, DynamoDB",
                "Update route tables",
                "Test connectivity from private subnets",
                "Monitor cost reduction"
            ]
        )
    
    def _monitoring_recommendations(
        self,
        profile: ProjectProfile,
        cost_estimate: CostEstimate,
        usage_pattern: UsagePattern
    ):
        """Monitoring and ops recommendations"""
        
        # Reduce log retention
        self._add_recommendation(
            title="Optimize CloudWatch Log Retention",
            service="Monitoring",
            description="Reduce log retention period for non-critical logs",
            savings=cost_estimate.service_costs.Monitoring * 0.40,
            risk=RiskLevel.LOW,
            complexity=ComplexityLevel.LOW,
            impact="Reduces storage costs while maintaining recent logs",
            steps=[
                "Identify log groups and current retention",
                "Set 7-day retention for debug logs",
                "Set 30-day retention for application logs",
                "Archive important logs to S3"
            ]
        )
        
        # Sampling for high-volume metrics
        if profile.expected_users > 50000:
            self._add_recommendation(
                title="Implement Metric Sampling",
                service="Monitoring",
                description="Sample metrics instead of logging every request",
                savings=cost_estimate.service_costs.Monitoring * 0.30,
                risk=RiskLevel.LOW,
                complexity=ComplexityLevel.MEDIUM,
                impact="Reduces monitoring costs with statistical accuracy",
                steps=[
                    "Implement 10% sampling for high-frequency metrics",
                    "Keep 100% sampling for errors and exceptions",
                    "Configure X-Ray sampling rules",
                    "Validate accuracy with dashboards"
                ]
            )
    
    def _add_recommendation(
        self,
        title: str,
        service: str,
        description: str,
        savings: float,
        risk: RiskLevel,
        complexity: ComplexityLevel,
        impact: str,
        steps: List[str]
    ):
        """Helper to add a recommendation"""
        rec = Recommendation(
            id=self.rec_id_counter,
            title=title,
            service=service,
            description=description,
            expected_savings_inr=round(savings, 2),
            risk=risk,
            complexity=complexity,
            impact=impact,
            implementation_steps=steps
        )
        self.recommendations.append(rec)
        self.rec_id_counter += 1