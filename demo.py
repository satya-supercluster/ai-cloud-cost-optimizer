"""
Demo Script for Cloud Cost Optimizer
Run this to see the system in action
"""
from models import (
    ProjectProfile, TechStack, CurrentInfrastructure, TrafficPattern
)
from optimizer_orchestrator import OptimizerOrchestrator
import json


def demo_food_delivery_app():
    """Demo: Food Delivery Application"""
    print("=" * 80)
    print("DEMO: Food Delivery App Cost Optimization")
    print("=" * 80)
    print()
    
    # Create project profile
    profile = ProjectProfile(
        project_name="Food Delivery App",
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
            "real-time order tracking",
            "image uploads",
            "notifications",
            "analytics"
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
    
    print("Project Configuration:")
    print(f"  Name: {profile.project_name}")
    print(f"  Budget: ₹{profile.monthly_budget_inr:,}/month")
    print(f"  Users: {profile.expected_users:,}")
    print(f"  Traffic: {profile.traffic_pattern.value}")
    print()
    
    # Run optimization (without LLM for faster demo)
    print("Running optimization (this may take a few seconds)...")
    print()
    
    optimizer = OptimizerOrchestrator(use_llm=False)
    report = optimizer.optimize(profile, num_recommendations=12)
    
    # Display results
    print(optimizer.get_summary(report))
    
    # Detailed recommendations
    print("\n📋 DETAILED RECOMMENDATIONS\n")
    
    for i, rec in enumerate(report.recommendations[:5], 1):
        print(f"{i}. {rec.title}")
        print(f"   Service: {rec.service}")
        print(f"   Monthly Savings: ₹{rec.expected_savings_inr:,.2f}")
        print(f"   Risk: {rec.risk.value} | Complexity: {rec.complexity.value}")
        print(f"   Score: {rec.score:.2f}")
        print(f"   Impact: {rec.impact}")
        print()
        print("   Implementation Steps:")
        for step in rec.implementation_steps:
            print(f"   • {step}")
        print()
    
    # Save report
    output_file = "demo_report.json"
    with open(output_file, "w") as f:
        f.write(report.json(indent=2))
    
    print(f"✅ Full report saved to: {output_file}")
    print()


def demo_ecommerce_app():
    """Demo: E-commerce Application"""
    print("=" * 80)
    print("DEMO: E-commerce Platform Cost Optimization")
    print("=" * 80)
    print()
    
    profile = ProjectProfile(
        project_name="E-commerce Platform",
        monthly_budget_inr=75000,
        expected_users=250000,
        traffic_pattern=TrafficPattern.SEASONAL,
        region="ap-south-1",
        tech_stack=TechStack(
            backend="Node.js",
            frontend="Next.js",
            database="MongoDB",
            cache="Redis",
            storage="S3",
            auth="OAuth2"
        ),
        features=[
            "product catalog",
            "shopping cart",
            "payment gateway",
            "user reviews",
            "recommendations"
        ],
        current_infra=CurrentInfrastructure(
            ec2_instances=4,
            instance_type="t3.large",
            rds="db.t3.large",
            load_balancer=True,
            cdn=True,
            storage_gb=2000,
            monitoring="advanced"
        )
    )
    
    print("Project Configuration:")
    print(f"  Name: {profile.project_name}")
    print(f"  Budget: ₹{profile.monthly_budget_inr:,}/month")
    print(f"  Users: {profile.expected_users:,}")
    print()
    
    print("Running optimization...")
    print()
    
    optimizer = OptimizerOrchestrator(use_llm=False)
    report = optimizer.optimize(profile, num_recommendations=15)
    
    print(optimizer.get_summary(report))
    
    # Show recommendations by service
    print("\n📊 RECOMMENDATIONS BY SERVICE\n")
    
    from recommendation_ranker import RecommendationRanker
    ranker = RecommendationRanker()
    grouped = ranker.group_by_service(report.recommendations)
    
    for service, recs in grouped.items():
        total_savings = sum(r.expected_savings_inr for r in recs)
        print(f"\n{service} ({len(recs)} recommendations, ₹{total_savings:,.2f} total savings):")
        for rec in recs[:3]:  # Top 3 per service
            print(f"  • {rec.title} (₹{rec.expected_savings_inr:,.2f})")
    
    print()


def demo_startup_mvp():
    """Demo: Startup MVP on tight budget"""
    print("=" * 80)
    print("DEMO: Startup MVP - Budget Optimization")
    print("=" * 80)
    print()
    
    profile = ProjectProfile(
        project_name="SaaS Startup MVP",
        monthly_budget_inr=25000,  # Tight budget
        expected_users=5000,
        traffic_pattern=TrafficPattern.STEADY,
        region="ap-south-1",
        tech_stack=TechStack(
            backend="Python Flask",
            frontend="React",
            database="PostgreSQL"
        ),
        features=[
            "user authentication",
            "basic CRUD",
            "email notifications"
        ],
        current_infra=CurrentInfrastructure(
            ec2_instances=2,
            instance_type="t3.medium",
            rds="db.t3.small",
            load_balancer=True,
            cdn=False,
            storage_gb=100,
            monitoring="basic"
        )
    )
    
    print("Startup Challenge:")
    print(f"  Budget: ₹{profile.monthly_budget_inr:,}/month (tight!)")
    print(f"  Current estimated cost: HIGH")
    print(f"  Goal: Stay within budget")
    print()
    
    print("Running optimization...")
    print()
    
    optimizer = OptimizerOrchestrator(use_llm=False)
    report = optimizer.optimize(profile, num_recommendations=10)
    
    print(optimizer.get_summary(report))
    
    # Show quick wins for startup
    print("\n🚀 QUICK WINS FOR STARTUP\n")
    print("Focus on these low-risk, low-complexity optimizations:\n")
    
    for i, rec in enumerate(report.top_3_quick_wins, 1):
        print(f"{i}. {rec.title}")
        print(f"   Savings: ₹{rec.expected_savings_inr:,.2f}/month")
        print(f"   Why: {rec.impact}")
        print()


def interactive_demo():
    """Interactive demo - let user choose"""
    print("\n" + "=" * 80)
    print("🎯 Cloud Cost Optimizer - Interactive Demo")
    print("=" * 80)
    print()
    print("Choose a demo scenario:")
    print("1. Food Delivery App (Peak Hours Traffic)")
    print("2. E-commerce Platform (Seasonal Traffic)")
    print("3. Startup MVP (Tight Budget)")
    print("4. Run All Demos")
    print("0. Exit")
    print()
    
    choice = input("Enter your choice (0-4): ").strip()
    
    if choice == "1":
        demo_food_delivery_app()
    elif choice == "2":
        demo_ecommerce_app()
    elif choice == "3":
        demo_startup_mvp()
    elif choice == "4":
        demo_food_delivery_app()
        print("\n" + "=" * 80 + "\n")
        demo_ecommerce_app()
        print("\n" + "=" * 80 + "\n")
        demo_startup_mvp()
    elif choice == "0":
        print("Goodbye!")
        return
    else:
        print("Invalid choice. Please try again.")
        interactive_demo()
    
    # Ask if user wants to try another
    print("\n" + "=" * 80)
    again = input("\nWould you like to try another demo? (y/n): ").strip().lower()
    if again == 'y':
        interactive_demo()
    else:
        print("\n✅ Demo complete! Check out main.py or streamlit_app.py for more.")


if __name__ == "__main__":
    try:
        interactive_demo()
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure all dependencies are installed:")
        print("  pip install -r requirements.txt")