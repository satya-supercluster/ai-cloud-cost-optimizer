# AI-Driven Cloud Cost Optimizer

A comprehensive, production-ready system that uses LLM intelligence to analyze cloud infrastructure and generate actionable cost optimization recommendations.

## What This Solves

Most developers and startups know their budget, tech stack, and user load, but struggle to identify:

- Where money is actually wasted
- Which services can be downsized
- What alternative architectures exist
- Which optimizations suit their specific workload

**This project provides:**

- Detailed cost analysis
- 12-20 intelligent, context-aware recommendations
- Risk assessment for each recommendation
- Implementation roadmaps

## Architecture

```
User Input (Project Profile)
       ↓
Cost Estimation Engine
       ↓
Usage Pattern Analyzer
       ↓
Rule-Based Optimizer
       ↓
LLM Recommendation Engine (Hugging Face)
       ↓
Recommendation Ranker
       ↓
JSON + Report Output
```

## Features

### Core Capabilities

- **Multi-layer Optimization**: Combines rule-based logic with LLM intelligence
- **Budget-Aware**: All recommendations consider your specific budget constraints
- **Risk Assessment**: Each recommendation includes risk level and complexity
- **Workload Matching**: Recommendations tailored to your traffic patterns and usage
- **Quick Wins Identification**: Highlights low-risk, high-impact optimizations

### Recommendation Categories

- **Compute**: Instance sizing, autoscaling, ARM migration, spot instances
- **Database**: Read replicas, connection pooling, storage optimization
- **Storage**: Lifecycle policies, intelligent tiering, compression
- **Network**: CDN enablement, VPC endpoints, data transfer optimization
- **Monitoring**: Log retention, metric sampling, cost-effective observability

## Quick Start

### Prerequisites

```bash
Python 3.10+
8GB+ RAM (for LLM models)
```

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/satya-supercluster/ai-cloud-cost-optimizer.git
cd ai-cloud-cost-optimizer
```

1. **Create virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

1. **Install dependencies**

```bash
pip install -r requirements.txt
```

### Running the Application

#### Option 1: FastAPI Backend (API Mode)

```bash
python main.py
```

The API will be available at `http://localhost:8000`

API Documentation: `http://localhost:8000/docs`

#### Option 2: Streamlit UI (Interactive Mode)

```bash
streamlit run streamlit_app.py
```

The web interface will open at `http://localhost:8501`

## Usage Examples

### Using the API

**1. Get an example profile:**

```bash
curl http://localhost:8000/example
```

**2. Optimize costs:**

```bash
curl -X POST http://localhost:8000/optimize \
  -H "Content-Type: application/json" \
  -d @example_profile.json
```

**3. Quick cost estimate:**

```bash
curl -X POST http://localhost:8000/quick-analysis \
  -H "Content-Type: application/json" \
  -d '{
    "monthly_budget": 50000,
    "expected_users": 100000,
    "has_database": true,
    "has_cdn": false,
    "num_instances": 2
  }'
```

### Using Python Directly

```python
from models import ProjectProfile, TechStack, CurrentInfrastructure, TrafficPattern
from optimizer_orchestrator import OptimizerOrchestrator

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
        cache="Redis"
    ),
    features=[
        "real-time order tracking",
        "image uploads",
        "notifications"
    ],
    current_infra=CurrentInfrastructure(
        ec2_instances=2,
        instance_type="t3.medium",
        rds="db.t3.medium",
        load_balancer=True,
        cdn=False
    )
)

# Run optimization
optimizer = OptimizerOrchestrator(use_llm=True)
report = optimizer.optimize(profile, num_recommendations=15)

# Print summary
print(optimizer.get_summary(report))

# Access recommendations
for rec in report.recommendations[:5]:
    print(f"\n{rec.title}")
    print(f"Savings: ₹{rec.expected_savings_inr:,.2f}/month")
    print(f"Risk: {rec.risk.value} | Complexity: {rec.complexity.value}")
```

## Configuration

### LLM Models

Edit `config.py` to change the LLM model:

```python
LLM_CONFIG = {
    "model_name": "mistralai/Mistral-7B-Instruct-v0.1",  # Default
    "alternative_models": [
        "meta-llama/Llama-2-7b-chat-hf",
        "tiiuae/falcon-7b-instruct"
    ],
    "max_length": 2048,
    "temperature": 0.7,
}
```

**Note:** First run will download the model (~14GB). Subsequent runs will use cached model.

### Pricing Configuration

Update pricing in `config.py` for your region:

```python
PRICING = {
    "EC2": {
        "t3.medium": 28000,  # INR per month
        # ... more instance types
    },
    "RDS": {
        "db.t3.medium": 40000,
        # ... more instance types
    },
    # ... other services
}
```

### Optimization Rules

Customize thresholds in `config.py`:

```python
OPTIMIZATION_RULES = {
    "cpu_threshold_low": 30,   # CPU < 30% suggests downsizing
    "cpu_threshold_high": 80,  # CPU > 80% suggests upsizing
    "read_heavy_ratio": 0.7,   # 70% reads → read replicas
}
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest test_optimizer.py -v

# Run specific test class
pytest test_optimizer.py::TestCostEstimationEngine -v

# Run with coverage
pytest test_optimizer.py --cov=. --cov-report=html
```

## Output Format

### Optimization Report Structure

```json
{
  "project": "Food Delivery App",
  "budget": 50000,
  "estimated_cost": 45000,
  "status": "Within Budget",
  "cost_breakdown": {
    "EC2": 18000,
    "RDS": 15000,
    "Storage": 7000,
    "LoadBalancer": 3000,
    "Monitoring": 2000
  },
  "total_potential_savings": 12500,
  "recommendations": [
    {
      "id": 1,
      "title": "Switch EC2 to Auto Scaling Group",
      "service": "EC2",
      "expected_savings_inr": 4500,
      "risk": "Low",
      "complexity": "Medium",
      "impact": "Improves scalability during peak hours",
      "implementation_steps": [
        "Create Auto Scaling Group with min 1, max 4 instances",
        "Set up target tracking scaling policy (CPU 70%)",
        "Configure scale-in protection for critical instances"
      ],
      "score": 75.2
    }
    // ... more recommendations
  ]
}
```

## How It Works

### 1. Cost Estimation Engine

- Calculates monthly costs for all services
- Applies regional pricing multipliers
- Accounts for traffic patterns and user load

### 2. Usage Pattern Analyzer

- Identifies traffic patterns (steady, bursty, peak hours)
- Determines database load characteristics
- Analyzes storage access patterns
- Detects CPU and memory requirements

### 3. Rule-Based Optimizer

- Applies deterministic optimization rules
- Generates baseline recommendations
- Examples:
  - Traffic bursty → autoscaling
  - DB read-heavy → read replicas
  - Storage cold → lifecycle policies

### 4. LLM Recommendation Engine

- Uses Hugging Face transformers
- Generates context-aware recommendations
- Considers:
  - Budget constraints
  - Technical stack compatibility
  - Business requirements
  - Implementation complexity

### 5. Recommendation Ranker

- Scores each recommendation
- Formula: `score = (savings × 0.5) - (risk × 0.3) - (complexity × 0.2) + workload_match`
- Provides quick wins and high-impact lists

## Project Structure

```
ai-cloud-cost-optimizer/
├── config.py                      # Configuration and constants
├── models.py                      # Pydantic data models
├── cost_estimation_engine.py     # Cost calculation logic
├── usage_pattern_analyzer.py     # Usage pattern detection
├── rule_based_optimizer.py       # Deterministic recommendations
├── llm_recommendation_engine.py  # LLM integration
├── recommendation_ranker.py      # Scoring and ranking
├── optimizer_orchestrator.py     # Main workflow coordinator
├── main.py                        # FastAPI application
├── streamlit_app.py              # Web UI
├── test_optimizer.py             # Unit tests
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## Advanced Usage

### Custom Pricing Integration

Integrate with AWS Cost Explorer API:

```python
from cost_estimation_engine import CostEstimationEngine

class AWSCostEstimationEngine(CostEstimationEngine):
    def __init__(self, aws_session):
        super().__init__()
        self.ce_client = aws_session.client('ce')
    
    def get_actual_costs(self, start_date, end_date):
        # Fetch actual costs from AWS
        pass
```

### Multi-Cloud Support

Extend for GCP/Azure:

```python
# Add to config.py
CLOUD_PROVIDERS = {
    "AWS": {...},
    "GCP": {...},
    "Azure": {...}
}
```

### Webhook Notifications

Add Slack/Teams notifications:

```python
from optimizer_orchestrator import OptimizerOrchestrator

class NotifyingOrchestrator(OptimizerOrchestrator):
    def optimize(self, profile, **kwargs):
        report = super().optimize(profile, **kwargs)
        self.send_slack_notification(report)
        return report
```

## Performance

- **Without LLM**: ~2-5 seconds
- **With LLM (first run)**: ~2-3 minutes (model download)
- **With LLM (cached)**: ~10-30 seconds
- **Memory usage**: ~2GB (without LLM), ~8GB (with LLM)

## Security Considerations

1. **API Keys**: Never commit AWS/GCP credentials
2. **Input Validation**: All inputs validated via Pydantic
3. **Rate Limiting**: Implement rate limiting in production
4. **Authentication**: Add auth middleware for production deployments

## Troubleshooting

### Model Download Issues

```bash
# Set HuggingFace cache directory
export HF_HOME=/path/to/cache
export TRANSFORMERS_CACHE=/path/to/cache
```

### Out of Memory

```bash
# Use smaller model or disable LLM
optimizer = OptimizerOrchestrator(use_llm=False)
```

### Import Errors

```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Hugging Face for transformer models
- FastAPI for the excellent web framework
- Streamlit for rapid UI development

## Roadmap

- [ ] Real-time AWS billing integration
- [ ] Multi-cloud support (GCP, Azure)
- [ ] What-if budget simulation
- [ ] Terraform export for recommendations
- [ ] Chat-based optimization assistant
- [ ] Historical cost tracking
- [ ] Anomaly detection
- [ ] Team collaboration features

---
