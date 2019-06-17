from django.contrib import admin

from .models import *


admin.site.register(User)
admin.site.register(Content)
admin.site.register(Comment)
admin.site.register(Meta)
admin.site.register(Link)
admin.site.register(Setting)
admin.site.register(Relationship)
