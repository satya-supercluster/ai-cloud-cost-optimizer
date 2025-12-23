"""
Pydantic models for request/response validation
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class TrafficPattern(str, Enum):
    STEADY = "steady"
    PEAK_HOURS = "peak_hours"
    BURSTY = "bursty"
    SEASONAL = "seasonal"


class RiskLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class ComplexityLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class TechStack(BaseModel):
    backend: str = Field(..., description="Backend technology")
    frontend: str = Field(..., description="Frontend technology")
    database: str = Field(..., description="Database type")
    cache: Optional[str] = Field(None, description="Caching layer")
    storage: Optional[str] = Field(None, description="Storage solution")
    auth: Optional[str] = Field(None, description="Authentication method")


class CurrentInfrastructure(BaseModel):
    ec2_instances: int = Field(..., ge=0, description="Number of EC2 instances")
    instance_type: str = Field(..., description="EC2 instance type")
    rds: Optional[str] = Field(None, description="RDS instance type")
    load_balancer: bool = Field(False, description="Load balancer enabled")
    cdn: bool = Field(False, description="CDN enabled")
    storage_gb: Optional[int] = Field(100, ge=0, description="Storage in GB")
    monitoring: str = Field("basic", description="Monitoring level")


class ProjectProfile(BaseModel):
    project_name: str = Field(..., description="Name of the project")
    monthly_budget_inr: int = Field(..., ge=0, description="Monthly budget in INR")
    expected_users: int = Field(..., ge=0, description="Expected number of users")
    traffic_pattern: TrafficPattern = Field(..., description="Traffic pattern")
    region: str = Field("ap-south-1", description="Cloud region")
    tech_stack: TechStack
    features: List[str] = Field(default_factory=list, description="Key features")
    current_infra: CurrentInfrastructure

    @validator('region')
    def validate_region(cls, v):
        valid_regions = ["ap-south-1", "us-east-1", "eu-west-1", "ap-southeast-1"]
        if v not in valid_regions:
            raise ValueError(f"Region must be one of {valid_regions}")
        return v


class ServiceCost(BaseModel):
    EC2: float = 0
    RDS: float = 0
    Storage: float = 0
    LoadBalancer: float = 0
    CDN: float = 0
    Monitoring: float = 0
    DataTransfer: float = 0
    Other: float = 0


class CostEstimate(BaseModel):
    service_costs: ServiceCost
    total_monthly_cost: float
    budget: float
    remaining_budget: float
    budget_utilization_percent: float


class UsagePattern(BaseModel):
    traffic_type: str
    db_load: str
    storage_access: str
    scaling_need: str
    cpu_pattern: str
    memory_pattern: str
    peak_hours: Optional[List[int]] = None


class Recommendation(BaseModel):
    id: int
    title: str
    service: str
    description: str
    expected_savings_inr: float
    risk: RiskLevel
    complexity: ComplexityLevel
    impact: str
    implementation_steps: List[str]
    score: float = 0.0

    class Config:
        use_enum_values = True


class OptimizationReport(BaseModel):
    project: str
    budget: float
    estimated_cost: float
    status: str
    cost_breakdown: ServiceCost
    usage_patterns: UsagePattern
    recommendations: List[Recommendation]
    total_potential_savings: float
    top_3_quick_wins: List[Recommendation]
    generated_at: str


class OptimizationRequest(BaseModel):
    profile: ProjectProfile
    num_recommendations: int = Field(15, ge=5, le=20)
    include_high_risk: bool = Field(True, description="Include high-risk recommendations")


class OptimizationResponse(BaseModel):
    success: bool
    report: Optional[OptimizationReport] = None
    error: Optional[str] = None