"""
Token usage tracking utilities for monitoring OpenAI API consumption and costs.
This module provides comprehensive tracking of token usage across the application.
"""

import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from threading import Lock
import logging

logger = logging.getLogger(__name__)


@dataclass
class TokenUsageRecord:
    """Individual token usage record for a single API call."""

    timestamp: float
    operation_type: str  # 'resume_parsing', 'job_parsing', 'talent_matching', etc.
    model_name: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: float
    operation_id: Optional[str] = None  # For tracking specific operations


class TokenTracker:
    """Centralized token usage tracker with cost estimation."""

    # OpenAI pricing per 1K tokens (as of 2024)
    TOKEN_PRICES = {
        "gpt-3.5-turbo": {
            "input": 0.0015,  # $0.0015 per 1K input tokens
            "output": 0.002,  # $0.002 per 1K output tokens
        },
        "gpt-4": {
            "input": 0.03,  # $0.03 per 1K input tokens
            "output": 0.06,  # $0.06 per 1K output tokens
        },
        "gpt-4-turbo": {
            "input": 0.01,  # $0.01 per 1K input tokens
            "output": 0.03,  # $0.03 per 1K output tokens
        },
    }

    def __init__(self):
        """Initialize the token tracker."""
        self.usage_records: List[TokenUsageRecord] = []
        self.operation_totals: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()
        self.session_start_time = time.time()

    def record_usage(
        self,
        operation_type: str,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int,
        operation_id: Optional[str] = None,
    ) -> float:
        """Record token usage for an operation.

        Args:
            operation_type: Type of operation (e.g., 'resume_parsing')
            model_name: Name of the model used
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens
            operation_id: Optional identifier for the specific operation

        Returns:
            Estimated cost for this operation
        """
        with self._lock:
            total_tokens = prompt_tokens + completion_tokens
            estimated_cost = self._calculate_cost(
                model_name, prompt_tokens, completion_tokens
            )

            # Create usage record
            record = TokenUsageRecord(
                timestamp=time.time(),
                operation_type=operation_type,
                model_name=model_name,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                estimated_cost=estimated_cost,
                operation_id=operation_id,
            )

            self.usage_records.append(record)

            # Update operation totals
            if operation_type not in self.operation_totals:
                self.operation_totals[operation_type] = {
                    "total_tokens": 0,
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "estimated_cost": 0.0,
                    "call_count": 0,
                    "models_used": set(),
                }

            totals = self.operation_totals[operation_type]
            totals["total_tokens"] += total_tokens
            totals["prompt_tokens"] += prompt_tokens
            totals["completion_tokens"] += completion_tokens
            totals["estimated_cost"] += estimated_cost
            totals["call_count"] += 1
            totals["models_used"].add(model_name)

            return estimated_cost

    def _calculate_cost(
        self, model_name: str, prompt_tokens: int, completion_tokens: int
    ) -> float:
        """Calculate estimated cost for token usage.

        Args:
            model_name: Name of the model
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens

        Returns:
            Estimated cost in USD
        """
        # Normalize model name for pricing lookup
        model_key = model_name.lower()
        if "gpt-4-turbo" in model_key:
            pricing = self.TOKEN_PRICES.get("gpt-4-turbo")
        elif "gpt-4" in model_key:
            pricing = self.TOKEN_PRICES.get("gpt-4")
        elif "gpt-3.5-turbo" in model_key:
            pricing = self.TOKEN_PRICES.get("gpt-3.5-turbo")
        else:
            # Default to GPT-3.5-turbo pricing for unknown models
            pricing = self.TOKEN_PRICES.get("gpt-3.5-turbo")
            logger.warning(f"Unknown model '{model_name}', using GPT-3.5-turbo pricing")

        if not pricing:
            return 0.0

        input_cost = (prompt_tokens / 1000) * pricing["input"]
        output_cost = (completion_tokens / 1000) * pricing["output"]

        return input_cost + output_cost

    def get_session_summary(self) -> Dict[str, Any]:
        """Get comprehensive summary of token usage for this session.

        Returns:
            Dictionary containing session statistics
        """
        with self._lock:
            if not self.usage_records:
                return {
                    "session_duration": time.time() - self.session_start_time,
                    "total_operations": 0,
                    "total_cost": 0.0,
                    "total_tokens": 0,
                    "operation_breakdown": {},
                }

            total_cost = sum(record.estimated_cost for record in self.usage_records)
            total_tokens = sum(record.total_tokens for record in self.usage_records)

            # Model usage breakdown
            model_usage = {}
            for record in self.usage_records:
                if record.model_name not in model_usage:
                    model_usage[record.model_name] = {
                        "calls": 0,
                        "tokens": 0,
                        "cost": 0.0,
                    }
                model_usage[record.model_name]["calls"] += 1
                model_usage[record.model_name]["tokens"] += record.total_tokens
                model_usage[record.model_name]["cost"] += record.estimated_cost

            # Operation type breakdown
            operation_breakdown = {}
            for op_type, totals in self.operation_totals.items():
                operation_breakdown[op_type] = {
                    "calls": totals["call_count"],
                    "total_tokens": totals["total_tokens"],
                    "prompt_tokens": totals["prompt_tokens"],
                    "completion_tokens": totals["completion_tokens"],
                    "estimated_cost": totals["estimated_cost"],
                    "models_used": list(totals["models_used"]),
                    "avg_tokens_per_call": (
                        totals["total_tokens"] / totals["call_count"]
                        if totals["call_count"] > 0
                        else 0
                    ),
                }

            return {
                "session_duration": time.time() - self.session_start_time,
                "total_operations": len(self.usage_records),
                "total_cost": total_cost,
                "total_tokens": total_tokens,
                "total_prompt_tokens": sum(
                    record.prompt_tokens for record in self.usage_records
                ),
                "total_completion_tokens": sum(
                    record.completion_tokens for record in self.usage_records
                ),
                "operation_breakdown": operation_breakdown,
                "model_usage": model_usage,
                "cost_per_operation_type": {
                    op_type: totals["estimated_cost"]
                    for op_type, totals in self.operation_totals.items()
                },
            }

    def print_session_summary(self) -> None:
        """Print a formatted summary of token usage and costs."""
        summary = self.get_session_summary()

        print("\n" + "=" * 80)
        print("💰 TOKEN USAGE & COST ANALYSIS")
        print("=" * 80)

        # Session overview
        duration_minutes = summary["session_duration"] / 60
        print(f"⏱️  Session Duration: {duration_minutes:.2f} minutes")
        print(f"🔢 Total API Calls: {summary['total_operations']}")
        print(f"🎯 Total Tokens Used: {summary['total_tokens']:,}")

        # Handle case where no API calls were made
        if summary["total_operations"] > 0:
            print(f"   • Input Tokens: {summary['total_prompt_tokens']:,}")
            print(f"   • Output Tokens: {summary['total_completion_tokens']:,}")
            print(f"💵 Estimated Total Cost: ${summary['total_cost']:.4f}")
        else:
            print("   • No API calls were made")
            print("💵 Estimated Total Cost: $0.0000")

        # Model breakdown
        if summary["model_usage"]:
            print(f"\n📊 MODEL USAGE BREAKDOWN:")
            print("-" * 50)
            for model, usage in summary["model_usage"].items():
                print(f"🤖 {model}:")
                print(f"   • Calls: {usage['calls']}")
                print(f"   • Tokens: {usage['tokens']:,}")
                print(f"   • Cost: ${usage['cost']:.4f}")

        # Operation breakdown
        if summary["operation_breakdown"]:
            print(f"\n🎯 OPERATION TYPE BREAKDOWN:")
            print("-" * 50)
            for op_type, breakdown in summary["operation_breakdown"].items():
                print(f"📋 {op_type.replace('_', ' ').title()}:")
                print(f"   • Calls: {breakdown['calls']}")
                print(f"   • Total Tokens: {breakdown['total_tokens']:,}")
                print(f"   • Avg Tokens/Call: {breakdown['avg_tokens_per_call']:.0f}")
                print(f"   • Cost: ${breakdown['estimated_cost']:.4f}")
                print(f"   • Models: {', '.join(breakdown['models_used'])}")

        # Cost efficiency insights
        if summary["total_operations"] > 0:
            avg_cost_per_operation = summary["total_cost"] / summary["total_operations"]
            avg_tokens_per_operation = (
                summary["total_tokens"] / summary["total_operations"]
            )

            print(f"\n📈 EFFICIENCY METRICS:")
            print("-" * 50)
            print(f"💲 Average Cost per Operation: ${avg_cost_per_operation:.4f}")
            print(f"🎯 Average Tokens per Operation: {avg_tokens_per_operation:.0f}")

            if summary["total_cost"] > 0.10:
                print(f"💡 Cost Optimization Tips:")
                print(f"   • Consider using GPT-3.5-turbo for simpler parsing tasks")
                print(f"   • Review max_tokens settings to avoid over-provisioning")
                print(f"   • Monitor chunk sizes to optimize token usage")

        print("=" * 80)

    def reset_session(self) -> None:
        """Reset the tracker for a new session."""
        with self._lock:
            self.usage_records.clear()
            self.operation_totals.clear()
            self.session_start_time = time.time()


# Global token tracker instance
_global_tracker = TokenTracker()


def get_token_tracker() -> TokenTracker:
    """Get the global token tracker instance."""
    return _global_tracker


def record_token_usage(
    operation_type: str,
    model_name: str,
    prompt_tokens: int,
    completion_tokens: int,
    operation_id: Optional[str] = None,
) -> float:
    """Convenience function to record token usage.

    Args:
        operation_type: Type of operation
        model_name: Model used
        prompt_tokens: Input tokens
        completion_tokens: Output tokens
        operation_id: Optional operation identifier

    Returns:
        Estimated cost for this operation
    """
    return _global_tracker.record_usage(
        operation_type, model_name, prompt_tokens, completion_tokens, operation_id
    )
