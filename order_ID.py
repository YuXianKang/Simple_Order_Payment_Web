class OrderIDGenerator:
    def __init__(self):
        self.counter = 1

    def generate_order_ID(self):
        order_id = self.counter
        self.counter += 1
        return order_id
