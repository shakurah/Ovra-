from django.contrib import admin
from .models import BOEUpdateLog, BOEDocument, BOEArticle

@admin.register(BOEUpdateLog)
class BOEUpdateLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "status", "articles_ingested", "message")
    list_filter = ("status", "timestamp")
    search_fields = ("message",)




admin.site.register(BOEDocument)
admin.site.register(BOEArticle)
