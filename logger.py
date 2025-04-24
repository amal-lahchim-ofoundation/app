import logging


# Logger setup with ANSI color formatter
class AnsiColorFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord):
        no_style = "\033[0m"
        grey = "\033[90m"
        yellow = "\033[93m"
        green = "\033[32m"
        cyan = "\033[36m"
        red = "\033[31m"
        red_light = "\033[91m"
        bold = "\033[91m"
        start_style = {
            "DEBUG": grey,
            "CONNECT": cyan,  # Custom "CONNECT" color
            "INFO": green,
            "WARNING": yellow,
            "ERROR": red,
            "CRITICAL": red_light + bold,
        }.get(record.levelname, no_style)
        return f"{start_style}{super().format(record)}{no_style}"


# Add custom log level 'CONNECT' with level value 15
logging.addLevelName(15, "CONNECT")


# Custom log method for CONNECT
def CONNECT(self, message, *args, **kwargs):
    if self.isEnabledFor(15):
        self._log(15, message, args, **kwargs)


# Attach the custom 'CONNECT' method to the logger
logging.Logger.CONNECT = CONNECT

# Set up logger
logger = logging.getLogger("app")

# Check if the logger already has handlers to avoid duplication
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    formatter = AnsiColorFormatter(
        "{asctime} | {levelname:<8s} | {name:<20s} | {message}", style="{"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Set the logger level
logger.setLevel(logging.DEBUG)
