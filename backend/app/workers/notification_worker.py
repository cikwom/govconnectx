import logging
import os
import time

from app.services.notification_outbox import process_due_deliveries

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("govconnectx.notification_worker")


def main():
    poll_seconds = max(5, int(os.getenv("NOTIFICATION_WORKER_POLL_SECONDS", "15")))
    batch_size = max(1, min(100, int(os.getenv("NOTIFICATION_WORKER_BATCH_SIZE", "25"))))
    logger.info("GovConnectX notification worker started")
    while True:
        try:
            processed = process_due_deliveries(batch_size=batch_size)
            if processed:
                logger.info("Processed %s notification deliveries", processed)
        except Exception:
            logger.exception("Notification worker cycle failed")
        time.sleep(poll_seconds)


if __name__ == "__main__":
    main()
