# -*- coding: utf-8 -*-
"""
Config file

"""
import os

### Reference Calendar Year
REFERENCE_CALENDAR_YEAR = 2024

### Whatif year to run (used by scenario planner module)
WHATIF_YEAR = 2024

## DMA_FLAG
DMA_FLAG = 0
### Directories
OPTIM_INPUT_DIR = os.path.join(os.getcwd(), "app_server", "optim_input")
OPTIM_OUTPUT_DIR = os.path.join(os.getcwd(), "app_server", "optim_output")
OPTIM_LOG_DIR = os.path.join(os.getcwd(), "app_server", "optim_logs")

