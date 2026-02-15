from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.metrics import dp
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from models import Cart
import requests
import os
from threading import Thread

# Backend API URL - can be configured via environment variable
BACKEND_URL = os.getenv('SHOPPING_API_URL', 'http://192.168.1.100:5000')


class CatalogScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.products = []
        self.loading = False

    def on_enter(self):
        if not self.loading:
            self.load_products()

    def load_products(self):
        """Fetch products from API in background thread"""
        self.loading = True
        Thread(target=self._fetch_products, daemon=True).start()

    def _fetch_products(self):
        """Background thread to fetch products from API"""
        try:
            response = requests.get(f'{BACKEND_URL}/api/products', timeout=5)
            if response.status_code == 200:
                self.products = response.json()
                self.ids.products_container.clear_widgets()
                for p in self.products:
                    row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(80), spacing=10, padding=10)
                    info = BoxLayout(orientation='vertical')
                    info.add_widget(Label(text=p['name'], halign='left', valign='middle'))
                    price_text = f"${p['price']:.2f}"
                    if p.get('stock', 0) <= 0:
                        price_text += " (Out of Stock)"
                    info.add_widget(Label(text=price_text, halign='left', valign='middle'))
                    add_btn = Button(text='Add', size_hint_x=None, width=dp(100))
                    add_btn.disabled = p.get('stock', 0) <= 0
                    add_btn.bind(on_release=lambda btn, pid=p['id'], pname=p['name'], pprice=p['price']: 
                                 self.add_to_cart(pid, pname, pprice))
                    row.add_widget(info)
                    row.add_widget(add_btn)
                    self.ids.products_container.add_widget(row)
            else:
                self._show_error('Failed to load products')
        except requests.exceptions.RequestException as e:
            self._show_error(f'Connection error: {str(e)}\n\nMake sure backend is running at {BACKEND_URL}')
        finally:
            self.loading = False

    def add_to_cart(self, product_id, name, price):
        app = App.get_running_app()
        app.root.cart.add_product({'id': product_id, 'name': name, 'price': price})
        self.ids.cart_count.text = str(app.root.cart.total_items())

    def _show_error(self, message):
        popup = Popup(title='Error', content=Label(text=message), size_hint=(0.8, 0.4))
        popup.open()


class CartScreen(Screen):
    def on_enter(self):
        app = App.get_running_app()
        container = self.ids.cart_container
        container.clear_widgets()
        for item in app.root.cart.items:
            row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(48), spacing=10, padding=8)
            row.add_widget(Label(text=item['name']))
            row.add_widget(Label(text=f"x{item['qty']}"))
            row.add_widget(Label(text=f"${item['qty'] * item['price']:.2f}", size_hint_x=0.2))
            remove = Button(text='Remove', size_hint_x=None, width=dp(100))
            remove.bind(on_release=lambda btn, pid=item['id']: self.remove_item(pid))
            row.add_widget(remove)
            container.add_widget(row)
        self.ids.total_label.text = f"${app.root.cart.total_price():.2f}"

    def remove_item(self, product_id):
        app = App.get_running_app()
        app.root.cart.remove_product_by_id(product_id)
        self.on_enter()
        self.manager.get_screen('catalog').ids.cart_count.text = str(app.root.cart.total_items())


class MainScreenManager(ScreenManager):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cart = Cart()


class ShoppingApp(App):
    def build(self):
        Builder.load_file('shopping.kv')
        sm = MainScreenManager()
        return sm

    def checkout(self):
        app = App.get_running_app()
        total = app.root.cart.total_price()
        if total <= 0:
            popup = Popup(title='Empty Cart', content=Label(text='Your cart is empty!'), size_hint=(0.7, 0.3))
            popup.open()
            return
        
        app.root.cart.clear()
        self.root.get_screen('catalog').ids.cart_count.text = '0'
        self.root.get_screen('cart').ids.total_label.text = '$0.00'
        popup = Popup(title='Checkout', content=Label(text=f'Paid ${total:.2f}\n\nThank you!'), size_hint=(0.7, 0.3))
        popup.open()


if __name__ == '__main__':
    ShoppingApp().run()

