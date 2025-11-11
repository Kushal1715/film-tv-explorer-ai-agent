"""Health endpoint and observability for MCP server."""

import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Simple in-memory metrics store
_metrics: Dict[str, Any] = {
    "tool_calls": {},
    "errors": [],
    "start_time": datetime.now().isoformat()
}

def record_tool_call(tool_name: str, latency: float, success: bool):
    """Record a tool call for observability."""
    if tool_name not in _metrics["tool_calls"]:
        _metrics["tool_calls"][tool_name] = {
            "count": 0,
            "total_latency": 0.0,
            "success_count": 0,
            "error_count": 0
        }
    
    _metrics["tool_calls"][tool_name]["count"] += 1
    _metrics["tool_calls"][tool_name]["total_latency"] += latency
    if success:
        _metrics["tool_calls"][tool_name]["success_count"] += 1
    else:
        _metrics["tool_calls"][tool_name]["error_count"] += 1

def record_error(error_type: str, message: str):
    """Record an error."""
    _metrics["errors"].append({
        "type": error_type,
        "message": message,
        "timestamp": datetime.now().isoformat()
    })
    # Keep only last 100 errors
    if len(_metrics["errors"]) > 100:
        _metrics["errors"] = _metrics["errors"][-100:]

def get_health_response():
    """Get health check response data."""
    return {
        "status": "healthy",
        "uptime": (datetime.now() - datetime.fromisoformat(_metrics["start_time"])).total_seconds(),
        "metrics": {
            "tool_calls": {
                name: {
                    "count": stats["count"],
                    "avg_latency": stats["total_latency"] / stats["count"] if stats["count"] > 0 else 0,
                    "success_rate": stats["success_count"] / stats["count"] if stats["count"] > 0 else 0
                }
                for name, stats in _metrics["tool_calls"].items()
            },
            "error_count": len(_metrics["errors"]),
            "recent_errors": _metrics["errors"][-10:]  # Last 10 errors
        }
    }

def get_metrics_response():
    """Get detailed metrics response data."""
    return _metrics


