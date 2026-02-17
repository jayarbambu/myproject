import requests
import json
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.image import AsyncImage
from kivy.uix.button import Button
from kivy.clock import mainthread
from kivy.metrics import dp
from kivy.graphics import Color, RoundedRectangle
from threading import Thread

Builder.load_file("shopping.kv")

session = requests.Session()

# Global cart storage
cart = []

def save_cart():
    with open("cart.json", "w") as f:
        json.dump(cart, f)  # json.dump comes from the json module

class LoginScreen(Screen):
    def login(self):
        username = self.ids.username.text
        password = self.ids.password.text

        try:
            response = session.post(
                f"http://172.29.184.133:5000/api/login",
                json={"username": username, "password": password}
            )
            data = response.json()

            if response.status_code == 200 and data.get("status") == "success":
                self.ids.message.text = "✅ Login Successful"
                self.manager.current = "catalog"
            else:
                self.ids.message.text = f"❌ {data.get('message')}"

        except Exception as e:
            self.ids.message.text = f"❌ Error: {str(e)}"

class ProductCard(BoxLayout):
    def __init__(self, product, **kwargs):
        super().__init__(orientation='vertical', size_hint_y=None, height=dp(180), spacing=dp(5), padding=dp(10), **kwargs)
        self.product = product

        # Card background
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.rect = RoundedRectangle(radius=[dp(10)], pos=self.pos, size=self.size)
        self.bind(pos=self.update_rect, size=self.update_rect)

        # Top layout: Image + Details
        top_layout = BoxLayout(orientation='horizontal', spacing=dp(10))
        img_url = product.get("image", "")
        top_layout.add_widget(AsyncImage(source=img_url, size_hint_x=None, width=dp(100)) if img_url else Label(text="No Image", size_hint_x=None, width=dp(100)))

        details = BoxLayout(orientation='vertical', spacing=dp(5))
        details.add_widget(Label(text=product.get("name", "N/A"), bold=True, font_size=dp(16)))
        details.add_widget(Label(text=f"Price: ₱{product.get('price', 0)}", color=(1,0,0,1), font_size=dp(14)))
        top_layout.add_widget(details)
        self.add_widget(top_layout)

        # Rating stars
        rating = product.get("rating", 0)
        stars_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(20))
        for i in range(5):
            stars_layout.add_widget(Label(text="★" if i<rating else "☆", color=(1,0.8,0,1)))
        self.add_widget(stars_layout)

        # Add to Cart Button
        btn = Button(text="Add to Cart", size_hint_y=None, height=dp(40), background_color=(0,0.6,1,1))
        btn.bind(on_press=self.add_to_cart)
        self.add_widget(btn)

    def add_to_cart(self, instance):
        # Add product to cart or increase quantity
        for item in cart:
            if item["product"]["id"] == self.product["id"]:
                item["quantity"] += 1
                break
        else:
            cart.append({"product": self.product, "quantity": 1})
        print(f"Cart updated: {len(cart)} items")

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

class CatalogScreen(Screen):
    def on_enter(self):
        self.ids.products_container.clear_widgets()
        self.ids.products_container.add_widget(Label(text="Loading products...", size_hint_y=None, height=dp(40)))
        Thread(target=self._fetch_products).start()

    def _fetch_products(self):
        try:
            response = requests.get("http://172.29.184.133:5000/api/products")
            products = response.json()
        except Exception as e:
            print("Error fetching products:", e)
            products = []
        self.update_products(products)

    @mainthread
    def update_products(self, products):
        container = self.ids.products_container
        container.clear_widgets()
        if not products:
            container.add_widget(Label(text="No products found", size_hint_y=None, height=dp(40)))
            return
        for product in products:
            container.add_widget(ProductCard(product))

class CartScreen(Screen):
    def on_enter(self):
        self.ids.cart_container.clear_widgets()
        if not cart:
            self.ids.cart_container.add_widget(Label(text="Your cart is empty", size_hint_y=None, height=dp(40)))
            return

        total_price = 0
        for item in cart:
            box = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50), spacing=dp(10))
            box.add_widget(Label(text=item["product"]["name"], size_hint_x=0.5))
            box.add_widget(Label(text=f"₱{item['product']['price']}", size_hint_x=0.2))
            box.add_widget(Label(text=str(item["quantity"]), size_hint_x=0.1))
            remove_btn = Button(text="Remove", size_hint_x=0.2)
            remove_btn.bind(on_press=lambda x, i=item: self.remove_item(i))
            box.add_widget(remove_btn)
            self.ids.cart_container.add_widget(box)
            total_price += item["product"]["price"] * item["quantity"]

        self.ids.total_label.text = f"Total: ₱{total_price}"

    def remove_item(self, item):
        cart.remove(item)
        self.on_enter()  # Refresh cart screen

class CheckoutScreen(Screen):
    def on_enter(self):
        self.ids.checkout_container.clear_widgets()
        if not cart:
            self.ids.checkout_container.add_widget(Label(text="Cart is empty"))
            self.ids.total_label.text = "Total: ₱0"
            return

        total = 0
        for item in cart:
            box = BoxLayout(orientation="horizontal", size_hint_y=None, height=40)
            box.add_widget(Label(text=item["product"]["name"], size_hint_x=0.6))
            box.add_widget(Label(text=f"₱{item['product']['price']}", size_hint_x=0.2))
            box.add_widget(Label(text=str(item["quantity"]), size_hint_x=0.2))
            self.ids.checkout_container.add_widget(box)
            total += item["product"]["price"] * item["quantity"]

        self.ids.total_label.text = f"Total: ₱{total:.2f}"

    def place_order(self):
        if not cart:
            self.ids.confirm_label.text = "❌ Cart is empty!"
            return

        payload = {str(item["product"]["id"]): item["quantity"] for item in cart}

        try:
            response = session.post(
                f"http://172.29.184.133:5000/api/checkout",
                json={"cart": payload}
            )
            data = response.json()

            if response.status_code == 200 and data.get("status") == "success":
                self.ids.confirm_label.text = (
                    f"✅ Order Placed!\n"
                    f"Order ID: {data['order_id']}\n"
                    f"Total: ₱{data['total']:.2f}"
                )
                cart.clear()
                self.ids.checkout_container.clear_widgets()
                self.ids.total_label.text = "Total: ₱0"

            else:
                self.ids.confirm_label.text = f"❌ {data.get('message')}"

        except Exception as e:
            self.ids.confirm_label.text = f"❌ Error: {str(e)}"


class ShoppingApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(CatalogScreen(name="catalog"))
        sm.add_widget(CartScreen(name="cart"))
        sm.add_widget(CheckoutScreen(name="checkout"))
        return sm

if __name__ == "__main__":
    ShoppingApp().run()
