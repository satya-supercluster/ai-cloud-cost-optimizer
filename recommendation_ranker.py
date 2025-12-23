"""
Recommendation Ranker
Scores and ranks recommendations
"""
from typing import List
from models import Recommendation, ProjectProfile, UsagePattern
from config import SCORING_WEIGHTS, RISK_LEVELS, COMPLEXITY_LEVELS
import logging

logger = logging.getLogger(__name__)


class RecommendationRanker:
    """Ranks recommendations based on multiple factors"""
    
    def __init__(self):
        self.weights = SCORING_WEIGHTS
        self.risk_scores = RISK_LEVELS
        self.complexity_scores = COMPLEXITY_LEVELS
    
    def rank_recommendations(
        self,
        recommendations: List[Recommendation],
        profile: ProjectProfile,
        usage_pattern: UsagePattern
    ) -> List[Recommendation]:
        """
        Score and rank all recommendations
        """
        # Score each recommendation
        for rec in recommendations:
            rec.score = self._calculate_score(rec, profile, usage_pattern)
        
        # Sort by score (highest first)
        ranked = sorted(recommendations, key=lambda x: x.score, reverse=True)
        
        logger.info(f"Ranked {len(ranked)} recommendations")
        return ranked
    
    def _calculate_score(
        self,
        rec: Recommendation,
        profile: ProjectProfile,
        usage_pattern: UsagePattern
    ) -> float:
        """
        Calculate recommendation score
        
        Formula: score = (savings * w1) - (risk * w2) - (complexity * w3) + workload_match
        """
        # Normalize savings (0-100 scale)
        max_savings = 20000  # Assume max potential savings
        normalized_savings = min(rec.expected_savings_inr / max_savings * 100, 100)
        
        # Get risk and complexity scores
        risk_score = self.risk_scores.get(rec.risk.value, 2)
        complexity_score = self.complexity_scores.get(rec.complexity.value, 2)
        
        # Calculate base score
        base_score = (
            normalized_savings * self.weights["savings"] +
            risk_score * self.weights["risk"] +
            complexity_score * self.weights["complexity"]
        )
        
        # Add workload match bonus
        workload_bonus = self._calculate_workload_match(rec, profile, usage_pattern)
        
        # Add urgency bonus for over-budget projects
        urgency_bonus = 0
        if profile.monthly_budget_inr < 0:  # Over budget
            urgency_bonus = 10
        
        final_score = base_score + workload_bonus + urgency_bonus
        
        return round(final_score, 2)
    
    def _calculate_workload_match(
        self,
        rec: Recommendation,
        profile: ProjectProfile,
        usage_pattern: UsagePattern
    ) -> float:
        """
        Calculate how well recommendation matches workload
        """
        bonus = 0
        title_lower = rec.title.lower()
        service_lower = rec.service.lower()
        
        # Auto-scaling bonus for variable traffic
        if "auto" in title_lower or "scaling" in title_lower:
            if usage_pattern.scaling_need in ["auto-scale-required", "horizontal-scaling"]:
                bonus += 15
        
        # Database optimization bonus for DB-heavy workloads
        if "database" in service_lower or "rds" in service_lower:
            if usage_pattern.db_load in ["read-heavy", "write-heavy"]:
                bonus += 12
        
        # Storage optimization bonus for storage-intensive apps
        if "storage" in service_lower or "s3" in title_lower:
            if "image" in str(profile.features).lower() or "upload" in str(profile.features).lower():
                bonus += 10
        
        # CDN bonus for high-traffic apps
        if "cdn" in title_lower or "cloudfront" in title_lower:
            if profile.expected_users > 50000:
                bonus += 12
        
        # Monitoring optimization for mature projects
        if "monitoring" in service_lower or "log" in title_lower:
            if profile.expected_users > 100000:
                bonus += 8
        
        # Spot instance bonus for batch workloads
        if "spot" in title_lower:
            if "analytics" in profile.features or "batch" in str(profile.features).lower():
                bonus += 15
        
        # ARM instance bonus for compatible workloads
        if "arm" in title_lower or "graviton" in title_lower:
            # Most workloads can benefit
            bonus += 10
        
        return bonus
    
    def get_quick_wins(self, recommendations: List[Recommendation], top_n: int = 3) -> List[Recommendation]:
        """
        Get quick win recommendations
        (Low complexity + Low risk + Good savings)
        """
        quick_wins = [
            rec for rec in recommendations
            if rec.complexity.value == "Low" and rec.risk.value == "Low"
        ]
        
        # Sort by savings
        quick_wins.sort(key=lambda x: x.expected_savings_inr, reverse=True)
        
        return quick_wins[:top_n]
    
    def get_high_impact(self, recommendations: List[Recommendation], top_n: int = 3) -> List[Recommendation]:
        """
        Get high-impact recommendations
        (Highest savings regardless of complexity)
        """
        sorted_recs = sorted(
            recommendations,
            key=lambda x: x.expected_savings_inr,
            reverse=True
        )
        
        return sorted_recs[:top_n]
    
    def filter_by_risk(
        self,
        recommendations: List[Recommendation],
        max_risk: str = "Medium"
    ) -> List[Recommendation]:
        """
        Filter recommendations by maximum acceptable risk
        """
        risk_order = {"Low": 1, "Medium": 2, "High": 3}
        max_risk_level = risk_order.get(max_risk, 2)
        
        filtered = [
            rec for rec in recommendations
            if risk_order.get(rec.risk.value, 3) <= max_risk_level
        ]
        
        return filtered
    
    def group_by_service(self, recommendations: List[Recommendation]) -> dict:
        """
        Group recommendations by service
        """
        groups = {}
        
        for rec in recommendations:
            service = rec.service
            if service not in groups:
                groups[service] = []
            groups[service].append(rec)
        
        return groups
    
    def calculate_total_savings(self, recommendations: List[Recommendation]) -> float:
        """
        Calculate total potential savings
        """
        return sum(rec.expected_savings_inr for rec in recommendations)
    
    def get_implementation_roadmap(
        self,
        recommendations: List[Recommendation]
    ) -> dict:
        """
        Create implementation roadmap by complexity and impact
        """
        roadmap = {
            "immediate": [],  # Low complexity, low risk
            "short_term": [],  # Medium complexity or risk
            "long_term": []  # High complexity or risk
        }
        
        for rec in recommendations:
            complexity_score = self.complexity_scores.get(rec.complexity.value, 2)
            risk_score = self.risk_scores.get(rec.risk.value, 2)
            total_score = complexity_score + risk_score
            
            if total_score <= 2:
                roadmap["immediate"].append(rec)
            elif total_score <= 4:
                roadmap["short_term"].append(rec)
            else:
                roadmap["long_term"].append(rec)
        
        return roadmap