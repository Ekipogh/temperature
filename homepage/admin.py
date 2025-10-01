from django.contrib import admin

from .models import Temperature


@admin.register(Temperature)
class TemperatureAdmin(admin.ModelAdmin):
    list_display = ("location", "temperature", "humidity", "timestamp")
    list_filter = ("location", "timestamp")
    search_fields = ("location",)
    ordering = ("-timestamp",)
    readonly_fields = ("timestamp",)

    # Group fields in the edit form
    fieldsets = (
        ("Location", {"fields": ("location",)}),
        ("Measurements", {"fields": ("temperature", "humidity")}),
        ("Timestamp", {"fields": ("timestamp",), "classes": ("collapse",)}),
    )

    # Customize the list display
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()

    # Add custom actions
    actions = ["export_to_csv"]

    def export_to_csv(self, request, queryset):
        import csv

        from django.http import HttpResponse

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="temperature_data.csv"'

        writer = csv.writer(response)
        writer.writerow(["Location", "Temperature (°C)", "Humidity (%)", "Timestamp"])

        for temp in queryset:
            writer.writerow(
                [temp.location, temp.temperature, temp.humidity or "", temp.timestamp]
            )

        return response

    export_to_csv.short_description = "Export selected temperatures to CSV"


# Customize admin site headers
admin.site.site_header = "Temperature Monitoring Admin"
admin.site.site_title = "Temperature Admin"
admin.site.index_title = "Welcome to Temperature Monitoring Administration"
