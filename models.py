class Cart:
    def __init__(self):
        self.items = []

    def add_product(self, product):
        for it in self.items:
            if it['id'] == product['id']:
                it['qty'] += 1
                return
        self.items.append({'id': product['id'], 'name': product['name'], 'price': product['price'], 'qty': 1})

    def add_product_by_id(self, product_id):
        p = next((x for x in sample_products if x['id'] == product_id), None)
        if p:
            self.add_product(p)

    def remove_product_by_id(self, product_id):
        self.items = [it for it in self.items if it['id'] != product_id]

    def total_items(self):
        return sum(it['qty'] for it in self.items)

    def total_price(self):
        return sum(it['qty'] * it['price'] for it in self.items)

    def clear(self):
        self.items = []


sample_products = [
    {'id': 1, 'name': 'T-Shirt', 'price': 19.99},
    {'id': 2, 'name': 'Jeans', 'price': 49.99},
    {'id': 3, 'name': 'Sneakers', 'price': 79.99},
    {'id': 4, 'name': 'Hat', 'price': 14.99},
    {'id': 5, 'name': 'Sunglasses', 'price': 29.99},
]
