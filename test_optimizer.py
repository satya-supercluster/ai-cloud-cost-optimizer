"""
Unit Tests for Cloud Cost Optimizer
"""
import pytest
from models import (
    ProjectProfile, TechStack, CurrentInfrastructure,
    TrafficPattern, RiskLevel, ComplexityLevel
)
from cost_estimation_engine import CostEstimationEngine
from usage_pattern_analyzer import UsagePatternAnalyzer
from rule_based_optimizer import RuleBasedOptimizer
from recommendation_ranker import RecommendationRanker
from optimizer_orchestrator import OptimizerOrchestrator


@pytest.fixture
def sample_profile():
    """Sample project profile for testing"""
    return ProjectProfile(
        project_name="Test App",
        monthly_budget_inr=50000,
        expected_users=100000,
        traffic_pattern=TrafficPattern.PEAK_HOURS,
        region="ap-south-1",
        tech_stack=TechStack(
            backend="Spring Boot",
            frontend="React",
            database="PostgreSQL",
            cache="Redis",
            storage="Object Storage",
            auth="JWT"
        ),
        features=[
            "real-time tracking",
            "image uploads",
            "notifications"
        ],
        current_infra=CurrentInfrastructure(
            ec2_instances=2,
            instance_type="t3.medium",
            rds="db.t3.medium",
            load_balancer=True,
            cdn=False,
            storage_gb=500,
            monitoring="basic"
        )
    )


class TestCostEstimationEngine:
    """Test cost estimation"""
    
    def test_estimate_costs(self, sample_profile):
        """Test basic cost estimation"""
        engine = CostEstimationEngine()
        estimate = engine.estimate_costs(sample_profile)
        
        assert estimate.total_monthly_cost > 0
        assert estimate.service_costs.EC2 > 0
        assert estimate.service_costs.RDS > 0
        assert estimate.budget == sample_profile.monthly_budget_inr
    
    def test_ec2_cost_calculation(self, sample_profile):
        """Test EC2 cost calculation"""
        engine = CostEstimationEngine()
        estimate = engine.estimate_costs(sample_profile)
        
        # Should be 2 instances * t3.medium price
        expected_min = 28000 * 2 * 0.9  # With multiplier variance
        expected_max = 28000 * 2 * 1.1
        
        assert expected_min <= estimate.service_costs.EC2 <= expected_max
    
    def test_budget_calculation(self, sample_profile):
        """Test budget calculations"""
        engine = CostEstimationEngine()
        estimate = engine.estimate_costs(sample_profile)
        
        assert estimate.remaining_budget == estimate.budget - estimate.total_monthly_cost
        assert estimate.budget_utilization_percent >= 0


class TestUsagePatternAnalyzer:
    """Test usage pattern analysis"""
    
    def test_analyze_patterns(self, sample_profile):
        """Test pattern analysis"""
        analyzer = UsagePatternAnalyzer()
        pattern = analyzer.analyze(sample_profile)
        
        assert pattern.traffic_type is not None
        assert pattern.db_load is not None
        assert pattern.scaling_need is not None
    
    def test_peak_hours_detection(self, sample_profile):
        """Test peak hours detection for food delivery"""
        sample_profile.project_name = "Food Delivery App"
        analyzer = UsagePatternAnalyzer()
        pattern = analyzer.analyze(sample_profile)
        
        assert pattern.peak_hours is not None
        assert 12 in pattern.peak_hours or 19 in pattern.peak_hours  # Meal times
    
    def test_read_heavy_detection(self, sample_profile):
        """Test read-heavy workload detection"""
        sample_profile.features = ["analytics", "dashboard", "reporting"]
        analyzer = UsagePatternAnalyzer()
        pattern = analyzer.analyze(sample_profile)
        
        assert pattern.db_load == "read-heavy"


class TestRuleBasedOptimizer:
    """Test rule-based recommendations"""
    
    def test_generate_recommendations(self, sample_profile):
        """Test recommendation generation"""
        engine = CostEstimationEngine()
        analyzer = UsagePatternAnalyzer()
        optimizer = RuleBasedOptimizer()
        
        estimate = engine.estimate_costs(sample_profile)
        pattern = analyzer.analyze(sample_profile)
        
        recommendations = optimizer.generate_recommendations(
            sample_profile, estimate, pattern
        )
        
        assert len(recommendations) > 0
        for rec in recommendations:
            assert rec.title
            assert rec.service
            assert rec.expected_savings_inr >= 0
            assert rec.risk in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH]
    
    def test_autoscaling_recommendation(self, sample_profile):
        """Test autoscaling recommendation for peak hours traffic"""
        sample_profile.traffic_pattern = TrafficPattern.BURSTY
        
        engine = CostEstimationEngine()
        analyzer = UsagePatternAnalyzer()
        optimizer = RuleBasedOptimizer()
        
        estimate = engine.estimate_costs(sample_profile)
        pattern = analyzer.analyze(sample_profile)
        recommendations = optimizer.generate_recommendations(
            sample_profile, estimate, pattern
        )
        
        # Should recommend autoscaling
        titles = [r.title.lower() for r in recommendations]
        assert any("auto" in t and "scal" in t for t in titles)


class TestRecommendationRanker:
    """Test recommendation ranking"""
    
    def test_rank_recommendations(self, sample_profile):
        """Test ranking logic"""
        engine = CostEstimationEngine()
        analyzer = UsagePatternAnalyzer()
        optimizer = RuleBasedOptimizer()
        ranker = RecommendationRanker()
        
        estimate = engine.estimate_costs(sample_profile)
        pattern = analyzer.analyze(sample_profile)
        recommendations = optimizer.generate_recommendations(
            sample_profile, estimate, pattern
        )
        
        ranked = ranker.rank_recommendations(recommendations, sample_profile, pattern)
        
        # Check scores are assigned
        assert all(rec.score > 0 for rec in ranked)
        
        # Check descending order
        scores = [rec.score for rec in ranked]
        assert scores == sorted(scores, reverse=True)
    
    def test_quick_wins(self, sample_profile):
        """Test quick wins extraction"""
        engine = CostEstimationEngine()
        analyzer = UsagePatternAnalyzer()
        optimizer = RuleBasedOptimizer()
        ranker = RecommendationRanker()
        
        estimate = engine.estimate_costs(sample_profile)
        pattern = analyzer.analyze(sample_profile)
        recommendations = optimizer.generate_recommendations(
            sample_profile, estimate, pattern
        )
        
        ranked = ranker.rank_recommendations(recommendations, sample_profile, pattern)
        quick_wins = ranker.get_quick_wins(ranked, top_n=3)
        
        assert len(quick_wins) <= 3
        for rec in quick_wins:
            assert rec.risk == RiskLevel.LOW
            assert rec.complexity == ComplexityLevel.LOW
    
    def test_total_savings(self, sample_profile):
        """Test total savings calculation"""
        engine = CostEstimationEngine()
        analyzer = UsagePatternAnalyzer()
        optimizer = RuleBasedOptimizer()
        ranker = RecommendationRanker()
        
        estimate = engine.estimate_costs(sample_profile)
        pattern = analyzer.analyze(sample_profile)
        recommendations = optimizer.generate_recommendations(
            sample_profile, estimate, pattern
        )
        
        total = ranker.calculate_total_savings(recommendations)
        expected = sum(r.expected_savings_inr for r in recommendations)
        
        assert total == expected
        assert total > 0


class TestOptimizerOrchestrator:
    """Test main orchestrator"""
    
    def test_full_optimization(self, sample_profile):
        """Test complete optimization workflow"""
        orchestrator = OptimizerOrchestrator(use_llm=False)  # Disable LLM for tests
        
        report = orchestrator.optimize(
            profile=sample_profile,
            num_recommendations=10,
            include_high_risk=True
        )
        
        assert report.project == sample_profile.project_name
        assert report.budget == sample_profile.monthly_budget_inr
        assert report.estimated_cost > 0
        assert len(report.recommendations) > 0
        assert len(report.top_3_quick_wins) <= 3
    
    def test_deduplication(self, sample_profile):
        """Test recommendation deduplication"""
        orchestrator = OptimizerOrchestrator(use_llm=False)
        report = orchestrator.optimize(sample_profile, num_recommendations=15)
        
        # Check for unique titles
        titles = [r.title for r in report.recommendations]
        assert len(titles) == len(set(titles))  # All unique
    
    def test_summary_generation(self, sample_profile):
        """Test summary generation"""
        orchestrator = OptimizerOrchestrator(use_llm=False)
        report = orchestrator.optimize(sample_profile)
        
        summary = orchestrator.get_summary(report)
        
        assert sample_profile.project_name in summary
        assert "Budget" in summary
        assert "Savings" in summary


# Integration Tests
class TestIntegration:
    """Integration tests"""
    
    def test_end_to_end_within_budget(self):
        """Test end-to-end with project within budget"""
        profile = ProjectProfile(
            project_name="Small App",
            monthly_budget_inr=100000,  # High budget
            expected_users=10000,
            traffic_pattern=TrafficPattern.STEADY,
            region="ap-south-1",
            tech_stack=TechStack(
                backend="Node.js",
                frontend="Vue",
                database="PostgreSQL"
            ),
            features=["basic CRUD"],
            current_infra=CurrentInfrastructure(
                ec2_instances=1,
                instance_type="t3.small",
                rds="db.t3.small",
                load_balancer=False,
                cdn=False
            )
        )
        
        orchestrator = OptimizerOrchestrator(use_llm=False)
        report = orchestrator.optimize(profile)
        
        assert report.status == "Within Budget"
        assert report.estimated_cost < report.budget
    
    def test_end_to_end_over_budget(self):
        """Test end-to-end with project over budget"""
        profile = ProjectProfile(
            project_name="Large App",
            monthly_budget_inr=30000,  # Low budget
            expected_users=500000,
            traffic_pattern=TrafficPattern.BURSTY,
            region="ap-south-1",
            tech_stack=TechStack(
                backend="Java",
                frontend="React",
                database="PostgreSQL",
                cache="Redis"
            ),
            features=["real-time", "analytics", "ML"],
            current_infra=CurrentInfrastructure(
                ec2_instances=5,
                instance_type="t3.xlarge",
                rds="db.t3.xlarge",
                load_balancer=True,
                cdn=True
            )
        )
        
        orchestrator = OptimizerOrchestrator(use_llm=False)
        report = orchestrator.optimize(profile)
        
        assert report.status == "Over Budget"
        assert report.estimated_cost > report.budget
        # Should have recommendations to reduce cost
        assert report.total_potential_savings > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])