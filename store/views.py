from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q
from .models import Product, Category, HeroSlide, Testimonial, Order, OrderItem, UserProfile, Notification
from .forms import ContactForm, NewsletterForm, CheckoutForm
from .notifications import push_new_order
from blog.models import Post


def robots_txt(request):
    sitemap_url = request.build_absolute_uri('/sitemap.xml')
    return render(request, 'robots.txt', {'sitemap_url': sitemap_url}, content_type='text/plain')


def home(request):
    slides = HeroSlide.objects.filter(is_active=True)
    featured_products = Product.objects.filter(is_featured=True, is_available=True)[:6]
    testimonials = Testimonial.objects.filter(is_active=True)[:3]
    recent_posts = Post.objects.filter(is_published=True).order_by('-published_at')[:3]
    categories = Category.objects.all()
    newsletter_form = NewsletterForm()

    if request.method == 'POST' and 'newsletter' in request.POST:
        newsletter_form = NewsletterForm(request.POST)
        if newsletter_form.is_valid():
            try:
                newsletter_form.save()
                messages.success(request, 'Merci pour votre inscription à notre newsletter !')
            except Exception:
                messages.info(request, 'Vous êtes déjà inscrit à notre newsletter.')
            return redirect('store:home')

    features_bar = [
        {'icon': 'fas fa-truck', 'title': 'Livraison 24h', 'sub': 'Dans tout Djibouti'},
        {'icon': 'fas fa-snowflake', 'title': 'Chaîne du froid', 'sub': 'Conservation optimale'},
        {'icon': 'fas fa-leaf', 'title': '100% Naturel', 'sub': 'Sans additifs'},
        {'icon': 'fas fa-shield-alt', 'title': 'Qualité garantie', 'sub': 'Contrôle strict'},
    ]
    return render(request, 'home.html', {
        'slides': slides,
        'featured_products': featured_products,
        'testimonials': testimonials,
        'recent_posts': recent_posts,
        'categories': categories,
        'newsletter_form': newsletter_form,
        'features_bar': features_bar,
    })


def about(request):
    stats = [
        {'num': '100%', 'lbl': 'Frais & Local'},
        {'num': '97%', 'lbl': 'Satisfaction'},
        {'num': '15+', 'lbl': 'Espèces'},
        {'num': '24h', 'lbl': 'Livraison'},
    ]
    values = [
        {'icon': 'fas fa-heart', 'title': 'Passion', 'text': 'Chaque produit est sélectionné avec soin pour vous offrir le meilleur de la mer.'},
        {'icon': 'fas fa-handshake', 'title': 'Confiance', 'text': 'Transparence et qualité irréprochable. Vous savez exactement d\'où vient votre poisson.'},
        {'icon': 'fas fa-globe', 'title': 'Durabilité', 'text': 'Partenariat avec des pêcheurs responsables pour préserver l\'écosystème marin.'},
        {'icon': 'fas fa-bolt', 'title': 'Innovation', 'text': 'La première plateforme digitale de commande de poissons frais à Djibouti.'},
    ]
    return render(request, 'about.html', {'stats': stats, 'values': values})


def contact(request):
    form = ContactForm()
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Votre message a été envoyé avec succès. Nous vous répondrons sous 24h.')
            return redirect('store:contact')
    return render(request, 'contact.html', {'form': form})


def product_list(request):
    products = Product.objects.filter(is_available=True)
    categories = Category.objects.all()
    selected_category = None

    category_slug = request.GET.get('categorie')
    search_query = request.GET.get('q', '')

    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=selected_category)

    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | Q(description__icontains=search_query)
        )

    return render(request, 'store/products.html', {
        'products': products,
        'categories': categories,
        'selected_category': selected_category,
        'search_query': search_query,
    })


def products_by_category(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(category=category, is_available=True)
    categories = Category.objects.all()
    return render(request, 'store/products.html', {
        'products': products,
        'categories': categories,
        'selected_category': category,
        'search_query': '',
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_available=True)
    related_products = Product.objects.filter(
        category=product.category, is_available=True
    ).exclude(pk=product.pk)[:4]
    return render(request, 'store/product_detail.html', {
        'product': product,
        'related_products': related_products,
    })


# ──── Panier ────────────────────────────────────────────────────────────────

def cart_json(request):
    """Retourne les données du panier en JSON pour mise à jour AJAX du panel."""
    cart = request.session.get('cart', {})
    items = []
    for product_id, item in cart.items():
        items.append({
            'id': product_id,
            'name': item['name'],
            'price': item['price'],
            'quantity': item['quantity'],
            'subtotal': item['price'] * item['quantity'],
            'image': item.get('image', ''),
            'unit': item.get('unit', 'kg'),
        })
    total = sum(i['subtotal'] for i in items)
    count = sum(i['quantity'] for i in items)
    return JsonResponse({'items': items, 'total': int(total), 'count': count})


def cart_detail(request):
    cart = request.session.get('cart', {})
    cart_items = []
    for product_id, item in cart.items():
        cart_items.append({
            'id': product_id,
            'name': item['name'],
            'price': item['price'],
            'quantity': item['quantity'],
            'subtotal': item['price'] * item['quantity'],
            'image': item.get('image', ''),
        })
    total = sum(i['subtotal'] for i in cart_items)
    return render(request, 'store/cart.html', {'cart_items': cart_items, 'total': total})


@require_POST
def cart_add(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_available=True)
    cart = request.session.get('cart', {})
    key = str(product_id)
    quantity = int(request.POST.get('quantity', 1))

    if key in cart:
        cart[key]['quantity'] += quantity
    else:
        img = ''
        if product.image:
            img = product.image.url
        elif product.image_url:
            img = product.image_url
        cart[key] = {
            'name': product.name,
            'price': float(product.price),
            'quantity': quantity,
            'unit': product.unit,
            'image': img,
        }

    request.session['cart'] = cart
    cart_count = sum(i['quantity'] for i in cart.values())
    cart_total = sum(i['price'] * i['quantity'] for i in cart.values())

    # Toujours répondre JSON (AJAX obligatoire)
    return JsonResponse({
        'success': True,
        'product_name': product.name,
        'cart_count': cart_count,
        'cart_total': int(cart_total),
    })


@require_POST
def cart_remove(request, product_id):
    cart = request.session.get('cart', {})
    cart.pop(str(product_id), None)
    request.session['cart'] = cart
    messages.success(request, 'Article retiré du panier.')
    return redirect('store:cart_detail')


@require_POST
def cart_update(request, product_id):
    cart = request.session.get('cart', {})
    key = str(product_id)
    quantity = int(request.POST.get('quantity', 1))
    if key in cart:
        if quantity > 0:
            cart[key]['quantity'] = quantity
        else:
            cart.pop(key, None)
    request.session['cart'] = cart
    return redirect('store:cart_detail')


def cart_clear(request):
    request.session['cart'] = {}
    messages.info(request, 'Votre panier a été vidé.')
    return redirect('store:cart_detail')


# ──── Commande ───────────────────────────────────────────────────────────────

@login_required
def checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.warning(request, 'Votre panier est vide.')
        return redirect('store:product_list')

    cart_items = []
    total = 0
    for product_id, item in cart.items():
        subtotal = item['price'] * item['quantity']
        total += subtotal
        cart_items.append({
            'id': product_id,
            'name': item['name'],
            'price': item['price'],
            'quantity': item['quantity'],
            'unit': item.get('unit', 'kg'),
            'subtotal': subtotal,
        })

    # Pré-remplissage depuis profil
    profile = getattr(request.user, 'profile', None)
    initial = {
        'full_name': request.user.get_full_name() or request.user.username,
        'email': request.user.email,
        'phone': profile.phone if profile else '',
        'delivery_address': profile.address if profile else '',
        'wilaya': profile.wilaya if profile else '',
    }
    form = CheckoutForm(initial=initial)

    wallets = [
        {'key': 'waafi',  'name': 'Waafi',   'img': 'waafi.webp'},
        {'key': 'cac',    'name': 'CAC',      'img': 'cac.webp'},
        {'key': 'dmoney', 'name': 'D-Money',  'img': 'd-money.webp'},
        {'key': 'saba',   'name': 'Saba',     'img': 'saba.webp'},
    ]

    if request.method == 'POST':
        # Récupérer tous les champs directement depuis POST (plus fiable que le form)
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        delivery_address = request.POST.get('delivery_address', '').strip()
        wilaya = request.POST.get('wilaya', '').strip()
        notes = request.POST.get('notes', '').strip()
        payment_method = request.POST.get('payment_method', 'cash')
        transaction_ref = request.POST.get('transaction_ref', '').strip()

        # Validation basique
        errors = []
        if not full_name: errors.append('Nom complet requis.')
        if not phone: errors.append('Téléphone requis.')
        if not delivery_address: errors.append('Adresse de livraison requise.')

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            order = Order(
                user=request.user,
                full_name=full_name,
                email=email,
                phone=phone,
                delivery_address=delivery_address,
                wilaya=wilaya,
                notes=notes,
                payment_method=payment_method,
                transaction_ref=transaction_ref,
                total_price=total,
                cgv_accepted=True,
                status='pending',
            )
            if 'transaction_screenshot' in request.FILES:
                order.transaction_screenshot = request.FILES['transaction_screenshot']
            order.save()

            for product_id, item in cart.items():
                try:
                    product = Product.objects.get(pk=int(product_id))
                except Product.DoesNotExist:
                    product = None
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    product_name=item['name'],
                    price=item['price'],
                    quantity=item['quantity'],
                    unit=item.get('unit', 'kg'),
                )

            request.session['cart'] = {}

            # Notifications dashboard — admin (plus rapide que l'email)
            push_new_order(order)

            messages.success(request, f'Commande #{order.pk} confirmée ! Notre équipe vous contactera rapidement.')
            return redirect('store:order_confirmation', pk=order.pk)

    return render(request, 'store/checkout.html', {
        'form': form,
        'cart_items': cart_items,
        'total': total,
        'wallets': wallets,
    })


@login_required
def order_confirmation(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    return render(request, 'store/order_confirmation.html', {'order': order})


@login_required
def notification_read(request, pk):
    notif = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notif.is_read = True
    notif.save(update_fields=['is_read'])
    return redirect(notif.link or 'store:home')


@login_required
@require_POST
def notifications_read_all(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return redirect(request.META.get('HTTP_REFERER', 'store:home'))
