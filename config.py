"""
Configuration for Cloud Cost Optimizer
"""
import os
from typing import Dict, Any
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)

# LLM Configuration
LLM_CONFIG = {
    "model_name": "mistralai/Mistral-7B-Instruct-v0.1",
    "alternative_models": [
        "meta-llama/Llama-2-7b-chat-hf",
        "tiiuae/falcon-7b-instruct"
    ],
    "max_length": 2048,
    "temperature": 0.7,
    "top_p": 0.9,
    "device": "cpu",  # Change to "cuda" if GPU available
}

# Cloud Service Pricing (INR per month)
# Simplified pricing - in production, use AWS/GCP/Azure APIs
PRICING = {
    "EC2": {
        "t3.nano": 3500,
        "t3.micro": 7000,
        "t3.small": 14000,
        "t3.medium": 28000,
        "t3.large": 56000,
        "t3.xlarge": 112000,
        "t3.2xlarge": 224000,
        # ARM instances (Graviton)
        "t4g.nano": 2800,
        "t4g.micro": 5600,
        "t4g.small": 11200,
        "t4g.medium": 22400,
        "t4g.large": 44800,
    },
    "RDS": {
        "db.t3.micro": 10000,
        "db.t3.small": 20000,
        "db.t3.medium": 40000,
        "db.t3.large": 80000,
        "db.t3.xlarge": 160000,
    },
    "STORAGE": {
        "object_storage_gb": 2,  # per GB
        "ebs_gp3_gb": 6,  # per GB
        "glacier_gb": 0.3,  # per GB
    },
    "NETWORK": {
        "load_balancer": 2000,
        "cdn_gb": 5,  # per GB transferred
        "data_transfer_gb": 7,  # per GB
    },
    "MONITORING": {
        "basic": 1000,
        "advanced": 3000,
        "custom_metrics": 50,  # per metric
    }
}

# Optimization Rules Configuration
OPTIMIZATION_RULES = {
    "cpu_threshold_low": 30,  # Below 30% CPU suggests downsizing
    "cpu_threshold_high": 80,  # Above 80% suggests upsizing
    "memory_threshold_low": 40,
    "memory_threshold_high": 85,
    "read_heavy_ratio": 0.7,  # 70% reads suggests read replicas
    "cold_storage_days": 90,  # Files not accessed in 90 days
}

# Recommendation Scoring Weights
SCORING_WEIGHTS = {
    "savings": 0.5,
    "risk": -0.3,
    "complexity": -0.2,
}

# Risk Levels
RISK_LEVELS = {
    "Low": 1,
    "Medium": 2,
    "High": 3,
}

# Complexity Levels
COMPLEXITY_LEVELS = {
    "Low": 1,
    "Medium": 2,
    "High": 3,
}

# Regions
REGIONS = {
    "ap-south-1": {"name": "Mumbai", "multiplier": 1.0},
    "us-east-1": {"name": "N. Virginia", "multiplier": 0.95},
    "eu-west-1": {"name": "Ireland", "multiplier": 1.05},
    "ap-southeast-1": {"name": "Singapore", "multiplier": 1.08},
}

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR}/cost_optimizer.db")

# API Configuration
API_CONFIG = {
    "title": "AI Cloud Cost Optimizer",
    "version": "1.0.0",
    "description": "LLM-driven cloud cost optimization system",
    "host": "0.0.0.0",
    "port": 8000,
}

# Prompt Templates
SYSTEM_PROMPT = """You are an expert cloud cost optimization consultant with deep knowledge of AWS, GCP, and Azure.
Your job is to analyze cloud infrastructure and provide actionable, money-saving recommendations.
You must be specific, practical, and consider real-world trade-offs."""

OPTIMIZATION_PROMPT_TEMPLATE = """You are a cloud cost optimization expert.

Project Details:
- Name: {project_name}
- Monthly Budget: ₹{monthly_budget:,}
- Expected Users: {expected_users:,}
- Traffic Pattern: {traffic_pattern}
- Region: {region}

Tech Stack:
{tech_stack}

Current Infrastructure Costs:
{current_costs}

Total Monthly Cost: ₹{total_cost:,}
Budget Status: {budget_status}

Usage Patterns Detected:
{usage_patterns}

Task: Generate exactly {num_recommendations} cost optimization recommendations.

For EACH recommendation, provide:
1. A clear, actionable title
2. The affected cloud service
3. Expected monthly savings in INR
4. Risk level (Low/Medium/High)
5. Performance impact description
6. Implementation complexity (Low/Medium/High)
7. Detailed implementation steps

Focus on:
- Recommendations with highest ROI
- Variety of services (compute, database, storage, network)
- Both quick wins and strategic changes
- Budget-aware suggestions

Format each recommendation clearly and professionally."""