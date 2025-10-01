from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError


class Temperature(models.Model):
    # Index for time-based queries
    timestamp = models.DateTimeField(db_index=True)
    location = models.CharField(
        max_length=100,
        db_index=True,  # Index for location-based queries
        help_text="Location where temperature was measured"
    )
    temperature = models.FloatField(
        validators=[
            MinValueValidator(-50.0,
                              message="Temperature cannot be below -50°C"),
            MaxValueValidator(70.0, message="Temperature cannot be above 70°C")
        ],
        help_text="Temperature in Celsius"
    )
    humidity = models.FloatField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(0.0, message="Humidity cannot be below 0%"),
            MaxValueValidator(100.0, message="Humidity cannot be above 100%")
        ],
        help_text="Relative humidity percentage"
    )

    class Meta:
        # Composite index for common query patterns
        indexes = [
            models.Index(fields=['location', 'timestamp']),
            # Different order for different queries
            models.Index(fields=['timestamp', 'location']),
        ]
        # REMOVED the unique constraint that was causing issues
        ordering = ['-timestamp']  # Default ordering by newest first
        verbose_name = "Temperature Reading"
        verbose_name_plural = "Temperature Readings"

    def clean(self):
        """Custom validation logic."""
        super().clean()

        # Additional validation
        if self.location and len(self.location.strip()) == 0:
            raise ValidationError(
                "Location cannot be empty or just whitespace")

        # Normalize location name
        if self.location:
            self.location = self.location.strip().title()

    def save(self, *args, **kwargs):
        """Override save to ensure validation."""
        self.full_clean()  # Ensures all validators run
        super().save(*args, **kwargs)

    def __str__(self):
        humidity_str = f", {self.humidity}% humidity" if self.humidity is not None else ""
        return f"{self.location} - {self.temperature}°C{humidity_str} at {self.timestamp}"

    @property
    def temperature_fahrenheit(self):
        """Convert temperature to Fahrenheit."""
        return (self.temperature * 9/5) + 32
