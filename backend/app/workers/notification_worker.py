import logging
import os
import time

from sqlalchemy import inspect

from app.database import engine
from app.services.notification_outbox import process_due_deliveries
from app.services.data_retention import run_retention_cleanup

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("govconnectx.notification_worker")


def wait_for_schema():
    required_tables = {"notification_deliveries", "phone_verifications"}
    while True:
        try:
            if required_tables.issubset(set(inspect(engine).get_table_names())):
                return
        except Exception:
            logger.exception("Could not check notification worker database readiness")
        logger.info("Waiting for API database migrations before starting notification worker")
        time.sleep(5)


def main():
    wait_for_schema()
    poll_seconds = max(5, int(os.getenv("NOTIFICATION_WORKER_POLL_SECONDS", "15")))
    batch_size = max(1, min(100, int(os.getenv("NOTIFICATION_WORKER_BATCH_SIZE", "25"))))
    logger.info("GovConnectX notification worker started")
    last_cleanup = time.monotonic() - 86400
    while True:
        try:
            if time.monotonic() - last_cleanup >= 86400:
                counts = run_retention_cleanup()
                logger.info("Retention cleanup completed: %s", counts)
                last_cleanup = time.monotonic()
            processed = process_due_deliveries(batch_size=batch_size)
            if processed:
                logger.info("Processed %s notification deliveries", processed)
        except Exception:
            logger.exception("Notification worker cycle failed")
        time.sleep(poll_seconds)


if __name__ == "__main__":
    main()
