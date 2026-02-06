from sort_emails import process_mails
import time
import logging
import traceback

logging.basicConfig(
    filename="mail_sorter.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def run_mail_processor():
    """Run the mail processor continuously every 30 seconds"""
    print("Starting mail processor...")

    while True:
        try:
            print(f"Processing mails... ({time.strftime('%Y-%m-%d %H:%M:%S')})")
            process_mails()
            print("Mail processing completed")
        except Exception as e:
            print(f"Error processing mails: {e}")
            print(traceback.format_exc())
            return

        # Wait 30 seconds before the next execution
        time.sleep(10)


if __name__ == "__main__":
    run_mail_processor()
