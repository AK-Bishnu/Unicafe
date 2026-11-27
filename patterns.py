
# CREATIONAL PATTERN: FACTORY

class Food:
    def __init__(self, food_id, name, price, stock, category):
        self.id = food_id
        self.name = name
        self.price = price
        self.stock = stock
        self.category = category

    def to_tuple(self):
        return (self.id, self.name, self.price, self.stock, self.category)


class FoodFactory:
    @staticmethod
    def create_food(food_id, name, price, stock, category):
        return Food(food_id, name, price, stock, category)


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
    def __init__(self, checkout_operation):
        self.checkout_operation = checkout_operation

    def checkout(self):
        return self.checkout_operation()
