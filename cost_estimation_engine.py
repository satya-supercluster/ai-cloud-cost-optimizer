"""
Cost Estimation Engine
Calculates cloud infrastructure costs based on configuration
"""
from typing import Dict, Tuple
from models import ProjectProfile, ServiceCost, CostEstimate
from config import PRICING, REGIONS
import logging

logger = logging.getLogger(__name__)


class CostEstimationEngine:
    """Estimates monthly cloud costs"""
    
    def __init__(self):
        self.pricing = PRICING
        self.regions = REGIONS
    
    def estimate_costs(self, profile: ProjectProfile) -> CostEstimate:
        """
        Main method to estimate all costs
        """
        region_multiplier = self.regions.get(profile.region, {}).get("multiplier", 1.0)
        
        # Calculate individual service costs
        ec2_cost = self._calculate_ec2_cost(profile, region_multiplier)
        rds_cost = self._calculate_rds_cost(profile, region_multiplier)
        storage_cost = self._calculate_storage_cost(profile, region_multiplier)
        lb_cost = self._calculate_load_balancer_cost(profile, region_multiplier)
        cdn_cost = self._calculate_cdn_cost(profile, region_multiplier)
        monitoring_cost = self._calculate_monitoring_cost(profile, region_multiplier)
        data_transfer_cost = self._calculate_data_transfer_cost(profile, region_multiplier)
        
        service_costs = ServiceCost(
            EC2=ec2_cost,
            RDS=rds_cost,
            Storage=storage_cost,
            LoadBalancer=lb_cost,
            CDN=cdn_cost,
            Monitoring=monitoring_cost,
            DataTransfer=data_transfer_cost
        )
        
        total_cost = sum([
            ec2_cost, rds_cost, storage_cost, lb_cost,
            cdn_cost, monitoring_cost, data_transfer_cost
        ])
        
        budget = profile.monthly_budget_inr
        remaining = budget - total_cost
        utilization = (total_cost / budget * 100) if budget > 0 else 0
        
        return CostEstimate(
            service_costs=service_costs,
            total_monthly_cost=total_cost,
            budget=budget,
            remaining_budget=remaining,
            budget_utilization_percent=utilization
        )
    
    def _calculate_ec2_cost(self, profile: ProjectProfile, multiplier: float) -> float:
        """Calculate EC2 instance costs"""
        instance_type = profile.current_infra.instance_type
        num_instances = profile.current_infra.ec2_instances
        
        cost_per_instance = self.pricing["EC2"].get(instance_type, 28000)
        total_cost = cost_per_instance * num_instances * multiplier
        
        logger.info(f"EC2 Cost: {num_instances}x {instance_type} = ₹{total_cost:,.2f}")
        return total_cost
    
    def _calculate_rds_cost(self, profile: ProjectProfile, multiplier: float) -> float:
        """Calculate RDS database costs"""
        if not profile.current_infra.rds:
            return 0
        
        instance_type = profile.current_infra.rds
        cost = self.pricing["RDS"].get(instance_type, 40000)
        total_cost = cost * multiplier
        
        # Add storage cost (assume 100GB default)
        storage_gb = 100
        storage_cost = storage_gb * self.pricing["STORAGE"]["ebs_gp3_gb"]
        total_cost += storage_cost
        
        logger.info(f"RDS Cost: {instance_type} + {storage_gb}GB = ₹{total_cost:,.2f}")
        return total_cost
    
    def _calculate_storage_cost(self, profile: ProjectProfile, multiplier: float) -> float:
        """Calculate object storage costs"""
        storage_gb = profile.current_infra.storage_gb or 100
        
        # Estimate based on features
        if "image uploads" in profile.features:
            storage_gb *= 2
        if "analytics" in profile.features:
            storage_gb *= 1.5
        
        cost_per_gb = self.pricing["STORAGE"]["object_storage_gb"]
        total_cost = storage_gb * cost_per_gb * multiplier
        
        logger.info(f"Storage Cost: {storage_gb}GB = ₹{total_cost:,.2f}")
        return total_cost
    
    def _calculate_load_balancer_cost(self, profile: ProjectProfile, multiplier: float) -> float:
        """Calculate load balancer costs"""
        if not profile.current_infra.load_balancer:
            return 0
        
        base_cost = self.pricing["NETWORK"]["load_balancer"]
        
        # Add LCU costs based on traffic
        if profile.traffic_pattern == "peak_hours":
            base_cost *= 1.3
        elif profile.traffic_pattern == "bursty":
            base_cost *= 1.5
        
        total_cost = base_cost * multiplier
        logger.info(f"Load Balancer Cost: ₹{total_cost:,.2f}")
        return total_cost
    
    def _calculate_cdn_cost(self, profile: ProjectProfile, multiplier: float) -> float:
        """Calculate CDN costs"""
        if not profile.current_infra.cdn:
            return 0
        
        # Estimate data transfer
        expected_users = profile.expected_users
        avg_data_per_user = 50  # MB per month
        
        total_gb = (expected_users * avg_data_per_user) / 1024
        cost_per_gb = self.pricing["NETWORK"]["cdn_gb"]
        
        total_cost = total_gb * cost_per_gb * multiplier
        logger.info(f"CDN Cost: {total_gb:.2f}GB = ₹{total_cost:,.2f}")
        return total_cost
    
    def _calculate_monitoring_cost(self, profile: ProjectProfile, multiplier: float) -> float:
        """Calculate monitoring and logging costs"""
        monitoring_level = profile.current_infra.monitoring
        
        if monitoring_level == "advanced":
            base_cost = self.pricing["MONITORING"]["advanced"]
        else:
            base_cost = self.pricing["MONITORING"]["basic"]
        
        # Add custom metrics cost
        num_services = 3 + len(profile.features)
        custom_metrics_cost = num_services * self.pricing["MONITORING"]["custom_metrics"]
        
        total_cost = (base_cost + custom_metrics_cost) * multiplier
        logger.info(f"Monitoring Cost: ₹{total_cost:,.2f}")
        return total_cost
    
    def _calculate_data_transfer_cost(self, profile: ProjectProfile, multiplier: float) -> float:
        """Calculate data transfer costs"""
        expected_users = profile.expected_users
        
        # Estimate data transfer
        avg_transfer_per_user = 100  # MB per month
        total_gb = (expected_users * avg_transfer_per_user) / 1024
        
        # First 100GB usually free, then charged
        billable_gb = max(0, total_gb - 100)
        cost_per_gb = self.pricing["NETWORK"]["data_transfer_gb"]
        
        total_cost = billable_gb * cost_per_gb * multiplier
        logger.info(f"Data Transfer Cost: {billable_gb:.2f}GB = ₹{total_cost:,.2f}")
        return total_cost
    
    def get_cost_breakdown_text(self, estimate: CostEstimate) -> str:
        """Format cost breakdown as text"""
        lines = []
        costs = estimate.service_costs
        
        if costs.EC2 > 0:
            lines.append(f"EC2: ₹{costs.EC2:,.2f}")
        if costs.RDS > 0:
            lines.append(f"RDS: ₹{costs.RDS:,.2f}")
        if costs.Storage > 0:
            lines.append(f"Storage: ₹{costs.Storage:,.2f}")
        if costs.LoadBalancer > 0:
            lines.append(f"Load Balancer: ₹{costs.LoadBalancer:,.2f}")
        if costs.CDN > 0:
            lines.append(f"CDN: ₹{costs.CDN:,.2f}")
        if costs.Monitoring > 0:
            lines.append(f"Monitoring: ₹{costs.Monitoring:,.2f}")
        if costs.DataTransfer > 0:
            lines.append(f"Data Transfer: ₹{costs.DataTransfer:,.2f}")
        
        return "\n".join(lines)