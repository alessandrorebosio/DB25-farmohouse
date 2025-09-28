from django.shortcuts import render
from django.http import HttpRequest, HttpResponse


# Create your views here.
def homepage(request: HttpRequest) -> HttpResponse:
    """
    Renders the "index.html" page when a request is made to the homepage.
    """
    return render(request, "index.html")
