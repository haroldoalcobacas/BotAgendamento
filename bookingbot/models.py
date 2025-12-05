from django.db import models


class Customer(models.Model):
    name = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=30, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name or 'Cliente'} ({self.phone})"


class Resource(models.Model):
    name = models.CharField(
        max_length=100, unique=True, verbose_name="Recurso")
    slug = models.SlugField(max_length=100, unique=True, help_text="STÚDIO")
    price_per_hour = models.DecimalField(
        max_digits=6, decimal_places=2, default=50.00)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Booking(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pendente"),
        ("confirmed", "Confirmado"),
        ("canceled", "Cancelado"),
    )

    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="bookings")
    resource = models.ForeignKey(Resource, on_delete=models.PROTECT)

    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending")
    google_event_id = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-start_time"]

    def __str__(self):
        return f"{self.customer.phone} — {self.date} {self.start_time}"
