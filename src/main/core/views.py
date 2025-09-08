from django.shortcuts import render
from django.http import HttpRequest, HttpResponse


# Create your views here.
def homepage(request: HttpRequest) -> HttpResponse:
    return render(request, "index.html")
