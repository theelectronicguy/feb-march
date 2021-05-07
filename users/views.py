import datetime
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import SuccessMessageMixin
from django.template.loader import render_to_string
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from company_assets.models import *
from users.serializers import MyTokenObtainPairSerializer, UserImportSerializer
from emails.mail_sender import MailSender
from django.shortcuts import render, redirect
from django.contrib.auth import logout, authenticate, login
from django.contrib import messages
from company_assets.models.others import RequestedInventory
from users.utils import read_file
from company_assets.models.asset import Asset
from company_assets.models.accessory import Accessory
from company_assets.models.consumable import Consumable
from company_assets.models.component import Component
from company_assets.models.license import License
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy
from django.utils import timezone
from .forms import ChangePasswordForm
from users.models import *
from django.contrib.auth.hashers import check_password, make_password

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


#
def index(request):
    # todo: use .annotate(count=Count("id")) wh needed for query from same table
    if request.user.is_anonymous:
        return render(request, "common/login.html")
    elif request.user is not None and request.user.is_superuser is True:
        return redirect('/admin/', status=302)
    elif request.user is not None and request.user.is_staff is True:
        inv_requests = RequestedInventory.objects.filter(declined_by=None).select_related('inventory_content_type',
                                                                                          'requested_by')
        asset_count = format(Asset.objects.all().count(), '02')
        component_count = format(Component.objects.all().count(), '02')
        accessory_count = format(Accessory.objects.all().count(), '02')
        licences_count = format(License.objects.all().count(), '02')
        consumables_count = format(Consumable.objects.all().count(), '02')
        # inventory_history = InventoryHistory.objects.order_by(
        #     'inventory_object_id').select_related('inventory_content_type', 'user')

        context = {
            "asset_count": asset_count,
            "component_count": component_count,
            "accessory_count": accessory_count,
            "licences_count": licences_count,
            "consumables_count": consumables_count,
            # 'inventory_history': inventory_history,
            "requests": list(inv_requests),
        }
        return render(request, 'admin-module/admin_dashboard.html', context)
    else:
        assets = Asset.objects.filter(deleted_at__isnull=True).values(
            "name", "image", "description", "uuid")
        accessories = Accessory.objects.filter(deleted_at__isnull=True).values(
            "name", "image", "description", "uuid")
        consumables = Consumable.objects.filter(deleted_at__isnull=True).values(
            "name", "image", "description", "uuid")
        components = Component.objects.filter(deleted_at__isnull=True).values(
            "name", "image", "description", "uuid")
        licenses = License.objects.filter(deleted_at__isnull=True).values(
            "name", "image", "description", "uuid")
        assets_count = InventoryHistory.objects.filter(
            user=request.user).count()
        pending_count = RequestedInventory.objects.filter(
            requested_by=request.user).count()
        context = {
            "assets": list(assets),
            "accessory": list(accessories),
            "consumable": list(consumables),
            "component": list(components),
            "license": list(licenses),
            "assets_count": assets_count,
            "pending_count": pending_count
        }
        return render(request, "user-module/user_dashboard.html", context)


@login_required
def accept_hr(request, obj_id):
    try:
        request_inventory = RequestedInventory.objects.filter(id=obj_id).select_related('inventory_content_type',
                                                                                        'requested_by').last()

        inv_his_count = InventoryHistory.objects.filter(inventory_content_type=request_inventory.inventory_content_type,
                                                        inventory_object_id=request_inventory.inventory_object_id,
                                                        checkout_date__isnull=True).count()
        inventory_models = {"asset": Asset, "accessory": Accessory, "consumable": Consumable, "component": Component,
                            "license": License}
        model = inventory_models.get(request_inventory.inventory_content_type.model)

        inventory = model.objects.filter(id=request_inventory.inventory_object_id).values('quantity')
        if inv_his_count >= inventory[0]['quantity']:
            messages.error(request, f'Inventory Not in stock')
            return redirect('/')
        else:
            inventory_history = InventoryHistory.objects.create(
                inventory_content_type=request_inventory.inventory_content_type,
                inventory_object_id=request_inventory.inventory_object_id,
                user=request_inventory.requested_by,
                checkin_date=timezone.now()
            )
            request_inventory.delete()

            return redirect('/')
    except:
        return render(request, "common/404-page-not-found.html", status=404)


@login_required
def decline_hr(request, obj_id):
    requested_inventory = RequestedInventory.objects.get(id=obj_id)
    requested_inventory.declined_by = request.user
    requested_inventory.save()
    return redirect('/')


def login_user(request):
    if request.method == "POST":
        email = request.POST.get("email", '')
        password = request.POST.get("password", '')

        # check if user has entered correct credentials
        user = authenticate(username=email, password=password)
        if user is not None and user.is_superuser is False:
            login(request, user)
            return redirect('/')
        elif user is not None and user.is_superuser is True:
            login(request, user)
            return redirect('/admin/', status=302)
        elif user is not None and user.is_staff is True:
            login(request, user)
            return redirect('/')
        else:
            messages.error(request, "Invalid Credentials")
            return render(request, 'common/login.html', status=404)
    return render(request, 'common/login.html', status=404)


@login_required
def logout_user(request):
    logout(request)
    messages.success(request, "Successfully Logged Out")
    return redirect('/users/login')


class UserImportView(generics.CreateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = UserImportSerializer

    users= User.objects.all()
    for user in users:
        if user.type == "ADMIN":
            user.is_superuser = True
            
            
        elif user.designation == "HR":
            user.is_staff = True
            
        user.is_active = True
        user.password=make_password("123456")
        user.save()
    
    
        
    def post(self, request, *args, **kwargs):
        # headers in file
        # First Name	Last Name	Email Address	Experience	Designation	Technologies	Type
        # Hourly Rate	lastLogin	Email Verified	TimeLog Edited Access	Active	Deleted	Address
        try:
            
            excel_file = request.FILES['files']
            df = read_file(excel_file.name)
            
            

       
        except:
            return Response(data={'error': "invalid input"}, status=status.HTTP_400_BAD_REQUEST)

        users_list = df[["first_name", "last_name", "email"]].to_dict('records')

        print(users_list)
        
        
        serializer = UserImportSerializer(data=users_list, many=True)
        
        if serializer.is_valid():
            serializer.save()

            return Response(data="imported successfully", status=status.HTTP_201_CREATED)
        else:
            
            return Response(data="error", status=status.HTTP_400_BAD_REQUEST)


@login_required
def requests(request, inventory, inventory_uuid):
    try:
        inventory_models = {"asset": Asset, "accessory": Accessory, "consumable": Consumable, "component": Component,
                            "license": License}
        model = inventory_models.get(inventory)
        ctype = ContentType.objects.get(model=inventory)
        content = model.objects.get(uuid=inventory_uuid)
        user = request.user
        has_already_requested = RequestedInventory.objects.filter(requested_by=user, inventory_content_type=ctype,
                                                                  inventory_object_id=content.id,
                                                                  declined_by=None)
        if has_already_requested:
            messages.error(
                request, f'You have already made an request for {content.name}')
            return redirect('/')
        else:
            inventory = RequestedInventory(
                requested_by=user, inventory=content)
            inventory.save()
            # todo : Use later when used by real users
            # staff_user = list(User.objects.filter(is_staff=True, is_active=True).values('email'))
            staff_user = settings.ADMIN_EMAILS

            full_name = user.get_full_name()
            context = {
                'item': content.name,
                'full_name': full_name,
            }
            html_content = render_to_string(
                template_name="emails/company_assets/request_mail.html", context=context)
            MailSender().inventory_requested_email(html_content, staff_user)

            messages.success(request, "item requested successfully!")
            return redirect('/')
    except:
        return render(request, "common/404-page-not-found.html", status=404)


class PasswordsChangeView(SuccessMessageMixin, PasswordChangeView):
    form_class = ChangePasswordForm
    template_name = 'common/change-password.html'
    success_url = reverse_lazy('home')
    success_message = 'Password Changed Successfully!!'
