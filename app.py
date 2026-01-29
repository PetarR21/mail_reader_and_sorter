from sort_emails import process_mails
import time
import logging

logging.basicConfig(
    filename="mail_sorter.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def run_mail_processor():
    """Run the mail processor continuously every 30 seconds"""
    logger.info("Starting mail processor...")

    while True:
        try:
            logger.info(f"Processing mails... ({time.strftime('%Y-%m-%d %H:%M:%S')})")
            process_mails()
            logger.info("Mail processing completed")
        except Exception as e:
            logger.info(f"Error processing mails: {e}")

        # Wait 30 seconds before the next execution
        time.sleep(30)


if __name__ == "__main__":
    run_mail_processor()
