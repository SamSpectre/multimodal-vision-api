"""
Health Check Router

Health checks are CRITICAL for production systems.
They tell orchestrators (Kubernetes, Docker, load balancers) if your service is working.

=== HEALTH CHECK TYPES ===

1. Liveness (/live)
   - "Is the process alive?"
   - If fails: Restart the container
   - Should be simple (just return 200 OK)

2. Readiness (/ready)
   - "Can the service handle requests?"
   - If fails: Remove from load balancer (don't restart)
   - Check dependencies (database, external APIs)

3. Startup (optional)
   - "Is the service done starting?"
   - For slow-starting services
   - Prevents premature health checks

=== WHY THIS MATTERS ===

In production (Kubernetes example):
    livenessProbe:
      httpGet:
        path: /api/v1/health/live
      periodSeconds: 10

    readinessProbe:
      httpGet:
        path: /api/v1/health/ready
      periodSeconds: 5

If readiness fails:
    - Service removed from load balancer
    - No traffic sent to unhealthy instance
    - Other instances handle requests

If liveness fails:
    - Container gets restarted
    - Useful for recovering from deadlocks
"""

import os
from datetime import datetime

from fastapi import APIRouter, HTTPException

# Import to check service availability
from src.clients.mistral_client import is_mistral_available


# Create the router
router = APIRouter()


@router.get("/")
async def health_check():
    """
    Basic health check endpoint.

    Returns:
        Overall health status of the API
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Vision Platform API",
        "version": "1.0.0"
    }


@router.get("/live")
async def liveness_check():
    """
    Liveness probe endpoint.

    This should be a simple check that the process is running.
    DO NOT check external dependencies here!

    If this fails, the orchestrator will restart the container.
    We only want restarts for actual process failures, not dependency issues.

    Returns:
        Simple alive status
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/ready")
async def readiness_check():
    """
    Readiness probe endpoint.

    Checks if the service can handle requests.
    Verifies external dependencies are accessible.

    If this fails:
    - Service is removed from load balancer
    - No traffic is sent to this instance
    - Container is NOT restarted

    Returns:
        Readiness status with dependency checks

    Raises:
        HTTPException 503 if not ready
    """
    checks = {
        "mistral_ocr": is_mistral_available(),
        "openai": bool(os.getenv("OPENAI_API_KEY")),
    }

    # Calculate overall status
    all_ready = all(checks.values())
    essential_ready = checks.get("openai", False)  # OpenAI is essential

    if not essential_ready:
        # Service cannot function without essential dependencies
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "message": "Essential services not available",
                "checks": checks
            }
        )

    return {
        "status": "ready" if all_ready else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks,
        "message": "All systems operational" if all_ready else "Some optional services unavailable"
    }


@router.get("/dependencies")
async def dependency_check():
    """
    Detailed dependency status.

    Shows status of all external services and configuration.
    Useful for debugging and monitoring dashboards.

    Returns:
        Detailed status of all dependencies
    """
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "dependencies": {
            "mistral_ocr": {
                "configured": is_mistral_available(),
                "model": "mistral-ocr-2512",
                "purpose": "Document OCR processing"
            },
            "openai": {
                "configured": bool(os.getenv("OPENAI_API_KEY")),
                "model": "gpt-4o",
                "purpose": "Vision analysis and classification"
            },
        },
        "environment": {
            "debug_mode": bool(os.getenv("DEBUG")),
            "python_env": os.getenv("PYTHON_ENV", "development"),
        }
    }


@router.get("/metrics")
async def metrics():
    """
    Basic metrics endpoint.

    In production, you'd use Prometheus metrics here.
    This is a placeholder showing the pattern.

    TODO: Implement proper Prometheus metrics with:
    - prometheus_client library
    - Counter for requests
    - Histogram for latencies
    - Gauge for current connections

    Returns:
        Basic metrics data
    """
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "note": "Prometheus metrics coming in Phase 5",
        "placeholder_metrics": {
            "requests_total": "TODO",
            "requests_in_progress": "TODO",
            "request_latency_seconds": "TODO"
        }
    }
