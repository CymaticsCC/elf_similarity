from django.contrib import admin

# Register your models here.


from .models import ioc_urls_record
admin.site.register(ioc_urls_record)

from .models import ioc_urls
admin.site.register(ioc_urls)

from .models import download_record
admin.site.register(download_record)

from .models import binary
admin.site.register(binary)


from .models import ssdeep_compare
admin.site.register(ssdeep_compare)
