from flask import Flask, render_template, request, redirect, url_for, session, send_file, make_response
import sqlite3
from datetime import datetime
import pandas as pd
from io import BytesIO  # ✅ You already have this
from xhtml2pdf import pisa

# When using:
output = BytesIO()  # ✅ CORRECT





app = Flask(__name__)
app.secret_key = 'your_secret_key'

# --------------------- DATABASE INITIALIZATION ---------------------
def init_db():
    conn = sqlite3.connect('textile.db')
    c = conn.cursor()

    # Users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')

    # Inventory table
    c.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            threshold INTEGER NOT NULL,
            unit TEXT,
            supplier_name TEXT,
            purchase_date TEXT
        )
    ''')

    # Batches table
    c.execute('''
        CREATE TABLE IF NOT EXISTS batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_name TEXT NOT NULL,
            date TEXT NOT NULL,
            raw_material TEXT NOT NULL,
            quantity_used INTEGER NOT NULL,
            product TEXT NOT NULL,
            status TEXT NOT NULL
        )
    ''')

    # Yarns table
    c.execute('''
        CREATE TABLE IF NOT EXISTS yarns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            party_name TEXT,
            yarn_type TEXT,
            count TEXT,
            quantity INTEGER,
            mill_name TEXT
        )
    ''')

    # Orders table 
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            party_name TEXT,
            yarn_type TEXT,
            count TEXT,
            qty_given REAL,
            qty_taken REAL,
            balance REAL,
            dye_wt REAL,
            colours TEXT
        )
    ''')

    # Machine Registration table
    c.execute('''
        CREATE TABLE IF NOT EXISTS machines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            machine_name TEXT NOT NULL,
            capacity TEXT NOT NULL,
            status TEXT NOT NULL
        )
    ''')

    # Machine Usage table
    c.execute('''
        CREATE TABLE IF NOT EXISTS machine_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            machine_id INTEGER NOT NULL,
            color TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            date TEXT NOT NULL,
            FOREIGN KEY (machine_id) REFERENCES machines(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            party_name TEXT NOT NULL,
            items TEXT NOT NULL,
            quantity REAL NOT NULL,
            rate REAL NOT NULL,
            amount REAL NOT NULL,
            gst_percent REAL NOT NULL,
            total_amount REAL NOT NULL,
            payment_mode TEXT NOT NULL,
            status TEXT NOT NULL
        )
    ''')


    # Insert default user if not exists
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", ('admin', 'admin'))

    conn.commit()
    conn.close()


# --------------------- LOGIN ---------------------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('textile.db')
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cur.fetchone()
        conn.close()
        if user:
            session['user'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

# --------------------- DASHBOARD ---------------------
# --------------------- DASHBOARD ---------------------

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
    else:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

    if not start_date:
        start_date = datetime.now().strftime('%Y-%m-%d')
    if not end_date:
        end_date = start_date

    conn = sqlite3.connect('textile.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Existing stats
    cur.execute("SELECT COUNT(*) FROM inventory")
    total_inventory = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM batches")
    total_batches = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM inventory WHERE quantity <= threshold")
    low_stock = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM yarns WHERE date BETWEEN ? AND ?", (start_date, end_date))
    yarn_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM orders WHERE date BETWEEN ? AND ?", (start_date, end_date))
    orders_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM machine_usage WHERE date BETWEEN ? AND ?", (start_date, end_date))
    machine_usage_count = cur.fetchone()[0]

    # ---- NEW billing/invoice stats ----
    # Total invoices count overall
    cur.execute("SELECT COUNT(*) FROM invoices")
    total_invoices = cur.fetchone()[0]

    # Count of invoices in date range
    cur.execute("SELECT COUNT(*) FROM invoices WHERE date BETWEEN ? AND ?", (start_date, end_date))
    invoices_today = cur.fetchone()[0]

    # Sum of total billing amount in date range
    # Sum of total billing amount in date range
    cur.execute("SELECT IFNULL(SUM(total_amount), 0) FROM invoices WHERE date BETWEEN ? AND ?", (start_date, end_date))
    total_billing_amount = cur.fetchone()[0]


    conn.close()

    return render_template(
        'dashboard.html',
        total_inventory=total_inventory,
        total_batches=total_batches,
        low_stock=low_stock,
        start_date=start_date,
        end_date=end_date,
        yarn_today=yarn_count,
        orders_today=orders_count,
        machine_usage_today=machine_usage_count,
        total_invoices=total_invoices,
        invoices_today=invoices_today,
        total_billing_amount=total_billing_amount
    )


# --------------------- INVENTORY ---------------------
@app.route('/add_inventory', methods=['GET', 'POST'])
def add_inventory():
    if request.method == 'POST':
        item_name = request.form['item_name']
        quantity = int(request.form.get('quantity', 0))
        threshold = int(request.form.get('threshold', 0))
        unit = request.form.get('unit')
        supplier_name = request.form.get('supplier_name')
        purchase_date = request.form.get('purchase_date')

        conn = sqlite3.connect('textile.db')
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO inventory (item_name, quantity, threshold, unit, supplier_name, purchase_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (item_name, quantity, threshold, unit, supplier_name, purchase_date))
        conn.commit()
        conn.close()
        return redirect(url_for('view_inventory'))

    return render_template('inventory.html')

@app.route('/view_inventory')
def view_inventory():
    conn = sqlite3.connect('textile.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM inventory")
    items = cur.fetchall()
    conn.close()
    return render_template('view_inventory.html', items=items)

@app.route('/edit_inventory/<int:id>', methods=['GET', 'POST'])
def edit_inventory(id):
    conn = sqlite3.connect('textile.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    if request.method == 'POST':
        item_name = request.form['item_name']
        quantity = int(request.form.get('quantity', 0))
        threshold = int(request.form.get('threshold', 0))
        unit = request.form.get('unit')
        supplier_name = request.form.get('supplier_name')
        purchase_date = request.form.get('purchase_date')

        cur.execute('''
            UPDATE inventory
            SET item_name=?, quantity=?, threshold=?, unit=?, supplier_name=?, purchase_date=?
            WHERE id=?
        ''', (item_name, quantity, threshold, unit, supplier_name, purchase_date, id))
        conn.commit()
        conn.close()
        return redirect(url_for('view_inventory'))

    cur.execute("SELECT * FROM inventory WHERE id=?", (id,))
    item = cur.fetchone()
    conn.close()
    return render_template('edit_inventory.html', item=item)

@app.route('/delete_inventory/<int:id>')
def delete_inventory(id):
    conn = sqlite3.connect('textile.db')
    cur = conn.cursor()
    cur.execute("DELETE FROM inventory WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('view_inventory'))

# --------------------- BATCH ---------------------
@app.route('/add_batch', methods=['GET', 'POST'])
def add_batch():
    if request.method == 'POST':
        batch_name = request.form['batch_name']
        date = request.form['date']
        raw_material = request.form['raw_material']
        quantity_used = int(request.form['quantity_used'])
        product = request.form['product']
        status = request.form['status']

        conn = sqlite3.connect('textile.db')
        cur = conn.cursor()

        # Update inventory quantity
        cur.execute("SELECT quantity FROM inventory WHERE item_name = ?", (raw_material,))
        inventory_item = cur.fetchone()
        if inventory_item:
            current_quantity = inventory_item[0]
            new_quantity = max(current_quantity - quantity_used, 0)
            cur.execute("UPDATE inventory SET quantity = ? WHERE item_name = ?", (new_quantity, raw_material))

        # Insert into batches
        cur.execute('''
            INSERT INTO batches (batch_name, date, raw_material, quantity_used, product, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (batch_name, date, raw_material, quantity_used, product, status))

        conn.commit()
        conn.close()
        return redirect(url_for('view_batches'))

    materials = get_all_inventory_items()
    return render_template('addbatch.html', materials=materials)

@app.route('/view_batches')
def view_batches():
    conn = sqlite3.connect('textile.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM batches")
    batches = cur.fetchall()
    conn.close()
    return render_template('view_batches.html', batches=batches)

@app.route('/edit_batch/<int:id>', methods=['GET', 'POST'])
def edit_batch(id):
    conn = sqlite3.connect('textile.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT * FROM batches WHERE id=?", (id,))
    batch = cur.fetchone()

    if request.method == 'POST':
        batch_name = request.form['batch_name']
        date = request.form['date']
        raw_material = request.form['raw_material']
        quantity_used = int(request.form['quantity_used'])
        product = request.form['product']
        status = request.form['status']

        old_raw_material = batch['raw_material']
        old_quantity_used = batch['quantity_used']

        # Adjust inventory quantities
        if old_raw_material != raw_material:
            # Restore old quantity to old raw material
            cur.execute("SELECT quantity FROM inventory WHERE item_name = ?", (old_raw_material,))
            old_inv = cur.fetchone()
            if old_inv:
                restored_quantity = old_inv[0] + old_quantity_used
                cur.execute("UPDATE inventory SET quantity = ? WHERE item_name = ?", (restored_quantity, old_raw_material))

            # Deduct new quantity from new raw material
            cur.execute("SELECT quantity FROM inventory WHERE item_name = ?", (raw_material,))
            new_inv = cur.fetchone()
            if new_inv:
                new_quantity = max(new_inv[0] - quantity_used, 0)
                cur.execute("UPDATE inventory SET quantity = ? WHERE item_name = ?", (new_quantity, raw_material))

        else:
            # Same raw material, adjust by difference
            diff = quantity_used - old_quantity_used
            cur.execute("SELECT quantity FROM inventory WHERE item_name = ?", (raw_material,))
            inv = cur.fetchone()
            if inv:
                new_quantity = max(inv[0] - diff, 0)
                cur.execute("UPDATE inventory SET quantity = ? WHERE item_name = ?", (new_quantity, raw_material))

        # Update batch
        cur.execute('''
            UPDATE batches
            SET batch_name=?, date=?, raw_material=?, quantity_used=?, product=?, status=?
            WHERE id=?
        ''', (batch_name, date, raw_material, quantity_used, product, status, id))

        conn.commit()
        conn.close()
        return redirect(url_for('view_batches'))

    materials = get_all_inventory_items()
    conn.close()
    return render_template('editbatch.html', batch=batch, materials=materials)

@app.route('/delete_batch/<int:id>')
def delete_batch(id):
    conn = sqlite3.connect('textile.db')
    cur = conn.cursor()
    cur.execute("DELETE FROM batches WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('view_batches'))

# --------------------- YARN REGISTRATION ---------------------
@app.route('/add_yarn', methods=['GET', 'POST'])
def add_yarn():
    if request.method == 'POST':
        date = request.form['date']
        party_name = request.form['party_name']
        yarn_type = request.form['yarn_type']
        count = request.form['count']
        quantity = request.form['quantity']
        mill_name = request.form['mill_name']

        conn = sqlite3.connect('textile.db')
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO yarns (date, party_name, yarn_type, count, quantity, mill_name)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (date, party_name, yarn_type, count, quantity, mill_name))
        conn.commit()
        conn.close()
        return redirect(url_for('view_yarn'))
    return render_template('yarn_registration.html')


@app.route('/view_yarn')
def view_yarn():
    conn = sqlite3.connect('textile.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM yarns")
    yarns = cur.fetchall()
    conn.close()
    return render_template('view_yarn.html', yarns=yarns)


@app.route('/edit_yarn/<int:id>', methods=['GET', 'POST'])
def edit_yarn(id):
    conn = sqlite3.connect('textile.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    if request.method == 'POST':
        date = request.form['date']
        party_name = request.form['party_name']
        yarn_type = request.form['yarn_type']
        count = request.form['count']
        quantity = request.form['quantity']
        mill_name = request.form['mill_name']

        cur.execute('''
            UPDATE yarns
            SET date=?, party_name=?, yarn_type=?, count=?, quantity=?, mill_name=?
            WHERE id=?
        ''', (date, party_name, yarn_type, count, quantity, mill_name, id))
        conn.commit()
        conn.close()
        return redirect(url_for('view_yarn'))

    cur.execute("SELECT * FROM yarns WHERE id=?", (id,))
    yarn = cur.fetchone()
    conn.close()
    return render_template('edit_yarn.html', yarn=yarn)

@app.route('/delete_yarn/<int:id>')
def delete_yarn(id):
    conn = sqlite3.connect('textile.db')
    cur = conn.cursor()
    cur.execute("DELETE FROM yarns WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('view_yarn'))


# --------------------- ORDER FORM ---------------------
# ---------- ADD ORDER ----------
@app.route('/add_order', methods=['GET', 'POST'])
def add_order():
    if request.method == 'POST':
        date = request.form['date']
        party_name = request.form['party_name']
        yarn_type = request.form['yarn_type']
        count = request.form['count']
        qty_given = float(request.form['qty_given'])
        qty_taken = float(request.form['qty_taken'])
        balance = qty_given - qty_taken
        dye_wt = float(request.form['dye_wt'])
        colours = request.form['colours']

        conn = sqlite3.connect('textile.db')
        c = conn.cursor()
        c.execute('''
            INSERT INTO orders (date, party_name, yarn_type, count, qty_given, qty_taken, balance, dye_wt, colours)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (date, party_name, yarn_type, count, qty_given, qty_taken, balance, dye_wt, colours))
        conn.commit()
        conn.close()
        return redirect(url_for('view_orders'))

    return render_template('order_form.html')

# ---------- VIEW ORDERS ----------
@app.route('/view_orders')
def view_orders():
    conn = sqlite3.connect('textile.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM orders ORDER BY date DESC')
    orders = c.fetchall()
    conn.close()
    return render_template('view_orders.html', orders=orders)

# ---------- EDIT ORDER ----------
@app.route('/edit_order/<int:id>', methods=['GET', 'POST'])
def edit_order(id):
    conn = sqlite3.connect('textile.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    if request.method == 'POST':
        date = request.form['date']
        party_name = request.form['party_name']
        yarn_type = request.form['yarn_type']
        count = request.form['count']
        qty_given = float(request.form['qty_given'])
        qty_taken = float(request.form['qty_taken'])
        balance = qty_given - qty_taken
        dye_wt = float(request.form['dye_wt'])
        colours = request.form['colours']

        c.execute('''
            UPDATE orders
            SET date=?, party_name=?, yarn_type=?, count=?, qty_given=?, qty_taken=?, balance=?, dye_wt=?, colours=?
            WHERE id=?
        ''', (date, party_name, yarn_type, count, qty_given, qty_taken, balance, dye_wt, colours, id))
        conn.commit()
        conn.close()
        return redirect(url_for('view_orders'))

    c.execute('SELECT * FROM orders WHERE id=?', (id,))
    order = c.fetchone()
    conn.close()
    return render_template('edit_order.html', order=order)

# ---------- DELETE ORDER ----------
@app.route('/delete_order/<int:id>')
def delete_order(id):
    conn = sqlite3.connect('textile.db')
    c = conn.cursor()
    c.execute('DELETE FROM orders WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('view_orders'))


# --------------------- MACHINE REGISTRATION ---------------------
@app.route('/add_machine', methods=['GET', 'POST'])
def add_machine():
    if request.method == 'POST':
        machine_name = request.form['machine_name']
        capacity = request.form['capacity']
        status = request.form['status']

        conn = sqlite3.connect('textile.db')
        cur = conn.cursor()
        cur.execute("INSERT INTO machines (machine_name, capacity, status) VALUES (?, ?, ?)", (machine_name, capacity, status))
        conn.commit()
        conn.close()
        return redirect(url_for('view_machine_registration'))
    return render_template('machine_registration.html')

@app.route('/view_machine_registration')
def view_machine_registration():
    conn = sqlite3.connect('textile.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM machines")
    machines = cur.fetchall()
    conn.close()
    return render_template('view_machine_registration.html', machines=machines)

@app.route('/edit_machine/<int:id>', methods=['GET', 'POST'])
def edit_machine(id):
    conn = sqlite3.connect('textile.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    if request.method == 'POST':
        machine_name = request.form['machine_name']
        capacity = request.form['capacity']
        status = request.form['status']
        cur.execute('''
            UPDATE machines
            SET machine_name=?, capacity=?, status=?
            WHERE id=?
        ''', (machine_name, capacity, status, id))
        conn.commit()
        conn.close()
        return redirect(url_for('view_machine_registration'))

    cur.execute("SELECT * FROM machines WHERE id=?", (id,))
    machine = cur.fetchone()
    conn.close()
    return render_template('edit_machine.html', machine=machine)

@app.route('/delete_machine/<int:id>')
def delete_machine(id):
    conn = sqlite3.connect('textile.db')
    cur = conn.cursor()
    cur.execute("DELETE FROM machines WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('view_machine_registration'))

# --------------------- MACHINE USAGE ---------------------
@app.route('/add_machine_usage', methods=['GET', 'POST']) 
def add_machine_usage():
    conn = sqlite3.connect('textile.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    if request.method == 'POST':
        try:
            order_id = request.form['order_id']
            machine_id = request.form['machine_id']
            color = request.form['color']
            quantity = request.form['quantity']
            date = request.form['date']

            cur.execute("""
                INSERT INTO machine_usage (order_id, machine_id, color, quantity, date)
                VALUES (?, ?, ?, ?, ?)
            """, (order_id, machine_id, color, quantity, date))
            conn.commit()
            conn.close()
            return redirect(url_for('view_machine_usage'))
        except Exception as e:
            conn.close()
            return f"Error submitting usage: {e}"

    # ✅ UPDATED QUERY HERE
    cur.execute("SELECT id, machine_name, capacity FROM machines where status ='Available'")

    machines = cur.fetchall()

    cur.execute("SELECT id FROM orders")
    orders = cur.fetchall()

    conn.close()
    return render_template('machine_usage.html', machines=machines, orders=orders)

@app.route('/view_machine_usage')
def view_machine_usage():
    conn = sqlite3.connect('textile.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute('''
        SELECT mu.id, mu.order_id, m.machine_name, mu.color, mu.quantity, mu.date
        FROM machine_usage mu
        JOIN machines m ON mu.machine_id = m.id
    ''')
    usage = cur.fetchall()
    conn.close()
    return render_template('view_machine_usage.html', usages=usage)

@app.route('/edit_machine_usage/<int:id>', methods=['GET', 'POST'])
def edit_machine_usage(id):
    conn = sqlite3.connect('textile.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    if request.method == 'POST':
        order_id = request.form['order_id']
        machine_id = request.form['machine_id']
        color = request.form['color']
        quantity = request.form['quantity']
        date = request.form['date']

        cur.execute('''
            UPDATE machine_usage
            SET order_id=?, machine_id=?, color=?, quantity=?, date=?
            WHERE id=?
        ''', (order_id, machine_id, color, quantity, date, id))
        conn.commit()
        conn.close()
        return redirect(url_for('view_machine_usage'))

    cur.execute("SELECT * FROM machine_usage WHERE id=?", (id,))
    usage = cur.fetchone()
    cur.execute("SELECT id, machine_name FROM machines")
    machines = cur.fetchall()
    cur.execute("SELECT id FROM orders")
    orders = cur.fetchall()
    conn.close()
    return render_template('edit_machine_usage.html', usage=usage, machines=machines, orders=orders)

@app.route('/delete_machine_usage/<int:id>')
def delete_machine_usage(id):
    conn = sqlite3.connect('textile.db')
    cur = conn.cursor()
    cur.execute("DELETE FROM machine_usage WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('view_machine_usage'))

@app.route('/export_inventory_pdf')
def export_inventory_pdf():
    start = request.args.get('start')
    end = request.args.get('end')
    conn = sqlite3.connect('textile.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    if start and end:
        cur.execute('''
            SELECT *, (quantity <= threshold) as low_stock 
            FROM inventory 
            WHERE purchase_date BETWEEN ? AND ?
        ''', (start, end))
    else:
        cur.execute('SELECT *, (quantity <= threshold) as low_stock FROM inventory')
    items = cur.fetchall()
    conn.close()

    selected_date = f"{start} to {end}" if start and end else None
    rendered = render_template('inventory_pdf.html', items=items, selected_date=selected_date)
    pdf = BytesIO()
    pisa.CreatePDF(BytesIO(rendered.encode('utf-8')), dest=pdf)
    pdf.seek(0)
    return send_file(pdf, download_name='inventory_report.pdf', as_attachment=True)

@app.route('/export_inventory_excel')
def export_inventory_excel():
    start = request.args.get('start')
    end = request.args.get('end')
    conn = sqlite3.connect('textile.db')
    cur = conn.cursor()
    if start and end:
        cur.execute('''
            SELECT id, item_name, quantity, unit, threshold, supplier_name, purchase_date 
            FROM inventory 
            WHERE purchase_date BETWEEN ? AND ?
        ''', (start, end))
    else:
        cur.execute('SELECT id, item_name, quantity, unit, threshold, supplier_name, purchase_date FROM inventory')
    data = cur.fetchall()
    conn.close()

    df = pd.DataFrame(data, columns=['ID', 'Item Name', 'Quantity', 'Unit', 'Threshold', 'Supplier Name', 'Purchase Date'])
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Inventory')
        worksheet = writer.sheets['Inventory']
        for column_cells in worksheet.columns:
            max_len = max(len(str(cell.value)) if cell.value else 0 for cell in column_cells)
            worksheet.column_dimensions[column_cells[0].column_letter].width = max_len + 2
    output.seek(0)
    return send_file(output, download_name="inventory_report.xlsx", as_attachment=True)

@app.route('/export_batches_pdf')
def export_batches_pdf():
    start = request.args.get('start')
    end = request.args.get('end')
    conn = sqlite3.connect('textile.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    if start and end:
        cur.execute('''
            SELECT * FROM batches 
            WHERE date BETWEEN ? AND ?
        ''', (start, end))
    else:
        cur.execute('SELECT * FROM batches')
    batches = cur.fetchall()
    conn.close()

    selected_date = f"{start} to {end}" if start and end else None
    rendered = render_template('batches_pdf.html', batches=batches, selected_date=selected_date)
    pdf = BytesIO()
    pisa.CreatePDF(BytesIO(rendered.encode('utf-8')), dest=pdf)
    pdf.seek(0)
    return send_file(pdf, download_name='batches_report.pdf', as_attachment=True)

@app.route('/export_batches_excel')
def export_batches_excel():
    start = request.args.get('start')
    end = request.args.get('end')
    conn = sqlite3.connect('textile.db')
    cur = conn.cursor()
    if start and end:
        cur.execute('''
            SELECT batch_name, date, raw_material, quantity_used, product, status 
            FROM batches 
            WHERE date BETWEEN ? AND ?
        ''', (start, end))
    else:
        cur.execute('SELECT batch_name, date, raw_material, quantity_used, product, status FROM batches')
    rows = cur.fetchall()
    conn.close()

    df = pd.DataFrame(rows, columns=['Batch Name', 'Date', 'Raw Material', 'Quantity Used', 'Final Product', 'Status'])
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Batches')
        worksheet = writer.sheets['Batches']
        for column_cells in worksheet.columns:
            max_len = max(len(str(cell.value)) if cell.value else 0 for cell in column_cells)
            worksheet.column_dimensions[column_cells[0].column_letter].width = max_len + 2
    output.seek(0)
    return send_file(output, download_name='batches_report.xlsx', as_attachment=True)

@app.route('/export_yarns_pdf')
def export_yarns_pdf():
    start = request.args.get('start')
    end = request.args.get('end')
    conn = sqlite3.connect('textile.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    if start and end:
        cur.execute('''
            SELECT * FROM yarns 
            WHERE date BETWEEN ? AND ?
        ''', (start, end))
    else:
        cur.execute('SELECT * FROM yarns')
    yarns = cur.fetchall()
    conn.close()

    selected_date = f"{start} to {end}" if start and end else None
    rendered = render_template('yarns_pdf.html', yarns=yarns, selected_date=selected_date)
    pdf = BytesIO()
    pisa.CreatePDF(BytesIO(rendered.encode('utf-8')), dest=pdf)
    pdf.seek(0)
    return send_file(pdf, download_name='yarns_report.pdf', as_attachment=True)

@app.route('/export_yarns_excel')
def export_yarns_excel():
    start = request.args.get('start')
    end = request.args.get('end')
    conn = sqlite3.connect('textile.db')
    cur = conn.cursor()
    if start and end:
        cur.execute('''
            SELECT date, party_name, yarn_type, count, quantity, mill_name 
            FROM yarns 
            WHERE date BETWEEN ? AND ?
        ''', (start, end))
    else:
        cur.execute('SELECT date, party_name, yarn_type, count, quantity, mill_name FROM yarns')
    data = cur.fetchall()
    conn.close()

    df = pd.DataFrame(data, columns=['Date', 'Party Name', 'Yarn Type', 'Count', 'Quantity', 'Mill Name'])
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Yarns')
        worksheet = writer.sheets['Yarns']
        for column_cells in worksheet.columns:
            max_len = max(len(str(cell.value)) if cell.value else 0 for cell in column_cells)
            worksheet.column_dimensions[column_cells[0].column_letter].width = max_len + 2
    output.seek(0)
    return send_file(output, download_name='yarns_report.xlsx', as_attachment=True)

@app.route('/export_orders_pdf')
def export_orders_pdf():
    start = request.args.get('start')
    end = request.args.get('end')
    conn = sqlite3.connect('textile.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    if start and end:
        cur.execute('SELECT * FROM orders WHERE date BETWEEN ? AND ?', (start, end))
    else:
        cur.execute('SELECT * FROM orders')
    orders = cur.fetchall()
    conn.close()

    selected_date = f"{start} to {end}" if start and end else None
    rendered = render_template('orders_pdf.html', orders=orders, selected_date=selected_date)
    pdf = BytesIO()
    pisa.CreatePDF(BytesIO(rendered.encode('utf-8')), dest=pdf)
    pdf.seek(0)
    return send_file(pdf, download_name='orders_report.pdf', as_attachment=True)

@app.route('/export_orders_excel')
def export_orders_excel():
    start = request.args.get('start')
    end = request.args.get('end')
    conn = sqlite3.connect('textile.db')
    cur = conn.cursor()
    if start and end:
        cur.execute('''
            SELECT date, party_name, yarn_type, count, qty_given, qty_taken, balance, dye_wt, colours 
            FROM orders WHERE date BETWEEN ? AND ?
        ''', (start, end))
    else:
        cur.execute('''
            SELECT date, party_name, yarn_type, count, qty_given, qty_taken, balance, dye_wt, colours 
            FROM orders
        ''')
    data = cur.fetchall()
    conn.close()

    df = pd.DataFrame(data, columns=[
        'Date', 'Party Name', 'Yarn Type', 'Count',
        'Quantity Given', 'Quantity Taken', 'Balance',
        'Dye Weight', 'Colours'
    ])
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Orders')
        worksheet = writer.sheets['Orders']
        for column_cells in worksheet.columns:
            max_len = max(len(str(cell.value)) if cell.value else 0 for cell in column_cells)
            worksheet.column_dimensions[column_cells[0].column_letter].width = max_len + 2
    output.seek(0)
    return send_file(output, download_name="orders_report.xlsx", as_attachment=True)

@app.route('/export_machine_usage_pdf')
def export_machine_usage_pdf():
    start = request.args.get('start')
    end = request.args.get('end')
    conn = sqlite3.connect('textile.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    if start and end:
        cur.execute('''
            SELECT mu.id, mu.order_id, m.machine_name, mu.color, mu.quantity, mu.date
            FROM machine_usage mu
            JOIN machines m ON mu.machine_id = m.id
            WHERE mu.date BETWEEN ? AND ?
        ''', (start, end))
    else:
        cur.execute('''
            SELECT mu.id, mu.order_id, m.machine_name, mu.color, mu.quantity, mu.date
            FROM machine_usage mu
            JOIN machines m ON mu.machine_id = m.id
        ''')

    usage_data = cur.fetchall()
    conn.close()

    selected_date = f"{start} to {end}" if start and end else None
    rendered = render_template('machine_usage_pdf.html', usage_data=usage_data, selected_date=selected_date)
    pdf = BytesIO()
    pisa.CreatePDF(BytesIO(rendered.encode('utf-8')), dest=pdf)
    pdf.seek(0)
    return send_file(pdf, download_name='machine_usage_report.pdf', as_attachment=True)


@app.route('/export_machine_usage_excel')
def export_machine_usage_excel():
    start = request.args.get('start')
    end = request.args.get('end')
    conn = sqlite3.connect('textile.db')
    cur = conn.cursor()

    if start and end:
        cur.execute('''
            SELECT mu.id, mu.order_id, m.machine_name, mu.color, mu.quantity, mu.date
            FROM machine_usage mu
            JOIN machines m ON mu.machine_id = m.id
            WHERE mu.date BETWEEN ? AND ?
        ''', (start, end))
    else:
        cur.execute('''
            SELECT mu.id, mu.order_id, m.machine_name, mu.color, mu.quantity, mu.date
            FROM machine_usage mu
            JOIN machines m ON mu.machine_id = m.id
        ''')

    data = cur.fetchall()
    conn.close()

    df = pd.DataFrame(data, columns=[
        'ID', 'Order ID', 'Machine Name', 'Color', 'Quantity', 'Date'
    ])

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Machine Usage')
        worksheet = writer.sheets['Machine Usage']
        for column_cells in worksheet.columns:
            max_len = max(len(str(cell.value)) if cell.value else 0 for cell in column_cells)
            worksheet.column_dimensions[column_cells[0].column_letter].width = max_len + 2

    output.seek(0)
    return send_file(output, download_name="machine_usage_report.xlsx", as_attachment=True)

@app.route('/add_invoice', methods=['GET', 'POST'])
def add_invoice():
    if request.method == 'POST':
        date = request.form['date']
        party_name = request.form['party_name']
        items = request.form['items']
        quantity = request.form['quantity']
        rate = request.form['rate']
        amount = request.form['amount']
        gst = float(request.form['gst_percent'])
        total = float(request.form['total_amount'])
        payment_mode = request.form['payment_mode']
        status = request.form['status']

        conn = sqlite3.connect('textile.db')
        c = conn.cursor()
        c.execute('''
            INSERT INTO invoices (date, party_name, items, quantity, rate, amount, gst_percent, total_amount, payment_mode, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (date, party_name, items, quantity, rate, amount, gst, total, payment_mode, status))
        conn.commit()
        conn.close()
        return redirect(url_for('view_invoices'))

    return render_template('add_invoice.html')

# ---------- VIEW INVOICES ----------
@app.route('/view_invoices')
def view_invoices():
    conn = sqlite3.connect('textile.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM invoices ORDER BY date DESC')
    invoices = c.fetchall()
    conn.close()
    return render_template('view_invoices.html', invoices=invoices)

# ---------- EDIT INVOICE ----------
@app.route('/edit_invoice/<int:id>', methods=['GET', 'POST'])
def edit_invoice(id):
    conn = sqlite3.connect('textile.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    if request.method == 'POST':
        date = request.form['date']
        party_name = request.form['party_name']
        items = request.form['items']
        quantity = request.form['quantity']
        rate = request.form['rate']
        amount = request.form['amount']
        gst = float(request.form['gst'])
        total = float(request.form['total'])
        payment_mode = request.form['payment_mode']
        status = request.form['status']

        c.execute('''
            UPDATE invoices
            SET date=?, party_name=?, items=?, quantity=?, rate=?, amount=?, gst_percent=?, total_amount=?, payment_mode=?, status=?
            WHERE id=?
        ''', (date, party_name, items, quantity, rate, amount, gst, total, payment_mode, status, id))
        conn.commit()
        conn.close()
        return redirect(url_for('view_invoices'))

    c.execute('SELECT * FROM invoices WHERE id=?', (id,))
    invoice = c.fetchone()
    conn.close()
    return render_template('edit_invoice.html', invoice=invoice)

# ---------- DELETE INVOICE ----------
@app.route('/delete_invoice/<int:id>')
def delete_invoice(id):
    conn = sqlite3.connect('textile.db')
    c = conn.cursor()
    c.execute('DELETE FROM invoices WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('view_invoices'))

# ---------- EXPORT INVOICES PDF ----------
@app.route('/export_invoices_pdf')
def export_invoices_pdf():
    start = request.args.get('start')
    end = request.args.get('end')

    conn = sqlite3.connect('textile.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    if start and end:
        c.execute('SELECT * FROM invoices WHERE date BETWEEN ? AND ? ORDER BY date DESC', (start, end))
    else:
        c.execute('SELECT * FROM invoices ORDER BY date DESC')
    invoices = c.fetchall()
    conn.close()

    selected_date = f"{start} to {end}" if start and end else None

    rendered = render_template('invoices_pdf.html', invoices=invoices, selected_date=selected_date)

    pdf = BytesIO()
    pisa_status = pisa.CreatePDF(BytesIO(rendered.encode('utf-8')), dest=pdf)
    if pisa_status.err:
        return "Error generating PDF", 500

    pdf.seek(0)
    return send_file(pdf, download_name='invoices_report.pdf', as_attachment=True)

# ---------- EXPORT INVOICES EXCEL ----------
@app.route('/export_invoices_excel')
def export_invoices_excel():
    start = request.args.get('start')
    end = request.args.get('end')

    conn = sqlite3.connect('textile.db')
    c = conn.cursor()
    if start and end:
        c.execute('''
            SELECT date, party_name, items, quantity, rate, amount, gst_percent, total_amount, payment_mode, status
            FROM invoices WHERE date BETWEEN ? AND ? ORDER BY date DESC
        ''', (start, end))
    else:
        c.execute('''
            SELECT date, party_name, items, quantity, rate, amount, gst_percent, total_amount, payment_mode, status
            FROM invoices ORDER BY date DESC
        ''')
    data = c.fetchall()
    conn.close()

    df = pd.DataFrame(data, columns=[
        'Date', 'Party Name', 'Items', 'Quantity', 'Rate', 'Amount',
        'GST (%)', 'Total', 'Payment Mode', 'Status'
    ])

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Invoices')
        worksheet = writer.sheets['Invoices']
        for column_cells in worksheet.columns:
            max_len = max(len(str(cell.value)) if cell.value else 0 for cell in column_cells)
            worksheet.column_dimensions[column_cells[0].column_letter].width = max_len + 2
    output.seek(0)

    return send_file(output, download_name="invoices_report.xlsx", as_attachment=True)

# --------------------- HELPER FUNCTION ---------------------
def get_all_inventory_items():
    conn = sqlite3.connect('textile.db')
    cur = conn.cursor()
    cur.execute("SELECT item_name FROM inventory")
    items = [row[0] for row in cur.fetchall()]
    conn.close()
    return items

def update_orders_table():
    conn = sqlite3.connect('textile.db')
    c = conn.cursor()
    # Try adding columns one by one with try-except to avoid errors if they already exist
    try:
        c.execute("ALTER TABLE orders ADD COLUMN qty_given REAL")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE orders ADD COLUMN qty_taken REAL")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE orders ADD COLUMN balance REAL")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE orders ADD COLUMN dye_wt REAL")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE orders ADD COLUMN colours TEXT")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()


# --------------------- MAIN ---------------------
if __name__ == '__main__':
    init_db()
    update_orders_table()
    app.run(debug=True)


