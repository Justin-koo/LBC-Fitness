import os
import django
import nfc

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
django.setup()

from main.models import NFCTag

def on_connect(tag):
    tag_id = tag.identifier.hex()
    print(f"Tag connected: {tag_id}")
    
    # Save or update tag in the database
    nfc_tag, created = NFCTag.objects.get_or_create(tag_id=tag_id)
    if not created:
        nfc_tag.save()
    
    return True

if __name__ == "__main__":
    try:
        clf = nfc.ContactlessFrontend('usb')
        clf.connect(rdwr={'on-connect': on_connect})
    except Exception as e:
        print(f"An error occurred: {e}")
