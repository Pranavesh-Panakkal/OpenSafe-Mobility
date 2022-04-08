import subprocess
import os
from subprocess import PIPE
from subprocess import Popen, PIPE
from datetime import datetime


def sync_aws(config):
    os.system(config.publish.command_to_publish_the_map_to_aws)
