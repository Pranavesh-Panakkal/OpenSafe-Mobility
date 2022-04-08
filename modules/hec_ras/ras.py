"""Codes realted to ras"""
import psutil
import os


def kill_a_process(process_name="Ras.exe"):
    # First check status
    if check_if_a_process_is_active(process_name=process_name):
        # Now that process is active, kill it
        killer(process_name=process_name)
        # Check status
        if check_if_a_process_is_active(process_name=process_name):
            # If the process still exists, kill it
            kill_process_using_psutil(process_name=process_name)
            if check_if_a_process_is_active(process_name=process_name):
                return False
            else:
                return True
        else:
            return True
    else:
        return True


def killer(process_name="Ras.exe"):
    os.system(f"taskkill /im {process_name}")


def kill_process_using_psutil(process_name="Ras.exe"):
    for proc in psutil.process_iter():
        # check whether the process name matches
        if proc.name() == process_name:
            proc.kill()


def check_if_a_process_is_active(process_name="Ras.exe"):
    for p in psutil.process_iter():
        try:
            if p.name().lower() == "ras.exe":
                return True
        except psutil.Error:
            pass
    # If no items return true, return false
    return False
