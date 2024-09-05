import ctypes
import json
import threading
import time
from channels.generic.websocket import WebsocketConsumer
from django.http import JsonResponse
import nfc
from smartcard.System import readers
from smartcard.util import toHexString
from smartcard.CardConnection import CardConnection
from smartcard.CardRequest import CardRequest
from smartcard.CardType import ATRCardType
from smartcard.ATR import ATR
from django.core.exceptions import ObjectDoesNotExist
from main.models import Member
from django.utils import timezone

class NFCConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
        self.run_nfc()

    def disconnect(self, close_code):
        print("NFC detection stopped.")

    def receive(self, text_data):
        data = json.loads(text_data)
        if data.get('action') == 'start_scan':
            self.run_nfc()

    def on_connect(self, connection):
        try:
            # APDU command to get the UID of the NFC tag
            get_uid_apdu = [0xFF, 0xCA, 0x00, 0x00, 0x00]
            uid, sw1, sw2 = connection.transmit(get_uid_apdu)

            if sw1 == 0x90 and sw2 == 0x00:
                uid_str = toHexString(uid).replace(" ", "")
                try:
                    member = Member.objects.get(nfc_tag_uid=uid_str)

                    today = timezone.now().date()
                    if member.start_date <= today <= member.end_date:
                        membership_status = 'Valid'
                    else:
                        membership_status = 'Expired'

                    self.send(text_data=json.dumps({
                        'message': f'Member found: {member.full_name}',
                        'member': {
                            'id': member.id,
                            'full_name': member.full_name,
                            'email': member.email,
                            'phone': member.phone,
                            'start_date': member.start_date.strftime('%Y-%m-%d'),
                            'end_date': member.end_date.strftime('%Y-%m-%d'),
                            'membership_status': membership_status
                        },
                        'type': 'member',
                    }))
                except ObjectDoesNotExist:
                    self.send(text_data=json.dumps({
                        'message': 'No member found with this NFC tag UID.',
                        'member': None,
                        'type': 'member',
                    }))
            else:
                self.send(text_data=json.dumps({
                    'message': f'Failed to read NFC tag, status words: {sw1:02X} {sw2:02X}',
                    'type': 'member',
                }))
        except Exception as e:
            self.send(text_data=json.dumps({
                'message': f"Error: {e}",
                'type': 'member',
            }))

    def run_nfc(self):
        try:
            # Get the list of available readers
            r = readers()
            if len(r) == 0:
                self.send(text_data=json.dumps({'message': 'No NFC readers available'}))
                return

            # Select the first reader
            reader = r[0]

            # Define the ATR pattern for the card type you are interested in
            atr_pattern = [0x3B, 0x8F, 0x80, 0x01, 0x80, 0x4F, 0x0C, 0xA0, 0x00, 0x00, 0x03, 0x06, 0x03, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x6A]
            card_type = ATRCardType(atr_pattern)

            # Create a request to wait for a card with the specified ATR
            card_request = CardRequest(timeout=None, cardType=card_type, readers=[reader])

            # Wait for a card to be attached
            card_service = card_request.waitforcard()  # This will block until a card matching the ATR is detected

            # Establish a connection to the card
            connection = card_service.connection
            connection.connect()

            # Process the card
            self.on_connect(connection)

            # Disconnect the card connection after processing
            # connection.disconnect()

        except Exception as e:
            self.send(text_data=json.dumps({
                'message': f"Error: {e}"
            }))

    # nfcpy as backup in case pyscard not working
    # def run_as_admin(self, command, params):
    #     SW_SHOWNORMAL = 1
    #     verb = "runas"

    #     try:
    #         result = ctypes.windll.shell32.ShellExecuteW(
    #             None, verb, command, params, None, SW_SHOWNORMAL
    #         )
    #         if result <= 32:
    #             raise RuntimeError(f"Failed to execute {command} with params {params} as admin")
    #         print("Device restarted successfully.")
    #     except Exception as e:
    #         self.send(text_data=json.dumps({
    #             'message': f"Failed to execute the command: {e}"
    #         }))

    # def connect(self):
    #     self.accept()
    #     self.clf = None
    #     self.command = "pnputil"
    #     self.params = '/restart-device "USB\\VID_072F&PID_2200\\7&1441131D&0&2"'
    #     self.stop_thread = False  # Flag to stop the thread
    #     if not hasattr(self, 'nfc_thread') or not self.nfc_thread.is_alive():
    #         self.nfc_thread = threading.Thread(target=self.run_nfc_loop, daemon=True)
    #         self.nfc_thread.start()

    # def disconnect(self, close_code):
    #     self.stop_thread = True
    #     if self.nfc_thread.is_alive():
    #         self.nfc_thread.join()  # Wait for the thread to finish
                
    #         if self.clf:
    #             self.clf.close()
    #             print("NFC reader connection closed")

    # def on_connect(self, tag):
    #     uid = tag.identifier.hex()
    #     try:
    #         member = Member.objects.get(nfc_tag_uid=uid)
    #         self.send(text_data=json.dumps({
    #             'message': f'Member found: {member.full_name}',
    #             'member': {
    #                 'full_name': member.full_name,
    #                 'email': member.email,
    #                 'phone': member.phone,
    #                 'start_date': member.start_date.strftime('%Y-%m-%d'),
    #                 'end_date': member.end_date.strftime('%Y-%m-%d'),
    #             }
    #         }))
    #     except ObjectDoesNotExist:
    #         self.send(text_data=json.dumps({
    #             'message': 'No member found with this NFC tag UID.'
    #         }))

    #     return True  # Indicate that the connection was successful

    # def run_nfc_loop(self):
    #     while not self.stop_thread:
    #         try:
    #             self.clf = nfc.ContactlessFrontend('usb')
                
    #             self.clf.connect(rdwr={'on-connect': self.on_connect})
    #             self.clf.close()

    #             time.sleep(5)

    #             self.run_as_admin(self.command, self.params)
    #             self.send(text_data=json.dumps({
    #                 'message': 'Device restarted. Waiting for next NFC tag...'
    #             }))

    #             time.sleep(1)

    #         except Exception as e:
    #             self.send(text_data=json.dumps({
    #                 'message': f"Error: {e}"
    #             }))
    #             self.run_as_admin(self.command, self.params)

    #             self.send(text_data=json.dumps({
    #                 'message': "Waiting for NFC Input..."
    #             }))
                
    #             time.sleep(2)
