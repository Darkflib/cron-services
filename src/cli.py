"""CLI interface for running jobs locally."""

import argparse
import asyncio
import logging
import sys

from .jobs import JOBS

logger = logging.getLogger(__name__)


async def run_job(job_name: str) -> int:
    """Run a specific job.

    Args:
        job_name: Name of job to run

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    if job_name not in JOBS:
        logger.error("Unknown job: %s", job_name)
        logger.info("Available jobs: %s", ", ".join(JOBS.keys()))
        return 1

    job_class = JOBS[job_name]
    job = job_class()

    try:
        result = await job.run()
    except Exception as e:
        logger.exception("Job raised an exception: %s", e)
        return 1

    if isinstance(result, dict) and result.get("status") == "success":
        logger.info("Job completed successfully: %s", result)
        return 0
    else:
        logger.error("Job failed: %s", result)
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Run scheduled data sync jobs")
    parser.add_argument(
        "job",
        choices=list(JOBS.keys()),
        help="Job to execute",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level",
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run job
    exit_code = asyncio.run(run_job(args.job))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
