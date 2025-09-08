from django.contrib import admin
from . import models

# Register your models here.
admin.site.register(models.Person)
admin.site.register(models.User)
admin.site.register(models.Employee)
admin.site.register(models.EmployeeHistory)
admin.site.register(models.EmployeeShift)
admin.site.register(models.Shift)
