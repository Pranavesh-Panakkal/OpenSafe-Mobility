# Title     : OpenSafe Mobility
# Objective : This repository contains all the necessary code to replicate OpenSafe Mobility workflow.
# Created by: Pranavesh Panakkal (pranavesh@rice.edu)
# Released on: 2022-04-07
# Version   : 1.0
""""""
import hydra
from omegaconf import DictConfig
import logging
from modules.OpenSafeMobility import OpenSafeMobility
import schedule
import time

log = logging.getLogger(__name__)


@hydra.main(config_path="configs", config_name="config")
def main(config: DictConfig) -> None:
    # Initiate OpenSafe Mobility Class
    analysis = OpenSafeMobility(config=config)
    # Define the scheduler and run the model
    schedule.every(config.time_step).minutes.do(analysis.run)
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()
