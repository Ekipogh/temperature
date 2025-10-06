from django.shortcuts import render

# Create your views here.


def daemon_dashboard(request):
    return render(request, "temperatire_dashboard/daemon_info.html")
