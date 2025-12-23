"""
LLM Recommendation Engine
Uses Hugging Face models for intelligent recommendations
"""
import re
import json
from typing import List, Dict, Optional
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch
from models import (
    ProjectProfile, UsagePattern, CostEstimate,
    Recommendation, RiskLevel, ComplexityLevel
)
from config import LLM_CONFIG, SYSTEM_PROMPT, OPTIMIZATION_PROMPT_TEMPLATE
import logging

logger = logging.getLogger(__name__)


class LLMRecommendationEngine:
    """Generates recommendations using LLM"""
    
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or LLM_CONFIG["model_name"]
        self.model = None
        self.tokenizer = None
        self.pipeline = None
        self.is_loaded = False
    
    def load_model(self):
        """Load the LLM model (lazy loading)"""
        if self.is_loaded:
            return
        
        try:
            logger.info(f"Loading model: {self.model_name}")
            
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None,
                trust_remote_code=True
            )
            
            self.pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                max_new_tokens=LLM_CONFIG["max_length"],
                temperature=LLM_CONFIG["temperature"],
                top_p=LLM_CONFIG["top_p"],
                do_sample=True
            )
            
            self.is_loaded = True
            logger.info("Model loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            logger.warning("Falling back to rule-based recommendations only")
            self.is_loaded = False
    
    def generate_recommendations(
        self,
        profile: ProjectProfile,
        cost_estimate: CostEstimate,
        usage_pattern: UsagePattern,
        num_recommendations: int = 10,
        baseline_recommendations: List[Recommendation] = None
    ) -> List[Recommendation]:
        """
        Generate LLM-powered recommendations
        """
        if not self.is_loaded:
            self.load_model()
        
        if not self.is_loaded:
            logger.warning("LLM not available, returning empty list")
            return []
        
        # Build prompt
        prompt = self._build_prompt(
            profile, cost_estimate, usage_pattern,
            num_recommendations, baseline_recommendations
        )
        
        # Generate response
        try:
            response = self._generate_llm_response(prompt)
            recommendations = self._parse_recommendations(response, baseline_recommendations)
            logger.info(f"Generated {len(recommendations)} LLM recommendations")
            return recommendations
        
        except Exception as e:
            logger.error(f"Error generating LLM recommendations: {e}")
            return []
    
    def _build_prompt(
        self,
        profile: ProjectProfile,
        cost_estimate: CostEstimate,
        usage_pattern: UsagePattern,
        num_recommendations: int,
        baseline_recommendations: Optional[List[Recommendation]]
    ) -> str:
        """Build the prompt for the LLM"""
        
        # Format tech stack
        tech_stack_str = f"""
Backend: {profile.tech_stack.backend}
Frontend: {profile.tech_stack.frontend}
Database: {profile.tech_stack.database}
Cache: {profile.tech_stack.cache or 'None'}
Storage: {profile.tech_stack.storage or 'Object Storage'}
Auth: {profile.tech_stack.auth or 'Standard'}
Features: {', '.join(profile.features)}
"""
        
        # Format current costs
        costs = cost_estimate.service_costs
        current_costs_str = f"""
EC2: ₹{costs.EC2:,.2f}
RDS: ₹{costs.RDS:,.2f}
Storage: ₹{costs.Storage:,.2f}
Load Balancer: ₹{costs.LoadBalancer:,.2f}
CDN: ₹{costs.CDN:,.2f}
Monitoring: ₹{costs.Monitoring:,.2f}
Data Transfer: ₹{costs.DataTransfer:,.2f}
"""
        
        # Budget status
        if cost_estimate.total_monthly_cost <= profile.monthly_budget_inr:
            budget_status = f"Within budget (₹{cost_estimate.remaining_budget:,.2f} remaining)"
        else:
            budget_status = f"Over budget by ₹{abs(cost_estimate.remaining_budget):,.2f}"
        
        # Usage patterns
        usage_patterns_str = f"""
Traffic Type: {usage_pattern.traffic_type}
Database Load: {usage_pattern.db_load}
Storage Access: {usage_pattern.storage_access}
Scaling Need: {usage_pattern.scaling_need}
CPU Pattern: {usage_pattern.cpu_pattern}
Memory Pattern: {usage_pattern.memory_pattern}
"""
        
        # Build full prompt
        prompt = OPTIMIZATION_PROMPT_TEMPLATE.format(
            project_name=profile.project_name,
            monthly_budget=profile.monthly_budget_inr,
            expected_users=profile.expected_users,
            traffic_pattern=profile.traffic_pattern,
            region=profile.region,
            tech_stack=tech_stack_str,
            current_costs=current_costs_str,
            total_cost=cost_estimate.total_monthly_cost,
            budget_status=budget_status,
            usage_patterns=usage_patterns_str,
            num_recommendations=num_recommendations
        )
        
        # Add baseline recommendations to avoid duplication
        if baseline_recommendations:
            baseline_titles = [rec.title for rec in baseline_recommendations[:5]]
            prompt += f"\n\nNote: Avoid duplicating these existing recommendations:\n"
            prompt += "\n".join(f"- {title}" for title in baseline_titles)
        
        return prompt
    
    def _generate_llm_response(self, prompt: str) -> str:
        """Generate response from LLM"""
        
        # Format for instruction-following models
        if "mistral" in self.model_name.lower():
            formatted_prompt = f"<s>[INST] {prompt} [/INST]"
        elif "llama" in self.model_name.lower():
            formatted_prompt = f"[INST] {prompt} [/INST]"
        else:
            formatted_prompt = prompt
        
        # Generate
        outputs = self.pipeline(
            formatted_prompt,
            max_new_tokens=LLM_CONFIG["max_length"],
            temperature=LLM_CONFIG["temperature"],
            top_p=LLM_CONFIG["top_p"],
            do_sample=True,
            pad_token_id=self.tokenizer.eos_token_id
        )
        
        response = outputs[0]["generated_text"]
        
        # Extract only the generated part (remove prompt)
        if formatted_prompt in response:
            response = response.replace(formatted_prompt, "").strip()
        
        return response
    
    def _parse_recommendations(
        self,
        llm_response: str,
        baseline_recommendations: Optional[List[Recommendation]]
    ) -> List[Recommendation]:
        """
        Parse LLM response into Recommendation objects
        """
        recommendations = []
        
        # Try to extract structured recommendations
        # The LLM might format recommendations in various ways
        
        # Pattern 1: Numbered list format
        pattern = r'(?:^|\n)(\d+)\.\s*\*\*([^*]+)\*\*\s*\n?(.*?)(?=\n\d+\.\s*\*\*|\Z)'
        matches = re.finditer(pattern, llm_response, re.DOTALL | re.MULTILINE)
        
        start_id = len(baseline_recommendations) + 1 if baseline_recommendations else 1
        
        for idx, match in enumerate(matches, start=start_id):
            try:
                title = match.group(2).strip()
                content = match.group(3).strip()
                
                # Extract details from content
                service = self._extract_service(title, content)
                savings = self._extract_savings(content)
                risk = self._extract_risk(content)
                complexity = self._extract_complexity(content)
                impact = self._extract_impact(content)
                steps = self._extract_steps(content)
                
                rec = Recommendation(
                    id=idx,
                    title=title,
                    service=service,
                    description=content[:200],  # First 200 chars as description
                    expected_savings_inr=savings,
                    risk=risk,
                    complexity=complexity,
                    impact=impact,
                    implementation_steps=steps
                )
                
                recommendations.append(rec)
                
            except Exception as e:
                logger.warning(f"Error parsing recommendation: {e}")
                continue
        
        # If pattern matching fails, try simpler extraction
        if not recommendations:
            recommendations = self._simple_parse(llm_response, start_id)
        
        return recommendations
    
    def _extract_service(self, title: str, content: str) -> str:
        """Extract service name"""
        services = ["EC2", "RDS", "Storage", "Network", "Monitoring", "Lambda", "CDN"]
        
        # Check title and content
        text = (title + " " + content).lower()
        
        for service in services:
            if service.lower() in text:
                return service
        
        # Default to EC2 for compute-related
        if any(word in text for word in ["instance", "compute", "cpu", "memory"]):
            return "EC2"
        elif any(word in text for word in ["database", "db", "sql"]):
            return "RDS"
        elif any(word in text for word in ["storage", "s3", "bucket"]):
            return "Storage"
        else:
            return "General"
    
    def _extract_savings(self, content: str) -> float:
        """Extract savings amount"""
        # Look for patterns like "₹5,000" or "5000 INR" or "save 5000"
        patterns = [
            r'₹\s*([\d,]+)',
            r'([\d,]+)\s*INR',
            r'sav(?:e|ings?).*?([\d,]+)',
            r'([\d,]+).*?(?:rupees?|INR)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    return float(amount_str)
                except:
                    continue
        
        # Default estimate based on service mentions
        if "downsize" in content.lower() or "reduce" in content.lower():
            return 3000
        elif "optimize" in content.lower():
            return 2000
        else:
            return 1500
    
    def _extract_risk(self, content: str) -> RiskLevel:
        """Extract risk level"""
        content_lower = content.lower()
        
        if "high risk" in content_lower or "risky" in content_lower:
            return RiskLevel.HIGH
        elif "medium risk" in content_lower or "moderate risk" in content_lower:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _extract_complexity(self, content: str) -> ComplexityLevel:
        """Extract complexity level"""
        content_lower = content.lower()
        
        if "complex" in content_lower or "difficult" in content_lower:
            return ComplexityLevel.HIGH
        elif "moderate" in content_lower:
            return ComplexityLevel.MEDIUM
        else:
            return ComplexityLevel.LOW
    
    def _extract_impact(self, content: str) -> str:
        """Extract impact description"""
        # Look for sentences containing "impact" or "performance"
        sentences = content.split('.')
        
        for sentence in sentences:
            if any(word in sentence.lower() for word in ["impact", "performance", "benefit", "improve"]):
                return sentence.strip()
        
        # Return first sentence if no impact found
        return sentences[0].strip() if sentences else "Optimizes cost efficiency"
    
    def _extract_steps(self, content: str) -> List[str]:
        """Extract implementation steps"""
        steps = []
        
        # Look for numbered or bulleted lists
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            # Match patterns like "1.", "•", "-", "*"
            if re.match(r'^[\d\-•*]+[\.\)]\s+', line):
                step = re.sub(r'^[\d\-•*]+[\.\)]\s+', '', line)
                if step and len(step) > 10:  # Meaningful step
                    steps.append(step)
        
        # If no steps found, create generic ones
        if not steps:
            steps = [
                "Analyze current configuration and usage",
                "Plan implementation with team",
                "Test in staging environment",
                "Deploy to production with monitoring"
            ]
        
        return steps[:5]  # Max 5 steps
    
    def _simple_parse(self, response: str, start_id: int) -> List[Recommendation]:
        """Fallback simple parsing"""
        recommendations = []
        
        # Split by double newlines or numbered items
        sections = re.split(r'\n\n+|\n\d+\.\s+', response)
        
        for idx, section in enumerate(sections[1:], start=start_id):  # Skip first (intro)
            if len(section.strip()) < 50:
                continue
            
            # Create basic recommendation
            title = section.split('\n')[0].strip()
            title = re.sub(r'^\*\*|\*\*$', '', title)  # Remove markdown bold
            
            rec = Recommendation(
                id=idx,
                title=title[:100],
                service="General",
                description=section[:200],
                expected_savings_inr=2000,
                risk=RiskLevel.MEDIUM,
                complexity=ComplexityLevel.MEDIUM,
                impact="Improves cost efficiency",
                implementation_steps=["Review and implement recommendation"]
            )
            
            recommendations.append(rec)
            
            if len(recommendations) >= 10:
                break
        
        return recommendations