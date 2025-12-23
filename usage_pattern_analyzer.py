"""
Usage Pattern Analyzer
Analyzes workload behavior and usage patterns
"""
from typing import Dict, List, Optional
from models import ProjectProfile, UsagePattern
import logging

logger = logging.getLogger(__name__)


class UsagePatternAnalyzer:
    """Analyzes usage patterns from project profile"""
    
    def analyze(self, profile: ProjectProfile) -> UsagePattern:
        """
        Analyze usage patterns from project configuration
        """
        traffic_type = self._analyze_traffic_type(profile)
        db_load = self._analyze_db_load(profile)
        storage_access = self._analyze_storage_access(profile)
        scaling_need = self._analyze_scaling_need(profile)
        cpu_pattern = self._analyze_cpu_pattern(profile)
        memory_pattern = self._analyze_memory_pattern(profile)
        peak_hours = self._identify_peak_hours(profile)
        
        pattern = UsagePattern(
            traffic_type=traffic_type,
            db_load=db_load,
            storage_access=storage_access,
            scaling_need=scaling_need,
            cpu_pattern=cpu_pattern,
            memory_pattern=memory_pattern,
            peak_hours=peak_hours
        )
        
        logger.info(f"Usage Pattern Analysis: {pattern}")
        return pattern
    
    def _analyze_traffic_type(self, profile: ProjectProfile) -> str:
        """Determine traffic type based on pattern"""
        pattern_map = {
            "steady": "consistent-low-variance",
            "peak_hours": "predictable-peaks",
            "bursty": "unpredictable-spikes",
            "seasonal": "periodic-variations"
        }
        return pattern_map.get(profile.traffic_pattern, "unknown")
    
    def _analyze_db_load(self, profile: ProjectProfile) -> str:
        """Analyze database load characteristics"""
        features = [f.lower() for f in profile.features]
        
        # Read-heavy indicators
        read_indicators = ["analytics", "dashboard", "reporting", "search"]
        read_score = sum(1 for ind in read_indicators if any(ind in f for f in features))
        
        # Write-heavy indicators
        write_indicators = ["upload", "tracking", "logging", "real-time"]
        write_score = sum(1 for ind in write_indicators if any(ind in f for f in features))
        
        if write_score > read_score * 1.5:
            return "write-heavy"
        elif read_score > write_score * 1.5:
            return "read-heavy"
        else:
            return "balanced"
    
    def _analyze_storage_access(self, profile: ProjectProfile) -> str:
        """Analyze storage access patterns"""
        features = [f.lower() for f in profile.features]
        
        # Hot storage indicators
        hot_indicators = ["image", "video", "real-time", "cdn"]
        hot_score = sum(1 for ind in hot_indicators if any(ind in f for f in features))
        
        # Cold storage indicators
        cold_indicators = ["archive", "backup", "historical", "logs"]
        cold_score = sum(1 for ind in cold_indicators if any(ind in f for f in features))
        
        if hot_score > cold_score:
            return "frequent-reads"
        elif cold_score > 0:
            return "mixed-hot-cold"
        else:
            return "occasional-access"
    
    def _analyze_scaling_need(self, profile: ProjectProfile) -> str:
        """Determine scaling requirements"""
        if profile.traffic_pattern in ["bursty", "peak_hours"]:
            return "auto-scale-required"
        elif profile.traffic_pattern == "seasonal":
            return "scheduled-scaling"
        elif profile.expected_users > 100000:
            return "horizontal-scaling"
        else:
            return "fixed-capacity"
    
    def _analyze_cpu_pattern(self, profile: ProjectProfile) -> str:
        """Analyze CPU usage pattern"""
        backend = profile.tech_stack.backend.lower()
        features = [f.lower() for f in profile.features]
        
        # CPU intensive indicators
        cpu_intensive = ["java", "spring", "machine learning", "video", "encoding"]
        is_cpu_intensive = any(ind in backend for ind in cpu_intensive) or \
                          any(ind in f for f in features for ind in cpu_intensive)
        
        if is_cpu_intensive:
            return "cpu-intensive"
        elif profile.traffic_pattern == "bursty":
            return "variable-cpu"
        else:
            return "moderate-cpu"
    
    def _analyze_memory_pattern(self, profile: ProjectProfile) -> str:
        """Analyze memory usage pattern"""
        backend = profile.tech_stack.backend.lower()
        cache = profile.tech_stack.cache
        features = [f.lower() for f in profile.features]
        
        # Memory intensive indicators
        memory_intensive = ["java", "jvm", "cache", "redis", "analytics"]
        is_memory_intensive = any(ind in backend for ind in memory_intensive) or \
                             (cache and "redis" in cache.lower()) or \
                             any("analytics" in f for f in features)
        
        if is_memory_intensive:
            return "memory-intensive"
        elif profile.expected_users > 50000:
            return "moderate-memory"
        else:
            return "low-memory"
    
    def _identify_peak_hours(self, profile: ProjectProfile) -> Optional[List[int]]:
        """Identify likely peak hours based on project type"""
        project_name = profile.project_name.lower()
        
        # Food delivery: lunch and dinner times
        if "food" in project_name or "delivery" in project_name or "restaurant" in project_name:
            return [12, 13, 19, 20, 21]
        
        # E-commerce: evening shopping
        elif "ecommerce" in project_name or "shop" in project_name or "store" in project_name:
            return [18, 19, 20, 21, 22]
        
        # Business apps: work hours
        elif "business" in project_name or "enterprise" in project_name or "crm" in project_name:
            return [9, 10, 11, 14, 15, 16]
        
        # Entertainment: evening/night
        elif "video" in project_name or "game" in project_name or "entertainment" in project_name:
            return [19, 20, 21, 22, 23]
        
        # Default: general peak hours
        else:
            return [9, 12, 18, 20]
    
    def get_pattern_summary(self, pattern: UsagePattern) -> str:
        """Get human-readable pattern summary"""
        summary_parts = [
            f"Traffic: {pattern.traffic_type}",
            f"Database: {pattern.db_load}",
            f"Storage: {pattern.storage_access}",
            f"Scaling: {pattern.scaling_need}",
            f"CPU: {pattern.cpu_pattern}",
            f"Memory: {pattern.memory_pattern}"
        ]
        
        if pattern.peak_hours:
            hours_str = ", ".join(f"{h}:00" for h in pattern.peak_hours)
            summary_parts.append(f"Peak Hours: {hours_str}")
        
        return "\n".join(summary_parts)