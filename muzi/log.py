from loguru import logger
import sys


FORMAT = '''[<m>{time:YYYY-MM-DD}</m> <g>{time:HH:mm:ss}</g>] [<lvl>{level}</lvl>] | {message}'''

logger.remove()
logger.add(sink=sys.stderr, format=FORMAT)
logger = logger.opt(colors=True)