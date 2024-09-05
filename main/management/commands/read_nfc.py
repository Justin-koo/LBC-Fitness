import ctypes
import time
from django.core.management.base import BaseCommand
import nfc
from main.models import NFCTag
from smartcard.System import readers
from smartcard.util import toHexString
import subprocess

class Command(BaseCommand):
    help = 'Read NFC tags'

    def handle(self, *args, **kwargs):
        command = "pnputil"
        params = '/restart-device "USB\\VID_072F&PID_2200\\7&1441131D&0&2"'

        def run_as_admin(command, params):
            # Constants for ShellExecute
            SW_SHOWNORMAL = 1
            verb = "runas"  # Indicates to run the program as admin

            # Execute the command as admin
            try:
                result = ctypes.windll.shell32.ShellExecuteW(
                    None, verb, command, params, None, SW_SHOWNORMAL
                )
                if result <= 32:
                    raise RuntimeError(f"Failed to execute {command} with params {params} as admin")
                print("Command executed successfully.")
            except Exception as e:
                print(f"Failed to execute the command: {e}")

        def on_connect(tag):
            uid = tag.identifier.hex()
            print(f"NFC Tag UID: {uid}")
            return True

        while True:
            try:
                clf = nfc.ContactlessFrontend('usb')
                print("waiting for input")
                clf.connect(rdwr={'on-connect': on_connect})
                clf.close()
                print('closed')
                time.sleep(1)
                run_as_admin(command, params)
                print('restarted')
                time.sleep(1)

            except Exception as e:
                print(f"Error: {e}")
                run_as_admin(command, params)
                time.sleep(2)

                

        
