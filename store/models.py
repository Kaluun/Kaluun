from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nom")
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    icon = models.CharField(max_length=50, default='fas fa-fish', verbose_name="Icône Font Awesome")

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('store:products_by_category', kwargs={'slug': self.slug})


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='products', verbose_name="Catégorie")
    name = models.CharField(max_length=200, verbose_name="Nom")
    slug = models.SlugField(unique=True, blank=True, max_length=250)
    description = models.TextField(blank=True, verbose_name="Description")
    price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Prix (FDJ)")
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name="Image")
    image_url = models.URLField(blank=True, null=True, verbose_name="URL image externe")
    stock = models.PositiveIntegerField(default=50, verbose_name="Stock (kg)")
    unit = models.CharField(max_length=20, default='kg', verbose_name="Unité")
    min_order = models.DecimalField(max_digits=5, decimal_places=1, default=0.5, verbose_name="Commande min (kg)")
    is_featured = models.BooleanField(default=False, verbose_name="Produit phare")
    is_available = models.BooleanField(default=True, verbose_name="Disponible")
    origin = models.CharField(max_length=100, default='Djibouti', verbose_name="Origine")
    season = models.CharField(max_length=100, blank=True, verbose_name="Saison")
    nutritional_info = models.TextField(blank=True, verbose_name="Info nutritionnelles")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Produit"
        verbose_name_plural = "Produits"
        ordering = ['-is_featured', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('store:product_detail', kwargs={'slug': self.slug})

    def get_image_url(self):
        if self.image:
            return self.image.url
        if self.image_url:
            return self.image_url
        return None


class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', verbose_name="Destinataire")
    title = models.CharField(max_length=200, verbose_name="Titre")
    message = models.CharField(max_length=300, blank=True, verbose_name="Message")
    link = models.CharField(max_length=300, blank=True, verbose_name="Lien")
    icon = models.CharField(max_length=40, default='fa-bell', verbose_name="Icône")
    is_read = models.BooleanField(default=False, verbose_name="Lu")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} → {self.recipient}"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    address = models.TextField(blank=True, verbose_name="Adresse")
    wilaya = models.CharField(max_length=100, blank=True, verbose_name="Quartier/Zone")

    class Meta:
        verbose_name = "Profil utilisateur"
        verbose_name_plural = "Profils utilisateurs"

    def __str__(self):
        return f"Profil de {self.user.username}"


class HeroSlide(models.Model):
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True)
    image = models.ImageField(upload_to='slides/', blank=True, null=True)
    cta_text = models.CharField(max_length=50, default='Découvrir')
    cta_url = models.CharField(max_length=200, default='/produits/')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Slide Hero"
        verbose_name_plural = "Slides Hero"
        ordering = ['order']

    def __str__(self):
        return self.title


class Testimonial(models.Model):
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=100)
    content = models.TextField()
    photo = models.ImageField(upload_to='testimonials/', blank=True, null=True)
    rating = models.PositiveIntegerField(default=5, choices=[(i, i) for i in range(1, 6)])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Témoignage"
        verbose_name_plural = "Témoignages"

    def __str__(self):
        return f"{self.name} - {self.role}"


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Abonné Newsletter"
        verbose_name_plural = "Abonnés Newsletter"

    def __str__(self):
        return self.email


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Message Contact"
        verbose_name_plural = "Messages Contact"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.subject}"


PAYMENT_CHOICES = [
    ('cash', 'Paiement à la livraison (Cash)'),
    ('waafi', 'Waafi Mobile'),
    ('cac', 'CAC Mobile'),
    ('dmoney', 'D-Money'),
    ('saba', 'Saba Mobile'),
]

ORDER_STATUS_CHOICES = [
    ('pending', 'En attente'),
    ('confirmed', 'Confirmée'),
    ('processing', 'En préparation'),
    ('delivering', 'En livraison'),
    ('delivered', 'Livrée'),
    ('cancelled', 'Annulée'),
    ('rejected', 'Rejetée'),
]


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='orders', verbose_name="Client")
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES,
                               default='pending', verbose_name="Statut")
    full_name = models.CharField(max_length=200, verbose_name="Nom complet")
    email = models.EmailField(blank=True, verbose_name="Email")
    phone = models.CharField(max_length=20, verbose_name="Téléphone")
    delivery_address = models.TextField(verbose_name="Adresse de livraison")
    wilaya = models.CharField(max_length=100, blank=True, verbose_name="Quartier/Zone")
    notes = models.TextField(blank=True, verbose_name="Notes")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES,
                                       default='cash', verbose_name="Mode de paiement")
    transaction_screenshot = models.ImageField(upload_to='transactions/',
                                                blank=True, null=True,
                                                verbose_name="Capture de transaction")
    transaction_ref = models.CharField(max_length=100, blank=True,
                                        verbose_name="Référence transaction")
    total_price = models.DecimalField(max_digits=12, decimal_places=0,
                                       default=0, verbose_name="Total (FDJ)")
    admin_note = models.TextField(blank=True, verbose_name="Note admin")
    cgv_accepted = models.BooleanField(default=False, verbose_name="CGV acceptées")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"
        ordering = ['-created_at']

    def __str__(self):
        return f"Commande #{self.pk} — {self.full_name}"

    def get_payment_display_icon(self):
        icons = {
            'cash': 'fas fa-money-bill-wave',
            'waafi': 'fas fa-mobile-alt',
            'cac': 'fas fa-mobile-alt',
            'dmoney': 'fas fa-mobile-alt',
            'saba': 'fas fa-mobile-alt',
        }
        return icons.get(self.payment_method, 'fas fa-credit-card')

    def compute_total(self):
        total = sum(item.subtotal() for item in self.items.all())
        self.total_price = total
        self.save(update_fields=['total_price'])


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE,
                               related_name='items', verbose_name="Commande")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL,
                                  null=True, verbose_name="Produit")
    product_name = models.CharField(max_length=200, verbose_name="Nom produit")
    price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Prix")
    quantity = models.DecimalField(max_digits=6, decimal_places=1,
                                    default=1, verbose_name="Quantité (kg)")
    unit = models.CharField(max_length=20, default='kg')

    class Meta:
        verbose_name = "Article"
        verbose_name_plural = "Articles"

    def __str__(self):
        return f"{self.quantity}{self.unit} × {self.product_name}"

    def subtotal(self):
        return int(self.price * self.quantity)
