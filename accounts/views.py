from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from .forms import RegisterForm, LoginForm
from store.models import Order, UserProfile, Product


def register(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    form = RegisterForm()
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.get_or_create(user=user)
            login(request, user)
            messages.success(request, f'Bienvenue {user.first_name or user.username} ! Votre compte est créé.')
            return redirect('accounts:dashboard')
    return render(request, 'accounts/register.html', {'form': form})


def user_login(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    form = LoginForm()
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Bienvenue {user.first_name or user.username} !')
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('accounts:dashboard')
    return render(request, 'accounts/login.html', {'form': form})


def user_logout(request):
    logout(request)
    messages.info(request, 'Vous avez été déconnecté.')
    return redirect('store:home')


@login_required
def dashboard(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    total_spent = orders.aggregate(t=Sum('total_price'))['t'] or 0
    pending_count = orders.filter(status='pending').count()
    delivered_count = orders.filter(status='delivered').count()
    last_order = orders.first()

    # Dernières commandes (5)
    recent_orders = orders[:5]

    # Produits phares
    featured_products = Product.objects.filter(is_featured=True, is_available=True)[:4]

    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    ctx = {
        'orders': orders,
        'recent_orders': recent_orders,
        'total_spent': total_spent,
        'total_orders': orders.count(),
        'pending_count': pending_count,
        'delivered_count': delivered_count,
        'last_order': last_order,
        'featured_products': featured_products,
        'profile': profile,
    }
    return render(request, 'accounts/dashboard.html', ctx)


@login_required
def profile(request):
    # Redirige vers le dashboard complet
    return redirect('accounts:dashboard')


@login_required
def profile_edit(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.save()
        profile.phone = request.POST.get('phone', profile.phone)
        profile.wilaya = request.POST.get('wilaya', profile.wilaya)
        profile.address = request.POST.get('address', profile.address)
        profile.save()
        messages.success(request, 'Profil mis à jour avec succès !')
        return redirect('accounts:dashboard')
    return render(request, 'accounts/profile_edit.html', {'profile': profile})
