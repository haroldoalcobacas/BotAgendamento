from django.contrib import admin
from .models import Customer, Resource, Booking
from django.utils.text import slugify

# =======================================================
#  Configuração do Recurso (Sala/Estúdio)
# =======================================================


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    """
    Permite a administração dos Recursos (Salas/Estúdios)
    e garante que o slug seja preenchido automaticamente.
    """
    list_display = ('name', 'price_per_hour', 'slug')
    search_fields = ('name',)

    prepopulated_fields = {'slug': ('name',)}

    fields = ('name', 'slug', 'price_per_hour', 'description')

    def save_model(self, request, obj, form, change):
        if not obj.slug:
            obj.slug = slugify(obj.name)
        super().save_model(request, obj, form, change)


# =======================================================
#  Configuração da Reserva
# =======================================================

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """
    Permite visualizar e gerenciar as Reservas.
    """
    list_display = (
        'date', 'start_time',
        'end_time',
        'resource',
        'customer_phone',
        'status'
    )
    list_filter = ('status', 'resource', 'date')
    search_fields = ('customer__phone', 'customer__name', 'resource__name')
    date_hierarchy = 'date'
    readonly_fields = ('google_event_id', 'created_at')

    def customer_phone(self, obj):
        return obj.customer.phone
    customer_phone.short_description = 'Cliente (Telefone)'

# =======================================================
# Inline para Reservas (opcional, mas útil)
# =======================================================


class BookingInline(admin.TabularInline):

    model = Booking
    extra = 0
    fields = ('date', 'start_time', 'end_time', 'resource', 'status')
    readonly_fields = ('date', 'start_time', 'end_time', 'resource')
    can_delete = False


# =======================================================
#  Configuração do Cliente
# =======================================================

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    """
    Permite a visualização e gestão dos Clientes.
    """
    list_display = ('name', 'phone', 'created_at')
    search_fields = ('name', 'phone')
    readonly_fields = ('created_at',)

    inlines = [BookingInline]
