# Import necessary modules from Flask, Forms, and other custom modules
from flask import Flask, render_template, request, redirect, url_for, flash
import shelve
import uuid
import payment_storage
from Forms import payment, collection_type
from products import food, coffee, non_coffee

# Create a Flask application instance
app = Flask(__name__)
app.secret_key = 'CafeCrest_Wonder'

# Combine product dictionaries into a single dictionary
all_products = {
    **food,
    **coffee,
    **non_coffee
}


# Define a route for the home page
@app.route('/')
def home():
    return render_template('home.html')


# Define a route for handling payment details form
@app.route('/payment_details', methods=['GET', 'POST'])
def create_payment():
    # Create an instance of the payment form
    Payment = payment(request.form)

    # Check if the form is submitted and valid
    if request.method == 'POST' and Payment.validate():
        payment_storage_dict = {}

        # Open the shelves database for payment storage
        db = shelve.open('payment.db', 'c')
        try:
            # Retrieve existing payment details from the database
            payment_storage_dict = db['payment']
        except Exception as e:
            app.logger.error(f"Error in retrieving Payment from payment.db: {str(e)}")
            flash("An error occurred while processing your request. Please try again later.", "error")
            return redirect(url_for('home'))

        # Create a payment object with form data
        Payment = payment_storage.payment_details(Payment.card_number.data, Payment.expiration_date.data,
                                                  Payment.cvv.data, Payment.card_name.data)
        # Store payment details in the database
        payment_storage_dict[Payment.get_payment_details_id()] = Payment
        db['payment'] = payment_storage_dict
        db.close()

        # Redirect to the payment retrieval page
        return redirect(url_for('retrieve_payment'))

    # Render the payment details form
    return render_template('payment_details.html', form=Payment)


# Define a route for retrieving payment details
@app.route('/retrieve_payment')
def retrieve_payment():
    # Open the shelves database for payment retrieval
    db = shelve.open('payment.db', 'r')
    payment_storage_dict = db['payment']
    db.close()

    # Create a list of payment details for rendering
    payment_details_list = []
    for key in payment_storage_dict:
        Payment = payment_storage_dict.get(key)
        payment_details_list.append(Payment)

    # Render the payment details retrieval page
    return render_template('view_payment_details.html', count=len(payment_details_list), payment_details_list=payment_details_list)


# Define a route for updating payment details
@app.route('/update_payment/<int:id>/', methods=['POST', 'GET'])
def update_payment(id):
    # Create an instance of the payment form for updating
    update_payment_details = payment(request.form)

    # Check if the form is submitted and valid
    if request.method == 'POST' and update_payment_details.validate():
        try:
            # Open the shelves database for payment update
            db = shelve.open('payment.db', 'w')
            payment_storage_dict = db['payment']

            # Retrieve existing payment details from the database
            Payment = payment_storage_dict.get(id)

            # Update payment details with form data
            Payment.set_card_number(update_payment_details.card_number.data)
            Payment.set_expiration_date(update_payment_details.expiration_date.data)
            Payment.set_cvv(update_payment_details.cvv.data)
            Payment.set_card_name(update_payment_details.card_name.data)
            db['payment'] = payment_storage_dict
            db.close()

            flash("Payment details updated successfully", "success")
            return redirect(url_for('retrieve_payment'))
        except Exception as e:
            app.logger.error(f"Error in adding product to cart: {str(e)}")
            flash("An error occurred while adding the product to your cart. Please try again later.", "error")
            return redirect(url_for('home'))

    else:
        try:
            # Open the shelves database for payment retrieval
            db = shelve.open('payment.db', 'r')
            payment_storage_dict = db['payment']
            db.close()
        except Exception as e:
            app.logger.error(f"Error in adding product to cart: {str(e)}")
            flash("An error occurred while adding the product to your cart. Please try again later.", "error")
            return redirect(url_for('home'))

        # Retrieve existing payment details for pre-filling the form
        Payment = payment_storage_dict.get(id)
        update_payment_details.card_number.data = Payment.get_card_number()
        update_payment_details.expiration_date.data = Payment.get_expiration_date()
        update_payment_details.cvv.data = Payment.get_cvv()
        update_payment_details.card_name.data = Payment.get_card_name()

    # Render the payment details update form
    return render_template('update_payment_details.html', form=update_payment_details)


# Define a route for deleting payment details
@app.route('/delete_payment/<int:id>', methods=['POST'])
def delete_payment(id):
    try:
        # Open the shelves database for payment deletion
        db = shelve.open('payment.db', 'w')
        payment_storage_dict = db['payment']

        # Remove payment details based on ID
        payment_storage_dict.pop(id)

        db['payment'] = payment_storage_dict
        db.close()

        flash("Payment details deleted successfully", "success")
        return redirect(url_for('retrieve_payment'))
    except Exception as e:
        app.logger.error(f"Error in deleting payment details: {str(e)}")
        flash("An error occurred while deleting payment details. Please try again later.", "error")
        return redirect(url_for('home'))


# Define a route for selecting order collection type
@app.route('/order', methods=['POST', 'GET'])
def order_collection():
    # Create an instance of the collection type form
    collection_Type = collection_type(request.form)

    # Check if the form is submitted and valid
    if request.method == 'POST' and collection_Type.validate():
        # Generate a unique order ID using UUID
        order_id = str(uuid.uuid4())
        order_data = {
            'order_id': order_id,
            'collection_type': collection_Type.collection_type.data
        }

        # Store order data in the order database
        with shelve.open('order.db', 'c') as db:
            orders = db.get('orders', {})
            orders[order_id] = order_data
            db['orders'] = orders

        # Initialize an empty cart for the order in the cart database
        with shelve.open('order.db', 'c') as db:
            cart = db.get('cart', {})
            cart[order_id] = []
            db['cart'] = cart

        # Redirect to the product page
        return redirect(url_for('show_products'))

    # Render the order collection type form
    return render_template('order_collection.html', form=collection_Type)


@app.route('/products', endpoint='show_products')
def show_products():
    try:
        # Retrieve the order details from the shelves database
        with shelve.open('order.db', 'c') as order_db:
            orders = order_db.get('orders', {})

            # Check if there are any orders
            if not orders:
                return render_template('error.html', error_message="Order not found")

            # Retrieve the last order ID (or choose the appropriate order ID based on your logic)
            order_id = list(orders.keys())[-1]  # Assuming you want the latest order, adjust as needed

            # Retrieve the cart from the shelves database
            cart = order_db.get('cart', {})
            order_cart = cart.get(order_id, [])

        return render_template('products.html', food=food, coffee=coffee, non_coffee=non_coffee, cart=order_cart)

    except Exception as e:
        # You can customize the error template or redirect to an error page
        return render_template('error.html', error_message=f"An error occurred: {str(e)}")


# Define a route for adding products to the cart
@app.route('/add_to_cart/<product_id>', methods=['POST'], endpoint='add_to_cart')
def add_to_cart(product_id):
    # Retrieve the selected product from the products dictionary
    product = all_products.get(product_id)

    # Check if the product exists
    if not product:
        flash("Product not found", "error")
        return redirect(url_for('show_products'))

    # Retrieve order details from the shelve database
    order_db = shelve.open('order.db', 'r')
    orders = order_db.get('orders', {})

    # Check if there are any orders
    if not orders:
        flash("Order not found", "error")
        order_db.close()
        return redirect(url_for('home'))

    # Retrieve the last order ID (or choose the appropriate order ID based on your logic)
    order_id = list(orders.keys())[-1]  # Assuming you want the latest order, adjust as needed
    collection_type = orders[order_id]['collection_type']
    order_db.close()

    # Create an item to be added to the cart
    item = {
        'product_id': product_id,
        'name': product['name'],
        'price': product['price'],
        'quantity': int(request.form['quantity']),
        'order_id': order_id,
        'collection_type': collection_type,
        'image_path': product['image_path']
    }

    try:
        # Retrieve or initialize the cart from the shelves database
        cart_db = shelve.open('order.db', 'c')
        cart = cart_db.get('cart', {})
        order_cart = cart.get(order_id, [])

        # Check if the item is already in the cart
        for existing_item in order_cart:
            if existing_item['name'] == item['name']:
                # If yes, update the quantity
                existing_item['quantity'] += item['quantity']
                break
        else:
            # If not, add the item to the order cart
            order_cart.append(item)

        # Update the cart in the shelves database
        cart[order_id] = order_cart
        cart_db['cart'] = cart
        cart_db.close()

        flash("Product added to cart successfully", "success")
        return redirect(url_for('show_products'))
    except Exception as e:
        app.logger.error(f"Error in adding product to cart: {str(e)}")
        flash("An error occurred while adding the product to your cart. Please try again later.", "error")
        return redirect(url_for('home'))


def calculate_subtotal(cart):
    subtotal = 0
    for item in cart:
        if isinstance(item, dict) and 'quantity' in item and 'price' in item:
            subtotal += item['quantity'] * item['price']
    subtotal = round(subtotal, 2)
    return subtotal


def calculate_sales_tax(subtotal):
    return round(0.09 * subtotal, 2)


def calculate_delivery_amount(collection_type):
    return 5 if collection_type == 'delivery' else 0


def calculate_grand_total(subtotal, sales_tax, delivery_amount, collection_type):
    if collection_type == 'delivery':
        return round(subtotal + sales_tax + delivery_amount, 2)
    else:
        return round(subtotal + sales_tax, 2)


# Define a route for viewing the cart
@app.route('/view_cart')
def view_cart():
    try:
        # Retrieve order details from the shelves database
        with shelve.open('order.db', 'r') as order_db:
            orders = order_db.get('orders', {})

            # Check if there are any orders
            if not orders:
                return "Order not found"

            # Retrieve the last order ID
            order_id = list(orders.keys())[-1]
            collection_type = orders[order_id]['collection_type']

            # Retrieve the cart from the shelves database
            cart = order_db.get('cart', {})

            # Retrieve the order cart from the cart
            order_cart = cart.get(order_id, [])

            # Calculate various totals for rendering in the template
            subtotal = calculate_subtotal(order_cart)
            sales_tax = calculate_sales_tax(subtotal)
            delivery_amount = calculate_delivery_amount(collection_type)
            grand_total = calculate_grand_total(subtotal, sales_tax, delivery_amount, collection_type)

        # Render the cart view page
        return render_template('view_cart.html', cart=order_cart, subtotal=subtotal, sales_tax=sales_tax,
                               delivery_amount=delivery_amount, grand_total=grand_total)

    except Exception as e:
        return f"An error occurred: {str(e)}"


# Define a route for updating the quantity of a cart item
@app.route('/update_cart_item/<product_id>', methods=['POST', 'GET'])
def update_cart_item(product_id):
    try:
        # Retrieve order details from the shelves database
        order_db = shelve.open('order.db', 'r')
        orders = order_db.get('orders', {})

        # Check if there are any orders
        if not orders:
            flash("Order not found", "error")
            order_db.close()
            return redirect(url_for('home'))

        # Retrieve the last order ID
        order_id = list(orders.keys())[-1]  # Assuming you want the latest order
        order_db.close()

        # Check if order details are available
        if not order_id:
            flash("Order not found", "error")
            return redirect(url_for('home'))

        # Retrieve new quantity from the form
        new_quantity = request.form.get('quantity', '0')
        try:
            # Convert the new_quantity to an integer
            new_quantity = int(new_quantity)
        except ValueError:
            flash("Invalid quantity value", "error")
            return redirect(url_for('view_cart'))

        # Open the shelves database for cart update
        cart_db = shelve.open('order.db', 'c')
        cart = cart_db.get('cart', {})

        # Update the quantity of the specified product in the cart
        for item in cart.get(order_id, []):
            if item['product_id'] == product_id:
                item['quantity'] = new_quantity

        # Save the updated cart back to the database
        cart_db['cart'] = cart
        cart_db.close()

    except Exception as e:
        return f"An error occurred: {str(e)}"

    return redirect(url_for('view_cart'))


# Define a route for removing a product from the cart
@app.route('/remove_from_cart/<product_id>', methods=['POST'])
def remove_from_cart(product_id):
    try:
        # Retrieve order details from the shelves database
        with shelve.open('order.db', 'r') as order_db:
            orders = order_db.get('orders', {})

            # Check if there are any orders
            if not orders:
                # You can customize the error handling, such as redirecting to an error page
                return redirect(url_for('home'))

            # Retrieve the last order ID
            order_id = list(orders.keys())[-1]  # Assuming you want the latest order

        # Check if order details are available
        if not order_id:
            # You can customize the error handling, such as redirecting to an error page
            return redirect(url_for('home'))

        # Open the shelves database for cart update
        with shelve.open('order.db', 'c') as cart_db:
            cart = cart_db.get('cart', {})

            # Use list comprehension to create a new cart excluding the specified product_id
            new_cart = [item for item in cart.get(order_id, []) if item.get('product_id') != product_id]

            # Update the cart in the database
            cart[order_id] = new_cart
            cart_db['cart'] = cart

        return redirect(url_for('view_cart'))

    except Exception as e:
        # Handle the exception - you can customize this based on your requirements
        return f"An error occurred: {str(e)}"


@app.route('/payment', methods=['GET', 'POST'])
def payment_page():
    db = shelve.open('payment.db', 'r')
    payment_storage_dict = db.get('payment', {})
    db.close()

    if not payment_storage_dict:
        if request.method == 'GET':
            Payment = payment(request.form)
            return render_template('payment.html', has_payment_details=False, form=Payment)

        elif request.method == 'POST':
            payment_detail = request.form.get('payment_detail')
            return render_template('payment.html', has_payment_details=False, form=payment_detail)

    else:
        payment_details_list = list(payment_storage_dict.values())
        return render_template('payment.html', payment_details_list=payment_details_list, has_payment_details=True)


@app.route('/submit_payment', methods=['POST'])
def submit_payment():
    try:
        # Retrieve selected payment method from the form
        payment_detail = request.form.get('payment_detail')

        if payment_detail == 'new_payment' and request.method == 'POST':  # Change here to check for POST
            # Check if all the required card details are provided
            card_number = request.form.get('card_number')
            expiration_date = request.form.get('expiration_date')
            cvv = request.form.get('cvv')
            card_name = request.form.get('card_name')

            if not (card_number and expiration_date and cvv and card_name):
                flash("Please provide all required card details", "error")
                return redirect(url_for('payment_page'))

            # Perform logic to store the new payment details
            new_payment = payment_storage.payment_details(card_number, expiration_date, cvv, card_name)

            # Open the shelves database for payment storage
            with shelve.open('payment.db', 'c') as db:
                payment_storage_dict = db.get('payment', {})
                payment_storage_dict[new_payment.get_payment_details_id()] = new_payment
                db['payment'] = payment_storage_dict

        elif payment_detail:
            # Retrieve the selected payment details using payment ID
            with shelve.open('payment.db', 'r') as db:
                payment_storage_dict = db.get('payment', {})
                selected_payment = payment_storage_dict.get(payment_detail)

        else:
            flash("Invalid payment details", "error")
            return redirect(url_for('payment_page'))

        # Retrieve the order details from the shelves database
        with shelve.open('order.db', 'r') as order_db:
            orders = order_db.get('orders', {})

            # Check if there are any orders
            if not orders:
                flash("Order not found", "error")
                return redirect(url_for('home'))

            # Retrieve the last order ID
            order_id = list(orders.keys())[-1]

        return redirect(url_for('success_payment'))

    except Exception as e:
        # Handle the exception - customize this based on your requirements
        flash(f"An error occurred: {str(e)}", "error")

    return redirect(url_for('home'))


@app.route('/success_payment')
def success_payment():
    # Retrieve the order details from the order database
    order_db = shelve.open('order.db', 'r')
    orders = order_db.get('orders', {})

    if not orders:
        flash("Order not found", "error")
        order_db.close()
        return redirect(url_for('home'))

        # Retrieve the last order ID
    order_id = list(orders.keys())[-1]

    order_data = orders.get(order_id)
    collection_type = order_data['collection_type']

    # Retrieve the order cart from the order database
    cart_db = shelve.open('order.db', 'r')
    order_cart = cart_db.get('cart', {}).get(order_id, [])
    cart_db.close()

    # Calculate the totals
    subtotal = calculate_subtotal(order_cart)
    sales_tax = calculate_sales_tax(subtotal)
    delivery_amount = calculate_delivery_amount(collection_type)
    grand_total = calculate_grand_total(subtotal, sales_tax, delivery_amount, collection_type)

    # Render the success page with order details
    order_db.close()
    return render_template('success_payment.html', order_id=order_id, order_data=order_data,
                           grand_total=grand_total, collection_type=collection_type, order_cart=order_cart)


if __name__ == '__main__':
    app.run()
