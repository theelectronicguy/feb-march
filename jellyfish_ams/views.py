from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from company_assets.models import *


def error_404_view(request, exception):
    return render(request, "common/404-page-not-found.html", status=404)
