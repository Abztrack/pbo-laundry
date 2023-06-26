import tkinter as tk
import tkinter.filedialog as filedialog
from tkinter import messagebox, ttk
import re
import datetime
import pytz
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

cred = credentials.Certificate('db.json')
firebase_admin.initialize_app(cred)
db = firestore.client()
timezone = pytz.timezone('Asia/Jakarta')

class Model:
    def __init__(self):
        self.db = db
        self.transactions_ref = self.db.collection('transactions')

    def generate_transaction_id(self):
        existing_ids = self.transactions_ref.stream()
        existing_numbers = [int(doc.id[1:]) for doc in existing_ids if doc.id.startswith('T')]

        if not existing_numbers:
            return 'T001'

        existing_numbers.sort()
        latest_number = existing_numbers[-1]
        new_number = latest_number + 1

        return f'T{str(new_number).zfill(3)}'

    def get_latest_transaction_id(self):
        latest_transactions = self.transactions_ref.order_by('timestamp', direction='DESCENDING').limit(1).stream()
        for transaction in latest_transactions:
            return transaction.id
        
        # If no transactions are found, create a new one and return its ID
        transaction_id = self.generate_transaction_id()
        transaction_ref = self.transactions_ref.document(transaction_id)
        transaction_data = {'id': transaction_id, 'timestamp': datetime.now()}
        transaction_ref.set(transaction_data)
        return transaction_id

    def add_transaction(self, data):
        transaction_id = self.generate_transaction_id()
        transaction_ref = self.transactions_ref.document(transaction_id)
        transaction_ref.set(data)
        return transaction_id

    def mark_transaction_as_finished(self, transaction_id):
        transaction_ref = self.db.collection('transactions').document(transaction_id)
        transaction_ref.update({'status': 'finished'})
        messagebox.showinfo("Berhasil", "Transaksi ditandai sebagai selesai.")

    def get_unfinished_transactions(self):
        transactions_ref = self.db.collection('transactions')
        query = transactions_ref.where('status', '==', 'unfinished').get()
        unfinished_transactions = []
        for transaction in query:
            transaction_dict = transaction.to_dict()
            transaction_dict['id'] = transaction.id  # Include the 'id' field in the dictionary
            unfinished_transactions.append(transaction_dict)
        return unfinished_transactions

    def filter_nomor(self, no_telp):
        pattern = r'^0[0-9]{11}$'
        if re.match(pattern, no_telp):
            return no_telp
        else:
            raise ValueError("Format nomor tidak sesuai. Pastikan nomor 11 digit dan berawal dari angka '0'.")
        
    def get_services(self):
        services_ref = self.db.collection('services')
        query = services_ref.get()
        services = []
        for service in query:
            service_dict = service.to_dict()
            service_dict['id'] = service.id  # Include the 'id' field in the dictionary
            services.append(service_dict)
        return services

class View:
    def __init__(self, root, controller):
        self.root = root
        self.controller = controller
        self.root.title("Laundry Service")
        self.root.geometry("400x300")

        self.title_label = tk.Label(root, text="Laundry Service\nManagement System", font=("Helvetica", 16, "bold"))
        self.title_label.pack(pady=10)

        self.menu_frame = tk.Frame(root)
        self.menu_frame.pack(pady=20)

        self.menu_label = tk.Label(self.menu_frame, text="Main Menu", font=("Helvetica", 12, "bold"))
        self.menu_label.pack()

        self.add_transaction_btn = tk.Button(self.menu_frame, text="Tambah Transaksi", command=self.controller.input_user, bg="#4caf50", fg="white", font=("Helvetica", 10, "bold"))
        self.add_transaction_btn.pack(pady=5)

        self.unfinished_transactions_btn = tk.Button(
            self.menu_frame,
            text="Lihat Transaksi Belum Selesai",
            command=self.controller.display_unfinished_transactions,
            bg="#1976d2",
            fg="white",
            font=("Helvetica", 10, "bold")
        )
        self.unfinished_transactions_btn.pack(pady=8)

        self.exit_btn = tk.Button(
            self.menu_frame,
            text="Keluar",
            command=self.root.quit,
            bg="#d32f2f",
            fg="white",
            font=("Helvetica", 10, "bold")
        )
        self.exit_btn.pack(pady=8)

class Controller:
    def __init__(self, root):
        self.model = Model()
        self.view = View(root, self)  # Pass the controller instance

        self.view.add_transaction_btn.configure(command=self.input_user)
        self.view.unfinished_transactions_btn.configure(command=self.display_unfinished_transactions)

    def run(self):
        self.view.root.mainloop()

    def input_user(self):
        input_window = tk.Toplevel(self.view.root)
        input_window.title("Tambah Transaksi")
        input_window.geometry("400x250")

        input_label = tk.Label(input_window, text="Input User Data", font=("Helvetica", 12, "bold"))
        input_label.pack()

        name_label = tk.Label(input_window, text="Nama:", font=("Helvetica", 10))
        name_label.pack()
        name_entry = tk.Entry(input_window)
        name_entry.pack()

        address_label = tk.Label(input_window, text="Alamat:", font=("Helvetica", 10))
        address_label.pack()
        address_entry = tk.Entry(input_window)
        address_entry.pack()

        phone_label = tk.Label(input_window, text="Nomor Telepon:", font=("Helvetica", 10))
        phone_label.pack()
        phone_entry = tk.Entry(input_window)
        phone_entry.pack()

        add_transaction_btn = tk.Button(
            input_window,
            text="Tambah Data",
            command=lambda: self.add_transaction(name_entry.get(), address_entry.get(), phone_entry.get(), input_window),
            bg="#1976d2",
            fg="white",
            font=("Helvetica", 10, "bold")
        )
        add_transaction_btn.pack(pady=10)

    def add_transaction(self, name, address, phone, input_window):
        try:
            phone = self.model.filter_nomor(phone)
            data = {
                "nama_pembeli": name,
                "alamat_pembeli": address,
                "no_telp_pembeli": phone,
                "status": "unfinished"
            }
            transaction_id = self.model.add_transaction(data)
            messagebox.showinfo("Berhasil", "Data telah ditambahkan.")
            input_window.destroy()  # Close the input window after adding the transaction
            self.choose_service(transaction_id)  # Open the service selection menu
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def choose_service(self, transaction_id):
        service_window = tk.Toplevel(self.view.root)
        service_window.title("Pilih jasa")
        service_window.geometry("400x300")

        service_label = tk.Label(service_window, text="Pilih jasa yang diinginkan", font=("Helvetica", 12, "bold"))
        service_label.pack()

        service_var = tk.StringVar()
        service_var.set("Cuci")

        service_radio_frame = tk.Frame(service_window)
        service_radio_frame.pack(pady=10)

        services = self.model.get_services()  # Fetch services from the Firestore database

        for service in services:
            service_radio = tk.Radiobutton(
                service_radio_frame,
                text=f"{service['name']}\nHarga: Rp{service['price']}\nLama Pengerjaan: {service['time']} Jam",
                variable=service_var,
                value=service['name'],
                justify="left",
                font=("Helvetica", 10)
            )
            service_radio.pack(anchor="w")

        weight_label = tk.Label(service_window, text="Berat (dalam kg):", font=("Helvetica", 10))
        weight_label.pack()
        weight_entry = tk.Entry(service_window)
        weight_entry.pack()

        confirm_btn = tk.Button(
            service_window,
            text="Konfirmasi",
            command=lambda: self.confirm_service(transaction_id, service_var.get(), weight_entry.get(), service_window),
            bg="#1976d2",
            fg="white",
            font=("Helvetica", 10, "bold")
        )
        confirm_btn.pack(pady=10)

    def confirm_service(self, transaction_id, service, weight, service_window):
        if service == "Cuci":
            service_id = "J01"  # Set the service ID for "Cuci"
        elif service == "Setrika":
            service_id = "J02"  # Set the service ID for "Setrika"
        elif service == "Cuci & Setrika":
            service_id = "J03"  # Set the service ID for "Cuci & Setrika"
        else:
            messagebox.showerror("Error", "Kamu belum memilih jasa.")
            return

        services_ref = self.model.db.collection('services')
        service_doc = services_ref.document(service_id).get().to_dict()

        if service_doc:
            price = service_doc['price']
            time = service_doc['time']
        else:
            messagebox.showerror("Error", "Tidak ada nama jasa yang kamu pilih.")

        try:
            weight = float(weight)
            total_price = price * weight
        except ValueError:
            messagebox.showerror("Error", "Input berat salah. Gunakan nilai numerik.")
            return

        entry_date = datetime.datetime.now(timezone)
        exit_date = entry_date + datetime.timedelta(hours=time)

        service_data = {
            "service": service,
            "service_id": service_id,  # Add the service ID to the service data
            "weight": weight,  # Add the weight to the service data
            "total_price": total_price,  # Add the total price to the service data
            "estimated_time": time,
            "status": "finished",
            "tgl_masuk": entry_date,
            "tgl_keluar": exit_date
        }
        transaction_ref = self.model.db.collection('transactions').document(transaction_id)
        transaction_ref.update(service_data)
        # messagebox.showinfo("Berhasil", "Jasa telah dikonfirmasi.")
        # Generate payment receipt
        receipt_text = f"Jasa: {service}\n\n" \
                       f"Harga: Rp{price}\n\n" \
                       f"Lama Pengerjaan: {time} Jam\n\n" \
                       f"Berat: {weight} kg\n\n" \
                       f"Total Harga: Rp{total_price}"

        # Save payment receipt as "receipt.txt"
        receipt_file_name = "receipt.txt"
        with open(receipt_file_name, "w") as receipt_file:
            receipt_file.write(receipt_text)

        # Show payment receipt using messagebox
        messagebox.showinfo("Payment Receipt", receipt_text)
        messagebox.showinfo("Berhasil", "Jasa telah masuk ke dalam database. Struk pembayaran telah disimpan sebagai receipt.txt.")
        service_window.destroy()

    def display_unfinished_transactions(self):
        unfinished_window = tk.Toplevel(self.view.root)
        unfinished_window.title("Transaksi Belum Selesai")

        unfinished_transactions = self.model.get_unfinished_transactions()

        if unfinished_transactions:
            num_transactions = len(unfinished_transactions)
            window_height = min(400 + num_transactions * 60, self.view.root.winfo_screenheight() - 100)
            unfinished_window.geometry(f"400x{window_height}")
            unfinished_label = tk.Label(unfinished_window, text="Transaksi Belum Selesai", font=("Helvetica", 12, "bold"))
            unfinished_label.pack()

            for i, transaction in enumerate(unfinished_transactions):
                transaction_text = f"Nama: {transaction['nama_pembeli']}\n" \
                                f"Alamat: {transaction['alamat_pembeli']}\n" \
                                f"No. Telp: {transaction['no_telp_pembeli']}\n" \
                                f"Status: {transaction['status']}\n"

                transaction_frame = tk.Frame(unfinished_window)
                transaction_frame.pack(pady=10)

                transaction_label = tk.Label(transaction_frame, text=transaction_text)
                transaction_label.pack()

                continue_btn = tk.Button(
                    transaction_frame,
                    text="Lanjutkan",
                    command=lambda transaction=transaction: (self.continue_transaction(transaction['id']), unfinished_window.destroy()),
                    bg="#1976d2",
                    fg="white",
                    font=("Helvetica", 10, "bold")
                )
                continue_btn.pack()

                if i < len(unfinished_transactions) - 1:
                    separator = ttk.Separator(unfinished_window, orient='horizontal')
                    separator.pack(fill='x', padx=10, pady=10)

        else:
            unfinished_window.geometry("400x200")
            no_transactions_label = tk.Label(unfinished_window, text="Tidak ada transaksi yang belum selesai.", font=("Helvetica", 10))
            no_transactions_label.pack()
            
    def continue_transaction(self, transaction_id):
        transaction_ref = self.model.db.collection('transactions').document(transaction_id)
        transaction_data = transaction_ref.get().to_dict()

        if transaction_data['status'] == 'unfinished':
            self.choose_service(transaction_id)  # Open the service selection menu
        else:
            messagebox.showerror("Error", "Transaksi ini sedang berjalan atau sudah selesai.")

    def display_exit_message(self):
        self.view.root.destroy()

    def display_invalid_choice_message(self):
        messagebox.showerror("Pilihan salah", "Pilihan salah. Silahkan coba lagi.")

if __name__ == '__main__':
    root = tk.Tk()
    controller = Controller(root)
    controller.run()
