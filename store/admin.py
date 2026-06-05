from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import (Category, Product, HeroSlide, Testimonial,
                     NewsletterSubscriber, ContactMessage, Order,
                     OrderItem, UserProfile)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon', 'product_count']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']

    def product_count(self, obj):
        count = obj.products.count()
        return format_html('<span style="color:#00D4FF;font-weight:700;">{}</span>', count)
    product_count.short_description = 'Produits'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['product_thumb', 'name', 'category', 'price_display',
                    'stock', 'is_featured', 'is_available']
    list_filter = ['category', 'is_featured', 'is_available']
    list_editable = ['is_featured', 'is_available', 'stock']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Informations principales', {'fields': ('name', 'slug', 'category', 'description')}),
        ('Prix & Stock', {'fields': ('price', 'stock', 'unit', 'min_order')}),
        ('Médias', {'fields': ('image', 'image_url')}),
        ('Disponibilité', {'fields': ('is_featured', 'is_available', 'origin', 'season')}),
        ('Infos nutritionnelles', {'fields': ('nutritional_info',)}),
        ('Dates', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    def product_thumb(self, obj):
        url = obj.get_image_url()
        if url:
            return format_html('<img src="{}" style="width:48px;height:48px;object-fit:cover;border-radius:6px;">', url)
        return '—'
    product_thumb.short_description = 'Image'

    def price_display(self, obj):
        return format_html('<strong style="color:#00FF88;">{} FDJ</strong>', obj.price)
    price_display.short_description = 'Prix'


@admin.register(HeroSlide)
class HeroSlideAdmin(admin.ModelAdmin):
    list_display = ['title', 'order', 'is_active']
    list_editable = ['order', 'is_active']


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ['name', 'role', 'rating', 'is_active']
    list_editable = ['is_active']


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ['email', 'subscribed_at', 'is_active']


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'created_at', 'is_read']
    list_editable = ['is_read']
    readonly_fields = ['name', 'email', 'subject', 'message', 'created_at']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product_name', 'price', 'quantity', 'unit']
    fields = ['product_name', 'quantity', 'unit', 'price']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_num', 'client_info', 'status_badge', 'payment_badge',
                    'total_display', 'created_at', 'actions_btn']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['full_name', 'phone', 'email']
    readonly_fields = ['created_at', 'updated_at', 'screenshot_preview']
    inlines = [OrderItemInline]
    fieldsets = (
        ('Commande', {'fields': ('user', 'status', 'admin_note')}),
        ('Client', {'fields': ('full_name', 'email', 'phone')}),
        ('Livraison', {'fields': ('delivery_address', 'wilaya', 'notes')}),
        ('Paiement', {'fields': ('payment_method', 'transaction_ref', 'transaction_screenshot', 'screenshot_preview')}),
        ('Montant', {'fields': ('total_price', 'cgv_accepted')}),
        ('Dates', {'fields': ('created_at', 'updated_at')}),
    )
    actions = ['confirmer_commandes', 'rejeter_commandes', 'marquer_livree']

    def order_num(self, obj):
        return format_html('<strong>#{}  </strong>', obj.pk)
    order_num.short_description = '#'

    def client_info(self, obj):
        return format_html('<strong>{}</strong><br><small style="color:#888;">{}</small>', obj.full_name, obj.phone)
    client_info.short_description = 'Client'

    def status_badge(self, obj):
        colors = {
            'pending': '#FFA500', 'confirmed': '#3385FF', 'processing': '#9B59B6',
            'delivering': '#00D4FF', 'delivered': '#00FF88',
            'cancelled': '#FF3366', 'rejected': '#FF3366',
        }
        color = colors.get(obj.status, '#888')
        return format_html(
            '<span style="background:rgba({},0.15);color:{};padding:3px 10px;border-radius:20px;font-size:.75rem;font-weight:700;">{}</span>',
            ','.join(str(int(color.lstrip('#')[i:i+2], 16)) for i in (0,2,4)),
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Statut'

    def payment_badge(self, obj):
        icons = {'cash':'💵','waafi':'📱','cac':'📱','dmoney':'📱','saba':'📱'}
        icon = icons.get(obj.payment_method, '💳')
        return format_html('{} {}', icon, obj.get_payment_method_display())
    payment_badge.short_description = 'Paiement'

    def total_display(self, obj):
        return format_html('<strong style="color:#00D4FF;">{} FDJ</strong>', obj.total_price)
    total_display.short_description = 'Total'

    def actions_btn(self, obj):
        if obj.status == 'pending':
            confirm_url = f'/admin/store/order/{obj.pk}/change/'
            return format_html(
                '<a href="{}" style="background:#0066FF;color:#fff;padding:4px 10px;border-radius:6px;font-size:.78rem;text-decoration:none;">Traiter</a>',
                confirm_url
            )
        return '—'
    actions_btn.short_description = 'Action'

    def screenshot_preview(self, obj):
        if obj.transaction_screenshot:
            return format_html('<img src="{}" style="max-width:300px;border-radius:8px;">', obj.transaction_screenshot.url)
        return 'Aucune capture'
    screenshot_preview.short_description = 'Aperçu capture'

    @admin.action(description='✅ Confirmer les commandes sélectionnées')
    def confirmer_commandes(self, request, queryset):
        count = queryset.filter(status='pending').update(status='confirmed')
        self.message_user(request, f'{count} commande(s) confirmée(s).')

    @admin.action(description='❌ Rejeter les commandes sélectionnées')
    def rejeter_commandes(self, request, queryset):
        count = queryset.update(status='rejected')
        self.message_user(request, f'{count} commande(s) rejetée(s).')

    @admin.action(description='🚚 Marquer comme livrées')
    def marquer_livree(self, request, queryset):
        count = queryset.update(status='delivered')
        self.message_user(request, f'{count} commande(s) marquée(s) comme livrées.')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'wilaya']
    search_fields = ['user__username', 'user__email', 'phone']


# Étendre l'admin User pour afficher le profil inline
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profil'
    fields = ['phone', 'address', 'wilaya']


class ExtendedUserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined']

admin.site.unregister(User)
admin.site.register(User, ExtendedUserAdmin)
