"""
Optimizer Orchestrator
Main workflow coordinator
"""
from typing import List, Optional
from datetime import datetime
from models import (
    ProjectProfile, OptimizationReport, Recommendation,
    UsagePattern, CostEstimate
)
from cost_estimation_engine import CostEstimationEngine
from usage_pattern_analyzer import UsagePatternAnalyzer
from rule_based_optimizer import RuleBasedOptimizer
from llm_recommendation_engine import LLMRecommendationEngine
from recommendation_ranker import RecommendationRanker
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OptimizerOrchestrator:
    """
    Main orchestrator that coordinates all optimization components
    """
    
    def __init__(self, use_llm: bool = True):
        self.cost_engine = CostEstimationEngine()
        self.pattern_analyzer = UsagePatternAnalyzer()
        self.rule_optimizer = RuleBasedOptimizer()
        self.ranker = RecommendationRanker()
        
        self.use_llm = use_llm
        self.llm_engine = None
        
        if use_llm:
            try:
                self.llm_engine = LLMRecommendationEngine()
                logger.info("LLM engine initialized")
            except Exception as e:
                logger.warning(f"LLM initialization failed: {e}. Using rule-based only.")
                self.use_llm = False
    
    def optimize(
        self,
        profile: ProjectProfile,
        num_recommendations: int = 15,
        include_high_risk: bool = True
    ) -> OptimizationReport:
        """
        Main optimization workflow
        
        Steps:
        1. Estimate costs
        2. Analyze usage patterns
        3. Generate rule-based recommendations
        4. Generate LLM recommendations (if enabled)
        5. Merge and rank all recommendations
        6. Generate final report
        """
        logger.info(f"Starting optimization for: {profile.project_name}")
        
        # Step 1: Cost Estimation
        logger.info("Step 1: Estimating costs...")
        cost_estimate = self.cost_engine.estimate_costs(profile)
        logger.info(f"Total estimated cost: ₹{cost_estimate.total_monthly_cost:,.2f}")
        
        # Step 2: Usage Pattern Analysis
        logger.info("Step 2: Analyzing usage patterns...")
        usage_pattern = self.pattern_analyzer.analyze(profile)
        
        # Step 3: Rule-Based Recommendations
        logger.info("Step 3: Generating rule-based recommendations...")
        rule_recommendations = self.rule_optimizer.generate_recommendations(
            profile, cost_estimate, usage_pattern
        )
        logger.info(f"Generated {len(rule_recommendations)} rule-based recommendations")
        
        # Step 4: LLM Recommendations (if enabled)
        llm_recommendations = []
        if self.use_llm and self.llm_engine:
            try:
                logger.info("Step 4: Generating LLM recommendations...")
                llm_count = max(5, num_recommendations - len(rule_recommendations))
                llm_recommendations = self.llm_engine.generate_recommendations(
                    profile,
                    cost_estimate,
                    usage_pattern,
                    num_recommendations=llm_count,
                    baseline_recommendations=rule_recommendations
                )
                logger.info(f"Generated {len(llm_recommendations)} LLM recommendations")
            except Exception as e:
                logger.error(f"LLM generation failed: {e}")
        
        # Step 5: Merge and Rank
        logger.info("Step 5: Merging and ranking recommendations...")
        all_recommendations = rule_recommendations + llm_recommendations
        
        # Remove duplicates by title similarity
        all_recommendations = self._deduplicate_recommendations(all_recommendations)
        
        # Rank recommendations
        ranked_recommendations = self.ranker.rank_recommendations(
            all_recommendations, profile, usage_pattern
        )
        
        # Filter by risk if needed
        if not include_high_risk:
            ranked_recommendations = self.ranker.filter_by_risk(
                ranked_recommendations, max_risk="Medium"
            )
        
        # Limit to requested number
        final_recommendations = ranked_recommendations[:num_recommendations]
        
        # Step 6: Generate Report
        logger.info("Step 6: Generating final report...")
        report = self._generate_report(
            profile,
            cost_estimate,
            usage_pattern,
            final_recommendations
        )
        
        logger.info("Optimization complete!")
        return report
    
    def _deduplicate_recommendations(
        self,
        recommendations: List[Recommendation]
    ) -> List[Recommendation]:
        """
        Remove duplicate recommendations based on title similarity
        """
        seen_titles = set()
        unique_recommendations = []
        
        for rec in recommendations:
            # Normalize title for comparison
            normalized_title = rec.title.lower().strip()
            
            # Check for similar titles
            is_duplicate = False
            for seen_title in seen_titles:
                if self._are_titles_similar(normalized_title, seen_title):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                seen_titles.add(normalized_title)
                unique_recommendations.append(rec)
        
        logger.info(f"Deduplicated: {len(recommendations)} -> {len(unique_recommendations)}")
        return unique_recommendations
    
    def _are_titles_similar(self, title1: str, title2: str) -> bool:
        """
        Check if two titles are similar (simple approach)
        """
        # Split into words
        words1 = set(title1.split())
        words2 = set(title2.split())
        
        # Calculate Jaccard similarity
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        if not union:
            return False
        
        similarity = len(intersection) / len(union)
        return similarity > 0.6  # 60% similarity threshold
    
    def _generate_report(
        self,
        profile: ProjectProfile,
        cost_estimate: CostEstimate,
        usage_pattern: UsagePattern,
        recommendations: List[Recommendation]
    ) -> OptimizationReport:
        """
        Generate final optimization report
        """
        # Determine status
        if cost_estimate.total_monthly_cost <= profile.monthly_budget_inr:
            status = "Within Budget"
        else:
            status = "Over Budget"
        
        # Calculate total potential savings
        total_savings = self.ranker.calculate_total_savings(recommendations)
        
        # Get top 3 quick wins
        quick_wins = self.ranker.get_quick_wins(recommendations, top_n=3)
        
        report = OptimizationReport(
            project=profile.project_name,
            budget=profile.monthly_budget_inr,
            estimated_cost=cost_estimate.total_monthly_cost,
            status=status,
            cost_breakdown=cost_estimate.service_costs,
            usage_patterns=usage_pattern,
            recommendations=recommendations,
            total_potential_savings=total_savings,
            top_3_quick_wins=quick_wins,
            generated_at=datetime.now().isoformat()
        )
        
        return report
    
    def get_summary(self, report: OptimizationReport) -> str:
        """
        Generate human-readable summary
        """
        lines = []
        lines.append("=" * 80)
        lines.append(f"Cloud Cost Optimization Report: {report.project}")
        lines.append("=" * 80)
        lines.append("")
        
        # Budget overview
        lines.append("📊 Budget Overview:")
        lines.append(f"   Monthly Budget: ₹{report.budget:,.2f}")
        lines.append(f"   Estimated Cost: ₹{report.estimated_cost:,.2f}")
        lines.append(f"   Status: {report.status}")
        
        if report.estimated_cost <= report.budget:
            remaining = report.budget - report.estimated_cost
            lines.append(f"   Remaining: ₹{remaining:,.2f}")
        else:
            overspend = report.estimated_cost - report.budget
            lines.append(f"   Over Budget: ₹{overspend:,.2f}")
        
        lines.append("")
        
        # Cost breakdown
        lines.append("💰 Cost Breakdown:")
        costs = report.cost_breakdown
        if costs.EC2 > 0:
            lines.append(f"   EC2: ₹{costs.EC2:,.2f}")
        if costs.RDS > 0:
            lines.append(f"   RDS: ₹{costs.RDS:,.2f}")
        if costs.Storage > 0:
            lines.append(f"   Storage: ₹{costs.Storage:,.2f}")
        if costs.LoadBalancer > 0:
            lines.append(f"   Load Balancer: ₹{costs.LoadBalancer:,.2f}")
        if costs.Monitoring > 0:
            lines.append(f"   Monitoring: ₹{costs.Monitoring:,.2f}")
        
        lines.append("")
        
        # Savings potential
        lines.append("💡 Optimization Potential:")
        lines.append(f"   Total Potential Savings: ₹{report.total_potential_savings:,.2f}/month")
        lines.append(f"   Number of Recommendations: {len(report.recommendations)}")
        
        lines.append("")
        
        # Quick wins
        if report.top_3_quick_wins:
            lines.append("🚀 Top Quick Wins:")
            for i, rec in enumerate(report.top_3_quick_wins, 1):
                lines.append(f"   {i}. {rec.title}")
                lines.append(f"      Savings: ₹{rec.expected_savings_inr:,.2f} | Risk: {rec.risk.value} | Complexity: {rec.complexity.value}")
        
        lines.append("")
        lines.append("=" * 80)
        
        return "\n".join(lines)