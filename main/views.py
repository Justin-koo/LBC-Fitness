import time
from django.http import Http404, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import user_passes_test
from django.urls import reverse

from main.models import Member, PaymentLog, Price
from .forms import ExtendMembershipForm, MemberForm, PriceForm 
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.core.cache import cache
from smartcard.System import readers
from smartcard.util import toHexString
from smartcard.CardRequest import CardRequest
from smartcard.CardType import AnyCardType
from smartcard.CardType import ATRCardType
import nfc
from nfc.clf import RemoteTarget

def admin_check(user):
    return user.is_superuser

def index(request):
    # return redirect('member_list')
    return render(request, 'index.html')

def scan_nfc(request):
    try:
        # Get the list of available readers
        r = readers()
        if len(r) == 0:
            return JsonResponse({'success': False, 'error': 'No NFC readers available'})

        # Select the first reader
        reader = r[0]

        # Define the card type we are interested in (any card)
        # card_type = AnyCardType()
        atr_pattern = [0x3B, 0x8F, 0x80, 0x01, 0x80, 0x4F, 0x0C, 0xA0, 0x00, 0x00, 0x03, 0x06, 0x03, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x6A]
        card_type = ATRCardType(atr_pattern)

        # Create a request to wait for a card to be attached, with a timeout
        request = CardRequest(timeout=None, cardType=card_type, readers=[reader])

        # Wait for the card to be attached
        card_service = request.waitforcard()  # This will block until a card is detected or timeout occurs

        connection = card_service.connection
        connection.connect()

        try:
            # APDU command to get the UID of the NFC tag
            get_uid_apdu = [0xFF, 0xCA, 0x00, 0x00, 0x00]
            response, sw1, sw2 = connection.transmit(get_uid_apdu)

            # Check if the command was successful
            if sw1 == 0x90 and sw2 == 0x00:
                uid = toHexString(response).replace(" ", "").replace(":", "").replace("-", "")
                print(f"NFC Tag UID: {uid}")
                return JsonResponse({'success': True, 'nfc_tag_uid': uid})
            else:
                return JsonResponse({'success': False, 'error': f'Failed to read NFC tag, status words: {sw1:02X} {sw2:02X}'})

        except Exception as e:
            print(f"Error occurred while reading the NFC tag: {e}")
            return JsonResponse({'success': False, 'error': str(e)})

        finally:
            try:
                connection.disconnect()
            except Exception as e:
                print(f"Error during disconnect: {e}")

    except Exception as outer_exception:
        print(f"Outer Error: {outer_exception}")
        return JsonResponse({'success': False, 'error': str(outer_exception)})
    
# def scan_nfc(request):
#     try:
#         # Initialize the NFC reader
#         clf = nfc.ContactlessFrontend('usb')
#         if clf is None:
#             return JsonResponse({'success': False, 'error': 'No NFC readers available'})

#         print("Waiting for NFC tag...")
#         uid = None

#         def on_connect(tag):
#             nonlocal uid
#             uid = tag.identifier.hex()
#             print(f"NFC Tag UID: {uid}")

#         # This will block and wait for an NFC tag to be connected
#         try:
#             clf.connect(rdwr={'on-connect': on_connect})
#         except Exception as e:
#             print(f"Error occurred while reading the NFC tag: {e}")
#             return JsonResponse({'success': False, 'error': str(e)})
        
#         # clf.close()
#         return JsonResponse({'success': True, 'nfc_tag_uid': uid})

#     except Exception as outer_exception:
#         print(f"Outer Error: {outer_exception}")
#         return JsonResponse({'success': False, 'error': str(outer_exception)})

def member_list(request):
    members = Member.objects.all()  # Sort by latest modified date
    return render(request, 'member/index.html', {'members': members})

def create_member(request):
    redirect_url = reverse('member_list')
    
    if request.method == 'POST':
        form = MemberForm(request.POST)

        if form.is_valid():
            member = form.save(commit=False)

            # Handle the custom date range input
            daterange = request.POST.get('daterange')
            start_date, end_date = daterange.split(' - ')
            member.start_date = start_date
            member.end_date = end_date

            # Save the final member object
            member.save()

            # Calculate the duration in months
            start = timezone.datetime.strptime(start_date, '%Y-%m-%d')
            end = timezone.datetime.strptime(end_date, '%Y-%m-%d')
            duration_months = (end.year - start.year) * 12 + end.month - start.month

            # Find the corresponding price based on duration
            try:
                price = Price.objects.get(duration=duration_months)
                # Create the PaymentLog entry with the member's full name
                PaymentLog.objects.create(
                    member=member,
                    member_name=member.full_name,
                    duration=duration_months,
                    price=price.price,
                    membership_type='new'
                )
            except Price.DoesNotExist:
                # Handle the case where no matching price is found
                pass

            return JsonResponse({'success': True, 'message': 'Member has been successfully created!', 'redirectUrl': redirect_url})
        else:
            errors = form.errors
            return JsonResponse({'success': False, 'errors': errors})
        
    return render(request, 'member/create.html')

def edit_member(request, pk):
    redirect_url = reverse('member_list')
    member = get_object_or_404(Member, pk=pk)
    
    if request.method == 'POST':
        form = MemberForm(request.POST, instance=member)
        if form.is_valid():
            daterange = request.POST.get('daterange')
            start_date, end_date = daterange.split(' - ')
            member.start_date = start_date
            member.end_date = end_date

            form.save()
            return JsonResponse({'success': True, 'message': 'Member updated successfully!', 'redirectUrl': redirect_url})
    else:
        form = MemberForm(instance=member)
        daterange = f"{member.start_date} - {member.end_date}"

        latest_payment_log = PaymentLog.objects.filter(member=member).order_by('-created_at').first()
        if latest_payment_log:
            price = latest_payment_log.price
        else:
            price = None
    
    return render(request, 'member/edit.html', {'form': form, 'daterange': daterange, 'price': price})

def extend_membership(request, pk):
    redirect_url = reverse('member_list')
    member = get_object_or_404(Member, pk=pk)

    if request.method == 'POST':
        extension_months = int(request.POST['extension_duration'])
        
        # Calculate the new end date based on the extension
        new_end_date = member.end_date + timezone.timedelta(days=30 * extension_months)
        member.end_date = new_end_date
        member.save()

        # Record a new payment log for the extension
        try:
            price = Price.objects.get(duration=extension_months)
            PaymentLog.objects.create(
                member=member,
                member_name=member.full_name,
                duration=extension_months,
                price=price.price,
                membership_type='extended'
            )
        except Price.DoesNotExist:
            # Handle case where no price exists for the extension period
            pass

        return JsonResponse({'success': True, 'message': 'Membership extended successfully!', 'redirectUrl': redirect_url})

    return render(request, 'member/extend_membership.html', {'member': member})

@require_POST
def delete_member(request, pk):
    redirect_url = reverse('member_list')

    try: 
        member = get_object_or_404(Member, pk=pk)
    except Http404:
        return JsonResponse({'success': False, 'message': 'Member not found.', 'redirectUrl': redirect_url}, status=404)
    
    member.delete()

    return JsonResponse({'success': True, 'message': 'Member has been successfully deleted!', 'redirectUrl': redirect_url})

def price_list(request):
    prices = Price.objects.all()
    return render(request, 'price/index.html', {'prices': prices})

def create_price(request):
    redirect_url = reverse('price_list')

    if request.method == 'POST':
        form = PriceForm(request.POST)
        if form.is_valid():
            form.save()

            return JsonResponse({'success': True, 'message': 'Price has been successfully created!', 'redirectUrl': redirect_url})
        else:
            errors = form.errors
            return JsonResponse({'success': False, 'errors': errors})

    return render(request, 'price/create.html')

def edit_price(request, pk):
    redirect_url = reverse('price_list')
    price = get_object_or_404(Price, pk=pk)

    if request.method == 'POST':
        form = PriceForm(request.POST, instance=price)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True, 'message': 'Price updated successfully!', 'redirectUrl': redirect_url})
    else:
        form = PriceForm(instance=price)

    return render(request, 'price/edit.html', {
        'form': form,
    })

@require_POST
def delete_price(request, pk):
    redirect_url = reverse('price_list')

    try: 
        price = get_object_or_404(Price, pk=pk)
    except Http404:
        return JsonResponse({'success': False, 'message': 'Price not found.', 'redirectUrl': redirect_url}, status=404)
    
    price.delete()

    return JsonResponse({'success': True, 'message': 'Price has been successfully deleted!', 'redirectUrl': redirect_url})

def get_price(request):
    if request.method == 'GET':
        duration = request.GET.get('duration')
        try:
            price = Price.objects.get(duration=duration)
            return JsonResponse({'success': True, 'price': str(price.price)})
        except Price.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'No price found for the selected duration.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
        
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

def payment_log_list(request):
    payment_logs = PaymentLog.objects.all().order_by('-created_at')
    return render(request, 'payment/payment_log.html', {'payment_logs': payment_logs})