"""
Streamlit Web Interface for Cloud Cost Optimizer
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import json

from models import (
    ProjectProfile, TechStack, CurrentInfrastructure,
    TrafficPattern, OptimizationRequest
)
from optimizer_orchestrator import OptimizerOrchestrator

# Page config
st.set_page_config(
    page_title="AI Cloud Cost Optimizer",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .recommendation-card {
        border-left: 4px solid #1f77b4;
        padding: 1rem;
        margin: 1rem 0;
        background-color: #f8f9fa;
        border-radius: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'optimizer' not in st.session_state:
    st.session_state.optimizer = None
if 'report' not in st.session_state:
    st.session_state.report = None


def main():
    """Main application"""
    
    # Header
    st.markdown('<div class="main-header">💰 AI Cloud Cost Optimizer</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Sidebar - Input Form
    with st.sidebar:
        st.header("📋 Project Configuration")
        
        # Basic Info
        st.subheader("Basic Information")
        project_name = st.text_input("Project Name", value="Food Delivery App")
        monthly_budget = st.number_input("Monthly Budget (INR)", min_value=0, value=50000, step=5000)
        expected_users = st.number_input("Expected Users", min_value=0, value=100000, step=10000)
        
        traffic_pattern = st.selectbox(
            "Traffic Pattern",
            options=["steady", "peak_hours", "bursty", "seasonal"],
            index=1
        )
        
        region = st.selectbox(
            "Region",
            options=["ap-south-1", "us-east-1", "eu-west-1", "ap-southeast-1"],
            index=0
        )
        
        # Tech Stack
        st.subheader("Tech Stack")
        backend = st.text_input("Backend", value="Spring Boot")
        frontend = st.text_input("Frontend", value="React")
        database = st.text_input("Database", value="PostgreSQL")
        cache = st.text_input("Cache (optional)", value="Redis")
        storage = st.text_input("Storage", value="Object Storage")
        auth = st.text_input("Authentication", value="JWT")
        
        # Features
        st.subheader("Features")
        features_text = st.text_area(
            "Features (one per line)",
            value="real-time order tracking\nimage uploads\nnotifications\nanalytics"
        )
        features = [f.strip() for f in features_text.split("\n") if f.strip()]
        
        # Infrastructure
        st.subheader("Current Infrastructure")
        ec2_instances = st.number_input("Number of EC2 Instances", min_value=1, value=2, step=1)
        instance_type = st.selectbox(
            "EC2 Instance Type",
            options=["t3.nano", "t3.micro", "t3.small", "t3.medium", "t3.large", "t3.xlarge"],
            index=3
        )
        
        rds_type = st.selectbox(
            "RDS Instance Type",
            options=["None", "db.t3.micro", "db.t3.small", "db.t3.medium", "db.t3.large"],
            index=3
        )
        
        load_balancer = st.checkbox("Load Balancer", value=True)
        cdn = st.checkbox("CDN", value=False)
        storage_gb = st.number_input("Storage (GB)", min_value=0, value=500, step=100)
        monitoring = st.selectbox("Monitoring Level", options=["basic", "advanced"], index=0)
        
        # Optimization Settings
        st.subheader("Optimization Settings")
        num_recommendations = st.slider("Number of Recommendations", min_value=5, max_value=20, value=15)
        include_high_risk = st.checkbox("Include High-Risk Recommendations", value=True)
        use_llm = st.checkbox("Use LLM (requires model download)", value=False)
        
        # Optimize Button
        st.markdown("---")
        optimize_button = st.button("🚀 Optimize Costs", type="primary", use_container_width=True)
    
    # Main Content
    if optimize_button:
        with st.spinner("🔍 Analyzing your infrastructure and generating recommendations..."):
            try:
                # Create profile
                profile = ProjectProfile(
                    project_name=project_name,
                    monthly_budget_inr=monthly_budget,
                    expected_users=expected_users,
                    traffic_pattern=TrafficPattern(traffic_pattern),
                    region=region,
                    tech_stack=TechStack(
                        backend=backend,
                        frontend=frontend,
                        database=database,
                        cache=cache if cache else None,
                        storage=storage if storage else None,
                        auth=auth if auth else None
                    ),
                    features=features,
                    current_infra=CurrentInfrastructure(
                        ec2_instances=ec2_instances,
                        instance_type=instance_type,
                        rds=rds_type if rds_type != "None" else None,
                        load_balancer=load_balancer,
                        cdn=cdn,
                        storage_gb=storage_gb,
                        monitoring=monitoring
                    )
                )
                
                # Initialize optimizer
                if st.session_state.optimizer is None:
                    st.session_state.optimizer = OptimizerOrchestrator(use_llm=use_llm)
                
                # Run optimization
                report = st.session_state.optimizer.optimize(
                    profile=profile,
                    num_recommendations=num_recommendations,
                    include_high_risk=include_high_risk
                )
                
                st.session_state.report = report
                st.success("✅ Optimization complete!")
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.exception(e)
    
    # Display Results
    if st.session_state.report:
        display_report(st.session_state.report)


def display_report(report):
    """Display optimization report"""
    
    # Overview Section
    st.header("📊 Cost Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Monthly Budget",
            f"₹{report.budget:,.0f}"
        )
    
    with col2:
        st.metric(
            "Estimated Cost",
            f"₹{report.estimated_cost:,.0f}",
            delta=f"{report.estimated_cost - report.budget:,.0f}"
        )
    
    with col3:
        st.metric(
            "Potential Savings",
            f"₹{report.total_potential_savings:,.0f}"
        )
    
    with col4:
        status_emoji = "✅" if report.status == "Within Budget" else "⚠️"
        st.metric(
            "Status",
            f"{status_emoji} {report.status}"
        )
    
    # Cost Breakdown Chart
    st.subheader("💰 Cost Breakdown")
    
    costs = report.cost_breakdown
    cost_data = {
        "Service": [],
        "Cost": []
    }
    
    for service, cost in costs.dict().items():
        if cost > 0:
            cost_data["Service"].append(service)
            cost_data["Cost"].append(cost)
    
    if cost_data["Service"]:
        fig = px.pie(
            values=cost_data["Cost"],
            names=cost_data["Service"],
            title="Cost Distribution by Service"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Usage Patterns
    st.subheader("📈 Usage Patterns")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"**Traffic Type:** {report.usage_patterns.traffic_type}")
        st.info(f"**Database Load:** {report.usage_patterns.db_load}")
        st.info(f"**Storage Access:** {report.usage_patterns.storage_access}")
    
    with col2:
        st.info(f"**Scaling Need:** {report.usage_patterns.scaling_need}")
        st.info(f"**CPU Pattern:** {report.usage_patterns.cpu_pattern}")
        st.info(f"**Memory Pattern:** {report.usage_patterns.memory_pattern}")
    
    # Quick Wins
    st.header("🚀 Top Quick Wins")
    
    for i, rec in enumerate(report.top_3_quick_wins, 1):
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"### {i}. {rec.title}")
                st.markdown(f"**Service:** {rec.service}")
                st.markdown(f"**Impact:** {rec.impact}")
            
            with col2:
                st.metric("Savings", f"₹{rec.expected_savings_inr:,.0f}/mo")
                st.markdown(f"**Risk:** {rec.risk.value}")
                st.markdown(f"**Complexity:** {rec.complexity.value}")
    
    st.markdown("---")
    
    # All Recommendations
    st.header("📋 All Recommendations")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filter_service = st.multiselect(
            "Filter by Service",
            options=list(set(rec.service for rec in report.recommendations)),
            default=None
        )
    
    with col2:
        filter_risk = st.multiselect(
            "Filter by Risk",
            options=["Low", "Medium", "High"],
            default=None
        )
    
    with col3:
        sort_by = st.selectbox(
            "Sort by",
            options=["Score", "Savings", "Risk", "Complexity"],
            index=0
        )
    
    # Apply filters
    filtered_recs = report.recommendations
    
    if filter_service:
        filtered_recs = [r for r in filtered_recs if r.service in filter_service]
    
    if filter_risk:
        filtered_recs = [r for r in filtered_recs if r.risk.value in filter_risk]
    
    # Apply sorting
    if sort_by == "Score":
        filtered_recs = sorted(filtered_recs, key=lambda x: x.score, reverse=True)
    elif sort_by == "Savings":
        filtered_recs = sorted(filtered_recs, key=lambda x: x.expected_savings_inr, reverse=True)
    elif sort_by == "Risk":
        risk_order = {"Low": 1, "Medium": 2, "High": 3}
        filtered_recs = sorted(filtered_recs, key=lambda x: risk_order[x.risk.value])
    elif sort_by == "Complexity":
        complexity_order = {"Low": 1, "Medium": 2, "High": 3}
        filtered_recs = sorted(filtered_recs, key=lambda x: complexity_order[x.complexity.value])
    
    # Display recommendations
    for rec in filtered_recs:
        with st.expander(f"#{rec.id} - {rec.title} (₹{rec.expected_savings_inr:,.0f}/mo)"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**Service:** {rec.service}")
                st.markdown(f"**Description:** {rec.description}")
                st.markdown(f"**Impact:** {rec.impact}")
                
                st.markdown("**Implementation Steps:**")
                for i, step in enumerate(rec.implementation_steps, 1):
                    st.markdown(f"{i}. {step}")
            
            with col2:
                st.metric("Monthly Savings", f"₹{rec.expected_savings_inr:,.0f}")
                st.metric("Score", f"{rec.score:.2f}")
                
                # Risk badge
                risk_color = {"Low": "green", "Medium": "orange", "High": "red"}
                st.markdown(f"**Risk:** :{risk_color[rec.risk.value]}[{rec.risk.value}]")
                
                # Complexity badge
                complexity_color = {"Low": "green", "Medium": "orange", "High": "red"}
                st.markdown(f"**Complexity:** :{complexity_color[rec.complexity.value]}[{rec.complexity.value}]")
    
    # Export Section
    st.markdown("---")
    st.header("📥 Export Report")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # JSON export
        json_data = report.json(indent=2)
        st.download_button(
            label="Download JSON Report",
            data=json_data,
            file_name=f"cost_optimization_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    with col2:
        # Summary export
        summary = generate_text_summary(report)
        st.download_button(
            label="Download Text Summary",
            data=summary,
            file_name=f"cost_optimization_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )


def generate_text_summary(report) -> str:
    """Generate text summary of report"""
    lines = []
    lines.append("=" * 80)
    lines.append(f"Cloud Cost Optimization Report: {report.project}")
    lines.append("=" * 80)
    lines.append(f"Generated: {report.generated_at}")
    lines.append("")
    
    lines.append("BUDGET OVERVIEW")
    lines.append(f"Monthly Budget: ₹{report.budget:,.2f}")
    lines.append(f"Estimated Cost: ₹{report.estimated_cost:,.2f}")
    lines.append(f"Status: {report.status}")
    lines.append(f"Total Potential Savings: ₹{report.total_potential_savings:,.2f}")
    lines.append("")
    
    lines.append("TOP 3 QUICK WINS")
    for i, rec in enumerate(report.top_3_quick_wins, 1):
        lines.append(f"{i}. {rec.title}")
        lines.append(f"   Savings: ₹{rec.expected_savings_inr:,.2f}/month")
        lines.append(f"   Risk: {rec.risk.value} | Complexity: {rec.complexity.value}")
        lines.append("")
    
    lines.append("=" * 80)
    return "\n".join(lines)


if __name__ == "__main__":
    main()