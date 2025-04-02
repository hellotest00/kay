import flet as ft
import csv
import os
import time
from collections import defaultdict, Counter
import qrcode  # Import the qrcode library
from datetime import datetime  # Import datetime for date manipulation

def load_products():
    products = {}
    if os.path.exists("products.csv"):
        with open("products.csv", "r") as file:
            reader = csv.reader(file)
            header = next(reader)  # Skip the header row
            for row in reader:
                if row:  # Check if the row is not empty
                    products[row[0]] = float(row[1])
    else:
        products = {"Apple": 1.00, "Banana": 0.50, "Orange": 0.75, "Milk": 2.50, "Bread": 1.80}
        save_products(products)
    return products

def save_products(products):
    """
    Saves the products to the products.csv file, preserving the header row.

    Args:
        products (dict): A dictionary of products and their prices.
    """
    header = ["Name", "Price"]
    file_exists = os.path.exists("products.csv")

    with open("products.csv", "w", newline="") as file:
        writer = csv.writer(file)
        if file_exists:
            #  The file exists, so don't write the header again if it's already there.
            try:
                with open("products.csv", "r") as check_file:
                    reader = csv.reader(check_file)
                    existing_header = next(reader)
                    if existing_header != header:
                        writer.writerow(header) # Write header if it doesn't match
            except StopIteration:
                writer.writerow(header) # Write header if the file is empty
        else:
            # The file does not exist, write the header.
            writer.writerow(header)

        # Write (or overwrite) all product data.
        for name, price in products.items():
            writer.writerow([name, price])



def record_transaction(cart, customer_name):
    if not os.path.exists("transactions.csv"):
        with open("transactions.csv", "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Index", "Customer", "Product", "Price", "Amount", "Total", "Timestamp"])

    with open("transactions.csv", "a", newline="") as file:
        writer = csv.writer(file)
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        index = sum(1 for _ in open("transactions.csv"))  # Unique index
        cart_summary = {}

        for item in cart:
            if item[0] in cart_summary:
                cart_summary[item[0]]["amount"] += 1
                cart_summary[item[0]]["total"] += item[1]
            else:
                cart_summary[item[0]] = {"price": item[1], "amount": 1, "total": item[1]}

        for product, details in cart_summary.items():
            writer.writerow([index, customer_name, product, details["price"], details["amount"], details["total"], timestamp])

def pos_system_content(page: ft.Page):
    products = load_products()
    cart = []
    total_price = ft.Text("Total: $0.00", size=16, weight=ft.FontWeight.BOLD)
    cart_list = ft.Column()
    # product_list = ft.Column()  # Removed product_list
    feedback_text = ft.Text("", size=14, color=ft.colors.GREEN)
    receipt_content = ft.Column()  # To store receipt
    customer_name_field = ft.TextField(label="Customer Name", width=250)
    customer_name = "Unknown" # default

    def update_cart():
        cart_list.controls.clear()
        total = 0
        cart_summary = {}
        for item in cart:
            if item[0] in cart_summary:
                cart_summary[item[0]]["amount"] += 1
            else:
                cart_summary[item[0]] = {"price": item[1], "amount": 1}

        for index, (name, details) in enumerate(cart_summary.items()):
            remove_button = ft.IconButton(ft.icons.DELETE, style=ft.ButtonStyle(padding=ft.padding.all(0),shape=ft.RoundedRectangleBorder(radius=2)), on_click=lambda e, i=index: remove_from_cart(i))
            cart_list.controls.append(ft.Container(content=ft.Row([ft.Text(f"{name} x{details['amount']} - ${details['price']:.2f}",color=ft.colors.BLUE, weight=ft.FontWeight.BOLD),remove_button],spacing=1, tight=True),padding=ft.padding.symmetric(vertical=-4)))  # Adjusts space between rows
            total += details["price"] * details["amount"]
        total_price.value = f"Total: ${total:.2f}"
        page.update()

    def add_to_cart(e):
        item_name = product_dropdown.value
        # ***Important change:*** Reload products *every time* an item is added.
        products = load_products()
        # Check if the selected item_name is in the products dictionary
        if item_name in products:
            item_price = products[item_name]
            cart.append((item_name, item_price))
            update_cart()
            feedback_text.value = "" # clear
        else:
            print(f"Product {item_name} not found in products dictionary.") # error handling
            feedback_text.value = f"Product {item_name} not found!"
            page.update()

    def remove_from_cart(index):
        del cart[index]
        update_cart()

    def checkout(e):
        if cart:
            customer_name = customer_name_field.value.strip()
            if not customer_name:
                customer_name = "Unknown"
            record_transaction(cart, customer_name)
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            total = 0
            receipt_content.controls.clear() # Clear previous receipt
            receipt_content.controls.append(ft.Text("Receipt", size=20, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER))
            receipt_content.controls.append(ft.Divider())
            receipt_content.controls.append(ft.Text(f"Customer Name: {customer_name}", text_align=ft.TextAlign.CENTER))

            cart_summary = {} # Calculate the summary.
            for item in cart:
                if item[0] in cart_summary:
                    cart_summary[item[0]]["amount"] += 1
                    cart_summary[item[0]]["total"] += item[1]
                else:
                    cart_summary[item[0]] = {"price": item[1], "amount": 1, "total": item[1]}

            for product, details in cart_summary.items():
                receipt_content.controls.append(ft.Text(f"{product} x{details['amount']} - ${details['total']:.2f}"))
                total += details["total"]

            receipt_content.controls.append(ft.Divider())
            receipt_content.controls.append(ft.Text(f"Total: ${total:.2f}", weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER))
            receipt_content.controls.append(ft.Text(f"Date: {timestamp}", text_align=ft.TextAlign.CENTER)) # add time
            page.go("/receipt")  # Navigate to the receipt tab
            cart.clear()
            update_cart()
            feedback_text.value = f"Checkout successful! Total: ${total:.2f}  {timestamp}"
            customer_name_field.value = ""  # Clear the customer name field
            page.update()

        else:
            feedback_text.value = "Cart is empty!"
            page.dialog = ft.AlertDialog(title=ft.Text("Cart is empty!"))
            page.dialog.open = True
            page.update()

    def update_product_list():
        products = load_products()  # Reload products.
        product_dropdown.options.clear()
        if not products:
            product_dropdown.options.append(ft.dropdown.Option(text="No products available", key=""))
            product_dropdown.value = ""
            product_dropdown.disabled = True
        else:
            product_dropdown.disabled = False
            for name, price in products.items():
                product_dropdown.options.append(ft.dropdown.Option(text=f"{name} - ${price:.2f}", key=name))
            product_dropdown.value = product_dropdown.options[0].key if product_dropdown.options else None # set default
        page.update()

    def refresh_products(e): # new function
        products = load_products() # re-load
        update_product_list() # re-populate the dropdown
        page.update()

    # Create the input field and dropdown
    product_dropdown = ft.Dropdown(
        options=[],
        on_change=add_to_cart,
        label="Select a product",
        width=250,  # increased width to accommodate price
        disabled=True,
    )
    update_product_list()  # Initialize the dropdown options
    refresh_button = ft.ElevatedButton("Refresh", on_click=refresh_products)
    checkout_button = ft.ElevatedButton("Checkout", on_click=checkout, bgcolor=ft.colors.GREEN)

    # Store the dropdown and receipt in page.window
    page.window.product_dropdown = product_dropdown
    page.window.receipt_content = receipt_content # store

    return ft.Column(
        [
            ft.Container(height=7),
            customer_name_field, # add customer name input
            ft.Row([product_dropdown, refresh_button]),
            ft.Text("Cart:", size=16, weight=ft.FontWeight.BOLD),
            cart_list,
            total_price,
            checkout_button,
            feedback_text,
        ]
    )

def transaction_history_content(page: ft.Page):
    transactions_list = ft.Column()

    # Create the year, month, and day dropdowns
    year_dropdown = ft.Dropdown(
        options=[ft.dropdown.Option(str(y)) for y in range(2020, datetime.now().year + 1)],
        label="Year",
        width=100,
    )
    month_dropdown = ft.Dropdown(
        options=[ft.dropdown.Option(str(m).zfill(2)) for m in range(1, 13)],
        label="Month",
        width=100,
    )
    day_dropdown = ft.Dropdown(
        options=[ft.dropdown.Option(str(d).zfill(2)) for d in range(1, 32)],
        label="Day",
        width=100,
    )

    def load_transactions():
        transactions = []
        # Create transactions.csv if it doesn't exist
        if not os.path.exists("transactions.csv"):
            with open("transactions.csv", "w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["Index", "Customer", "Product", "Price", "Amount", "Total", "Timestamp"])

        if os.path.exists("transactions.csv"):
            with open("transactions.csv", "r") as file:
                reader = csv.reader(file)
                header = next(reader)  # Skip header row
                for row in reader:
                    transactions.append(row)
        return transactions

    def delete_transaction(e, index_to_delete):
        transactions = load_transactions()
        if 0 <= index_to_delete < len(transactions):
            del transactions[index_to_delete]
            # Rewrite the CSV without the deleted row
            with open("transactions.csv", "w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["Index", "Customer", "Product", "Price", "Amount", "Total", "Timestamp"])  # Write header
                for i, row in enumerate(transactions):
                    writer.writerow([i + 1] + row[1:])  # Re-index and write data
            update_transactions_list()
        else:
            print(f"Index {index_to_delete} out of range.  Transactions length: {len(transactions)}")

    def update_transactions_list(_=None):
        transactions_list.controls.clear()
        transactions = load_transactions()
        filtered_transactions = []

        # Get filter values
        selected_year = year_dropdown.value
        selected_month = month_dropdown.value
        selected_day = day_dropdown.value

        # Apply filters
        for row in transactions:
            try:
                timestamp_str = row[6]  # Timestamp is in the 7th column (index 6)
                # Attempt to parse the date with the format '2/4/2025 10:33'
                try:
                    transaction_date = datetime.strptime(timestamp_str, "%d/%m/%Y %H:%M")
                except ValueError:
                    # If the first format fails, try the original format '%Y-%m-%d %H:%M:%S'
                    transaction_date = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

                year_match = not selected_year or transaction_date.year == int(selected_year)
                month_match = not selected_month or transaction_date.month == int(selected_month)
                day_match = not selected_day or transaction_date.day == int(selected_day)

                if year_match and month_match and day_match:
                    filtered_transactions.append(row)
            except ValueError as e:
                print(f"Error parsing date: {e}, for row: {row}") # handle parsing issue

        # Reverse the order of filtered transactions before displaying
        for i, row in reversed(list(enumerate(filtered_transactions))):
            index, customer, product, price, amount, total, timestamp = row # include customer
            delete_button = ft.IconButton(ft.icons.DELETE, on_click=lambda e, i=i: delete_transaction(e, i))
            transactions_list.controls.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Text(f"#{int(index)}"),
                            ft.Text(f"Customer: {customer}"), # display customer name
                            ft.Text(f"Product: {product}"), # Display Product
                            ft.Text(f"Price: ${float(price):.2f}"),
                            ft.Text(f"Amount: x{amount}"), # Display Amount
                            ft.Text(f"Total: ${float(total):.2f}"),
                            ft.Text(timestamp),
                            delete_button
                        ],
                        spacing=1,
                        tight=True
                    ),
                    padding=ft.padding.symmetric(vertical=-2)
                )
            )

        page.update()

    refresh_button = ft.ElevatedButton("Refresh", on_click=lambda _: update_transactions_list())

    # Initial update
    update_transactions_list()

    return ft.Column(
        [
            ft.Text("Transaction History", size=20, weight=ft.FontWeight.BOLD),
            ft.Row([year_dropdown, month_dropdown, day_dropdown]), # add the dropdowns
            refresh_button,
            transactions_list
        ]
    )

def products_tab_content(page: ft.Page):
    products = load_products()
    products_list = ft.Column()

    def load_products_data():
        products_data = []
        if os.path.exists("products.csv"):
            with open("products.csv", "r") as file:
                reader = csv.reader(file)
                header = next(reader)  # Skip the header row.  Added in response to user query.
                for row in reader:
                    if row:
                        products_data.append(row)
        return products_data

    def update_products_list(e=None): # Make e optional
        products_list.controls.clear()
        products_data = load_products_data()
        for name, price in products_data:
            delete_button = ft.IconButton(ft.icons.DELETE, on_click=lambda e, product_name=name: delete_product(e, product_name), data=name)
            products_list.controls.append(
                ft.Row([
                    ft.Text(name),
                    ft.Text(f"${float(price):.2f}"),
                    delete_button
                ])
            )
        # Update the product dropdown in the POS tab.
        if page.window.product_dropdown:
            product_dropdown = page.window.product_dropdown
            product_dropdown.options.clear()
            products_dict = load_products() # get latest
            if not products_dict:
                product_dropdown.options.append(ft.dropdown.Option(text="No products available", key=""))
                product_dropdown.value = ""
                product_dropdown.disabled = True
            else:
                product_dropdown.disabled = False
                for name, price in products_dict.items():
                    product_dropdown.options.append(ft.dropdown.Option(text=f"{name} - ${price:.2f}", key=name))
                product_dropdown.value = product_dropdown.options[0].key if product_dropdown.options else None
            # Find the POS tab and update.
            for control in page.controls:
                if isinstance(control, ft.Tabs):
                    for tab in control.tabs:
                        if tab.text == "POS System":
                            # Force update of the POS tab.
                            tab.content.update()
                            break
                    break
        page.update()

    product_name_field = ft.TextField(label="Product Name", width=200)
    product_price_field = ft.TextField(label="Price", keyboard_type=ft.KeyboardType.NUMBER, width=100)

    def add_product(e):
        new_product_name = product_name_field.value.strip()
        new_product_price = product_price_field.value.strip()
        if new_product_name and new_product_price:
            try:
                new_product_price = float(new_product_price)
                products[new_product_name] = new_product_price
                save_products(products)
                update_products_list()  # Update the product list after adding a new product
                product_name_field.value = ""
                product_price_field.value = ""
                page.update()
            except ValueError:
                page.dialog = ft.AlertDialog(title=ft.Text("Invalid price!"))
                page.dialog.open = True
                page.update()

    def delete_product(e, product_name):
        if product_name in products:
            del products[product_name]
            save_products(products)
            update_products_list()
            page.update()
        else:
            print(f"Product {product_name} not found.")

    update_products_list()

    add_product_button = ft.ElevatedButton("Add Product", on_click=add_product, bgcolor=ft.colors.BLUE)
    refresh_button = ft.ElevatedButton("Refresh", on_click=lambda _: update_products_list())

    return ft.Column(
        [
            ft.Text("Products", size=20, weight=ft.FontWeight.BOLD),
            ft.Row([product_name_field, product_price_field, add_product_button, refresh_button]),
            products_list,
        ]
    )

def hello_world_content(page: ft.Page):
    sales_data_text = ft.Text("Sales Data", size=20, weight=ft.FontWeight.BOLD)
    sales_display_area = ft.Column()

    def calculate_daily_sales():
        daily_sales = defaultdict(float)
        if os.path.exists("transactions.csv"):
            with open("transactions.csv", "r") as file:
                reader = csv.reader(file)
                header = next(reader)  # Skip header
                for row in reader:
                    try:
                        timestamp = row[6]  # Timestamp is in the 7th column (index 6) now
                        date = timestamp.split()[0]  # Extract date part
                        total = float(row[5])      # Total price is in 6th column now
                        daily_sales[date] += total
                    except (ValueError, IndexError) as e:
                        print(f"Error processing row: {row}. Error: {e}") #handle errors

        return daily_sales

    def update_sales_display(e=None): # Add e as an optional parameter.
        sales_display_area.controls.clear()
        daily_sales = calculate_daily_sales()
        if not daily_sales:
            sales_display_area.controls.append(ft.Text("No sales data available."))
        else:
            for date, total_sales in daily_sales.items():
                sales_display_area.controls.append(ft.Text(f"Date: {date}, Total Sales: ${total_sales:.2f}"))
        page.update()

    refresh_button = ft.ElevatedButton("Refresh Sales Data", on_click=update_sales_display)

    # Initial update
    update_sales_display()

    return ft.Column(
        [
            sales_data_text,
            refresh_button,
            sales_display_area,
        ]
    )

def hello_4_content(page: ft.Page):
    def quit_app(e):
        page.window.close()

    def get_top_10_sales():
        product_quantities = Counter()
        if os.path.exists("transactions.csv"):
            with open("transactions.csv", "r") as file:
                reader = csv.reader(file)
                header = next(reader)
                for row in reader:
                    try:
                        product = row[2]  # Product name is now in the 3rd column
                        amount = int(row[4]) # Amount sold is now in the 5th column
                        product_quantities[product] += amount
                    except (ValueError, IndexError) as e:
                        print(f"Error processing row: {row}. Error: {e}")
        # Get the top 10 products
        top_10 = product_quantities.most_common(10)
        return top_10

    def update_top_10_list(e=None): # Add e as an optional parameter.
        top_10_sales_list.controls.clear()
        top_10_products = get_top_10_sales()
        if not top_10_products:
            top_10_sales_list.controls.append(ft.Text("No sales data available."))
        else:
            for product, quantity in top_10_products:
                top_10_sales_list.controls.append(ft.Text(f"Product: {product}, Quantity Sold: {quantity}"))
        page.update()

    top_10_sales_title = ft.Text("Top 10 Sales", size=20, weight=ft.FontWeight.BOLD)
    top_10_sales_list = ft.Column()
    update_top_10_list() # Initial update

    refresh_button = ft.ElevatedButton("Refresh Top 10 Sales", on_click=update_top_10_list)

    return ft.Column(
        [
            top_10_sales_title, # Title
            refresh_button,
            top_10_sales_list,
            ft.Divider(),
            ft.ElevatedButton("Quit", on_click=quit_app),
        ]
    )

def receipt_tab_content(page: ft.Page):
    # Retrieve the receipt content from  page.window
    receipt_content = page.window.receipt_content if hasattr(page.window, 'receipt_content') else ft.Column()

    return ft.Column(
        [
            ft.Text("Receipt", size=24, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
            ft.Divider(),
            receipt_content,
        ]
    )

def qr_code_tab_content(page: ft.Page):
    # Generate the QR code
    data = "https://github.com/flet-dev/flet"  # Replace with your actual data
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Save the QR code to a temporary file
    qr_filename = "temp_qr.png"
    img.save(qr_filename)

    # Display the QR code
    qr_image = ft.Image(src=qr_filename, width=200, height=200)
    # Add the image here
    xyz_image = ft.Image(src="xyz.jpg", width=200, height=200) # Add this

    # Clean up the temporary file when the page is disposed
    def dispose():
        os.remove(qr_filename)
    page.on_dispose = dispose

    return ft.Column(
        [
            ft.Text("Scan this QR code", size=24, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
            #qr_image,
            xyz_image # And this
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.CENTER
    )

def main(page: ft.Page):
    page.title = "My POS App"

    # Store the page in page.window
    page.window.main_page = page

    tabs = ft.Tabs(
        expand=True,
        tabs=[
            ft.Tab(text="POS System", content=pos_system_content(page)),
            ft.Tab(text="Transaction", content=transaction_history_content(page)),
            ft.Tab(text="Products", content=products_tab_content(page)),
            ft.Tab(text="Sales", content=hello_world_content(page)),
            ft.Tab(text="Top", content=hello_4_content(page)),
            ft.Tab(text="Receipt", content=receipt_tab_content(page)),
            ft.Tab(text="QR Code", content=qr_code_tab_content(page)),
        ],
        #animate_selected_content=True, # causes error
    )

    # Add a function to handle route changes for navigation
    def route_change(route):
        if page.route == "/receipt":
            tabs.selected_index = 5
        elif page.route == "/qr":
            tabs.selected_index = 6
        else:
            tabs.selected_index = 0
        page.update()

    page.on_route_change = route_change
    page.go(page.route)  # Initial navigation

    page.add(tabs)

if __name__ == "__main__":
    ft.app(target=main)
