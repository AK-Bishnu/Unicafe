
# CREATIONAL PATTERN: FACTORY

class Food:
    def __init__(self, name, price, category):
        self.name = name
        self.price = price
        self.category = category


class FoodFactory:
    @staticmethod
    def create_food(name, price, category):
        return Food(name, price, category)



# BEHAVIORAL PATTERN: STRATEGY

class DiscountStrategy:
    def calculate(self, subtotal, item_count):
        raise NotImplementedError


class NoDiscount(DiscountStrategy):
    def calculate(self, subtotal, item_count):
        return 0


class ComboDiscount(DiscountStrategy):
    def calculate(self, subtotal, item_count):
        return subtotal * 0.10 if item_count >= 3 else 0



# STRUCTURAL PATTERN: FACADE

class CheckoutFacade:
    def __init__(self, cart, inventory, payment):
        self.cart = cart
        self.inventory = inventory
        self.payment = payment

    def checkout(self):
        if not self.cart:
            return "Cart is empty"

        if not self.inventory.check(self.cart):
            return "Insufficient stock"

        if not self.payment.pay(self.cart):
            return "Payment failed"

        self.inventory.update(self.cart)
        return "Checkout successful"

