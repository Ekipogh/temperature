from django.db import models

# Create your models here.
class Temperature(models.Model):
    timestamp = models.DateTimeField()  # Remove auto_now_add to allow manual timestamps
    location = models.CharField(max_length=100)
    temperature = models.FloatField()
    humidity = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.location} - {self.temperature}°C at {self.timestamp}"
