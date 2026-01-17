"""CLI interface for running jobs locally."""

import argparse
import asyncio
import logging
import sys

from .jobs import JOBS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


async def run_job(job_name: str) -> int:
    """Run a specific job.

    Args:
        job_name: Name of the job to run

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    if job_name not in JOBS:
        logger.error(f"Unknown job: {job_name}")
        logger.info(f"Available jobs: {', '.join(JOBS.keys())}")
        return 1

    job_class = JOBS[job_name]
    job = job_class()

    result = await job.run()

    if result["status"] == "success":
        logger.info(f"Job completed successfully: {result}")
        return 0
    else:
        logger.error(f"Job failed: {result}")
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

    # Update log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    # Run job
    exit_code = asyncio.run(run_job(args.job))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
