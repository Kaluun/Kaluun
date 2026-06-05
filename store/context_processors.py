def cart_count(request):
    cart = request.session.get('cart', {})
    count = sum(item['quantity'] for item in cart.values())
    total = sum(item['price'] * item['quantity'] for item in cart.values())
    cart_items_list = [
        {
            'id': k,
            'name': v['name'],
            'price': v['price'],
            'quantity': v['quantity'],
            'subtotal': v['price'] * v['quantity'],
            'image': v.get('image', ''),
        }
        for k, v in cart.items()
    ]
    return {
        'cart_count': count,
        'cart_total': total,
        'cart_items_list': cart_items_list,
    }
