"""
FastAPI Application for Cloud Cost Optimizer
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
from datetime import datetime

from models import (
    ProjectProfile, OptimizationRequest, OptimizationResponse,
    OptimizationReport
)
from optimizer_orchestrator import OptimizerOrchestrator
from config import API_CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=API_CONFIG["title"],
    version=API_CONFIG["version"],
    description=API_CONFIG["description"]
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize optimizer (lazy loading for LLM)
optimizer = None


def get_optimizer():
    """Get or create optimizer instance"""
    global optimizer
    if optimizer is None:
        optimizer = OptimizerOrchestrator(use_llm=True)
    return optimizer


# Health check
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "AI Cloud Cost Optimizer",
        "version": API_CONFIG["version"],
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/optimize", response_model=OptimizationResponse)
async def optimize_costs(request: OptimizationRequest):
    """
    Main optimization endpoint
    
    Accepts a project profile and returns optimization recommendations
    """
    try:
        logger.info(f"Received optimization request for: {request.profile.project_name}")
        
        # Get optimizer instance
        opt = get_optimizer()
        
        # Run optimization
        report = opt.optimize(
            profile=request.profile,
            num_recommendations=request.num_recommendations,
            include_high_risk=request.include_high_risk
        )
        
        # Generate summary for logging
        summary = opt.get_summary(report)
        logger.info(f"Optimization complete:\n{summary}")
        
        return OptimizationResponse(
            success=True,
            report=report
        )
    
    except Exception as e:
        logger.error(f"Optimization failed: {str(e)}", exc_info=True)
        return OptimizationResponse(
            success=False,
            error=str(e)
        )


@app.post("/estimate-costs")
async def estimate_costs(profile: ProjectProfile):
    """
    Quick cost estimation without full optimization
    """
    try:
        from cost_estimation_engine import CostEstimationEngine
        
        engine = CostEstimationEngine()
        estimate = engine.estimate_costs(profile)
        
        return {
            "success": True,
            "estimate": estimate.dict()
        }
    
    except Exception as e:
        logger.error(f"Cost estimation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze-patterns")
async def analyze_patterns(profile: ProjectProfile):
    """
    Analyze usage patterns without full optimization
    """
    try:
        from usage_pattern_analyzer import UsagePatternAnalyzer
        
        analyzer = UsagePatternAnalyzer()
        pattern = analyzer.analyze(profile)
        
        return {
            "success": True,
            "pattern": pattern.dict()
        }
    
    except Exception as e:
        logger.error(f"Pattern analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/recommendations/filter")
async def filter_recommendations(
    service: Optional[str] = None,
    max_risk: Optional[str] = None,
    max_complexity: Optional[str] = None,
    min_savings: Optional[float] = None
):
    """
    Get information about available filters
    """
    return {
        "available_filters": {
            "service": ["EC2", "RDS", "Storage", "Network", "Monitoring", "General"],
            "risk": ["Low", "Medium", "High"],
            "complexity": ["Low", "Medium", "High"]
        },
        "usage": "Use these values with the /optimize endpoint"
    }


class QuickAnalysisRequest(BaseModel):
    monthly_budget: float
    expected_users: int
    has_database: bool = True
    has_cdn: bool = False
    num_instances: int = 2


@app.post("/quick-analysis")
async def quick_analysis(request: QuickAnalysisRequest):
    """
    Quick cost analysis for simple scenarios
    """
    try:
        from cost_estimation_engine import CostEstimationEngine
        from config import PRICING
        
        # Simple calculation
        ec2_cost = PRICING["EC2"]["t3.medium"] * request.num_instances
        rds_cost = PRICING["RDS"]["db.t3.medium"] if request.has_database else 0
        storage_cost = 100 * PRICING["STORAGE"]["object_storage_gb"]
        cdn_cost = (request.expected_users * 50 / 1024) * PRICING["NETWORK"]["cdn_gb"] if request.has_cdn else 0
        monitoring_cost = PRICING["MONITORING"]["basic"]
        
        total_cost = ec2_cost + rds_cost + storage_cost + cdn_cost + monitoring_cost
        
        status = "Within Budget" if total_cost <= request.monthly_budget else "Over Budget"
        
        return {
            "success": True,
            "estimated_cost": total_cost,
            "budget": request.monthly_budget,
            "status": status,
            "breakdown": {
                "EC2": ec2_cost,
                "RDS": rds_cost,
                "Storage": storage_cost,
                "CDN": cdn_cost,
                "Monitoring": monitoring_cost
            },
            "note": "This is a simplified estimate. Use /optimize for detailed analysis."
        }
    
    except Exception as e:
        logger.error(f"Quick analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Example endpoint for testing
@app.get("/example")
async def get_example():
    """
    Returns an example project profile for testing
    """
    from models import TechStack, CurrentInfrastructure, TrafficPattern
    
    example = ProjectProfile(
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
    
    return {
        "example_profile": example.dict(),
        "usage": "POST this to /optimize endpoint"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=API_CONFIG["host"],
        port=API_CONFIG["port"],
        reload=True,
        log_level="info"
    )