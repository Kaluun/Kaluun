from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import Order, Product, Category, ContactMessage, OrderItem, UserProfile, ORDER_STATUS_CHOICES
from .emails import notify_status_change


LOGIN_URL = '/comptes/connexion/'


# ══════════════════════════════════════════════════════════
#  DASHBOARD
# ══════════════════════════════════════════════════════════
@staff_member_required(login_url=LOGIN_URL)
def admin_dashboard(request):
    now = timezone.now()
    today = now.date()
    week_ago = now - timedelta(days=7)

    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    delivered_orders = Order.objects.filter(status='delivered').count()
    total_revenue = Order.objects.filter(
        status__in=['confirmed', 'processing', 'delivering', 'delivered']
    ).aggregate(t=Sum('total_price'))['t'] or 0
    total_users = User.objects.filter(is_staff=False).count()
    total_products = Product.objects.filter(is_available=True).count()
    orders_today = Order.objects.filter(created_at__date=today).count()
    revenue_today = Order.objects.filter(created_at__date=today).aggregate(t=Sum('total_price'))['t'] or 0
    orders_week = Order.objects.filter(created_at__gte=week_ago)

    recent_orders = Order.objects.select_related('user').prefetch_related('items').order_by('-created_at')[:12]

    top_products = OrderItem.objects.values('product_name').annotate(
        total_qty=Sum('quantity'), total_orders=Count('order', distinct=True)
    ).order_by('-total_orders')[:5]

    status_data = []
    total_o = total_orders or 1
    for status, label, color in [
        ('pending', 'En attente', '#FFD166'),
        ('confirmed', 'Confirmées', '#3D8EFF'),
        ('processing', 'Préparation', '#9B59B6'),
        ('delivering', 'Livraison', '#00CFFF'),
        ('delivered', 'Livrées', '#00E676'),
        ('cancelled', 'Annulées', '#FF4757'),
        ('rejected', 'Rejetées', '#FF4757'),
    ]:
        count = Order.objects.filter(status=status).count()
        pct = round(count / total_o * 100, 1)
        status_data.append({'status': status, 'label': label, 'color': color, 'count': count, 'pct': pct})

    return render(request, 'admin_panel/dashboard.html', {
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'delivered_orders': delivered_orders,
        'total_revenue': total_revenue,
        'total_users': total_users,
        'total_products': total_products,
        'orders_today': orders_today,
        'revenue_today': revenue_today,
        'revenue_week': revenue_today,
        'orders_week_count': orders_week.count(),
        'recent_orders': recent_orders,
        'top_products': top_products,
        'status_data': status_data,
        'status_choices': ORDER_STATUS_CHOICES,
    })


# ══════════════════════════════════════════════════════════
#  COMMANDES
# ══════════════════════════════════════════════════════════
@staff_member_required(login_url=LOGIN_URL)
def admin_orders(request):
    status_filter = request.GET.get('status', '')
    search = request.GET.get('q', '')
    orders = Order.objects.select_related('user').prefetch_related('items').order_by('-created_at')
    if status_filter:
        orders = orders.filter(status=status_filter)
    if search:
        orders = orders.filter(Q(full_name__icontains=search) | Q(phone__icontains=search) | Q(pk__icontains=search))
    return render(request, 'admin_panel/orders.html', {
        'orders': orders,
        'status_filter': status_filter,
        'search': search,
        'status_choices': ORDER_STATUS_CHOICES,
        'pending_count': Order.objects.filter(status='pending').count(),
    })


@staff_member_required(login_url=LOGIN_URL)
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    return render(request, 'admin_panel/order_detail.html', {'order': order, 'status_choices': ORDER_STATUS_CHOICES})


@staff_member_required(login_url=LOGIN_URL)
def order_validate(request, pk):
    order = get_object_or_404(Order, pk=pk)
    note = request.POST.get('admin_note', '')
    order.status = 'confirmed'
    if note: order.admin_note = note
    order.save()
    notify_status_change(order, 'confirmed')   # ← email client
    messages.success(request, f'Commande #{pk} confirmée ✅ — client notifié par email.')
    return redirect(request.META.get('HTTP_REFERER', 'gestadmin:orders'))


@staff_member_required(login_url=LOGIN_URL)
def order_reject(request, pk):
    order = get_object_or_404(Order, pk=pk)
    note = request.POST.get('admin_note', '')
    order.status = 'rejected'
    if note: order.admin_note = note
    order.save()
    notify_status_change(order, 'rejected')    # ← email client
    messages.warning(request, f'Commande #{pk} rejetée — client notifié par email.')
    return redirect(request.META.get('HTTP_REFERER', 'gestadmin:orders'))


@staff_member_required(login_url=LOGIN_URL)
def order_set_status(request, pk):
    order = get_object_or_404(Order, pk=pk)
    new_status = request.POST.get('status')
    note = request.POST.get('admin_note', '')
    if new_status:
        order.status = new_status
    if note:
        order.admin_note = note
    order.save()
    if new_status:
        notify_status_change(order, new_status)   # ← email client selon statut
    messages.success(request, f'Commande #{pk} → {new_status} — client notifié.')
    return redirect(request.META.get('HTTP_REFERER', 'gestadmin:orders'))


# ══════════════════════════════════════════════════════════
#  PRODUITS — CRUD COMPLET
# ══════════════════════════════════════════════════════════
@staff_member_required(login_url=LOGIN_URL)
def admin_products(request):
    products = Product.objects.select_related('category').order_by('-is_featured', 'name')
    categories = Category.objects.all()
    return render(request, 'admin_panel/products.html', {
        'products': products,
        'categories': categories,
        'pending_orders_count': Order.objects.filter(status='pending').count(),
    })


@staff_member_required(login_url=LOGIN_URL)
def product_add(request):
    categories = Category.objects.all()
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, 'Le nom du produit est requis.')
        else:
            from django.utils.text import slugify
            slug = slugify(name)
            # Slug unique
            base_slug = slug
            n = 1
            while Product.objects.filter(slug=slug).exists():
                slug = f'{base_slug}-{n}'; n += 1

            product = Product(
                name=name, slug=slug,
                category_id=request.POST.get('category') or None,
                description=request.POST.get('description', ''),
                price=request.POST.get('price') or 0,
                stock=request.POST.get('stock') or 50,
                unit=request.POST.get('unit', 'kg'),
                origin=request.POST.get('origin', 'Djibouti'),
                season=request.POST.get('season', ''),
                image_url=request.POST.get('image_url', ''),
                nutritional_info=request.POST.get('nutritional_info', ''),
                is_featured='is_featured' in request.POST,
                is_available=True,
            )
            if 'image' in request.FILES:
                product.image = request.FILES['image']
            product.save()
            messages.success(request, f'Produit "{name}" créé avec succès !')
            return redirect('gestadmin:products')

    return render(request, 'admin_panel/product_form.html', {
        'categories': categories,
        'action': 'Ajouter',
        'product': None,
        'pending_orders_count': Order.objects.filter(status='pending').count(),
    })


@staff_member_required(login_url=LOGIN_URL)
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    categories = Category.objects.all()
    if request.method == 'POST':
        product.name = request.POST.get('name', product.name).strip()
        product.category_id = request.POST.get('category') or None
        product.description = request.POST.get('description', '')
        product.price = request.POST.get('price') or product.price
        product.stock = request.POST.get('stock') or product.stock
        product.unit = request.POST.get('unit', product.unit)
        product.origin = request.POST.get('origin', product.origin)
        product.season = request.POST.get('season', '')
        product.image_url = request.POST.get('image_url', product.image_url)
        product.nutritional_info = request.POST.get('nutritional_info', '')
        product.is_featured = 'is_featured' in request.POST
        product.is_available = 'is_available' in request.POST
        if 'image' in request.FILES:
            product.image = request.FILES['image']
        product.save()
        messages.success(request, f'Produit "{product.name}" modifié avec succès !')
        return redirect('gestadmin:products')

    return render(request, 'admin_panel/product_form.html', {
        'product': product,
        'categories': categories,
        'action': 'Modifier',
        'pending_orders_count': Order.objects.filter(status='pending').count(),
    })


@staff_member_required(login_url=LOGIN_URL)
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    name = product.name
    product.delete()
    messages.success(request, f'Produit "{name}" supprimé.')
    return redirect('gestadmin:products')


@staff_member_required(login_url=LOGIN_URL)
def product_toggle(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.is_available = not product.is_available
    product.save()
    status = 'activé' if product.is_available else 'désactivé'
    messages.success(request, f'"{product.name}" {status}.')
    return redirect(request.META.get('HTTP_REFERER', 'gestadmin:products'))


# ══════════════════════════════════════════════════════════
#  UTILISATEURS — CRUD COMPLET
# ══════════════════════════════════════════════════════════
@staff_member_required(login_url=LOGIN_URL)
def admin_users(request):
    users = User.objects.filter(is_superuser=False).select_related('profile').annotate(
        total_spent=Sum('orders__total_price'),
        order_count=Count('orders'),
    ).order_by('-date_joined')
    return render(request, 'admin_panel/users.html', {
        'users': users,
        'pending_orders_count': Order.objects.filter(status='pending').count(),
    })


@staff_member_required(login_url=LOGIN_URL)
def user_edit(request, pk):
    user = get_object_or_404(User, pk=pk)
    profile, _ = UserProfile.objects.get_or_create(user=user)
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', user.first_name).strip()
        user.last_name = request.POST.get('last_name', user.last_name).strip()
        user.email = request.POST.get('email', user.email).strip()
        user.is_active = 'is_active' in request.POST
        new_pw = request.POST.get('password', '').strip()
        if new_pw:
            user.set_password(new_pw)
        user.save()
        profile.phone = request.POST.get('phone', profile.phone).strip()
        profile.wilaya = request.POST.get('wilaya', profile.wilaya).strip()
        profile.address = request.POST.get('address', profile.address).strip()
        profile.save()
        messages.success(request, f'Utilisateur "{user.username}" modifié.')
        return redirect('gestadmin:users')
    user_orders = Order.objects.filter(user=user).order_by('-created_at')
    total_spent = user_orders.aggregate(t=Sum('total_price'))['t'] or 0
    return render(request, 'admin_panel/user_form.html', {
        'u': user, 'profile': profile,
        'orders': user_orders,
        'total_spent': total_spent,
        'pending_orders_count': Order.objects.filter(status='pending').count(),
    })


@staff_member_required(login_url=LOGIN_URL)
def user_toggle(request, pk):
    user = get_object_or_404(User, pk=pk)
    user.is_active = not user.is_active
    user.save()
    status = 'activé' if user.is_active else 'bloqué'
    messages.success(request, f'Compte de {user.username} {status}.')
    return redirect(request.META.get('HTTP_REFERER', 'gestadmin:users'))


@staff_member_required(login_url=LOGIN_URL)
def user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    name = user.username
    user.delete()
    messages.success(request, f'Utilisateur "{name}" supprimé.')
    return redirect('gestadmin:users')
