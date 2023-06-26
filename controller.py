from model import Model
from view import View
import tkinter as tk
from tkinter import messagebox, ttk
import tkinter.filedialog as filedialog
import datetime
import pytz
import math

timezone = pytz.timezone('Asia/Jakarta')

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

        service_doc = self.model.get_service_by_id(service_id)

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
        transaction_ref = self.model.get_transaction_ref_by_id(transaction_id)
        transaction_ref.update(service_data)

        # messagebox.showinfo("Berhasil", "Jasa telah dikonfirmasi.")
        # Generate payment receipt

        transaction_doc = transaction_ref.get().to_dict()

        read_entry_date = self.model.read_date_format(entry_date)
        read_exit_date = self.model.read_date_format(exit_date)

        receipt_text = f"Nama : {transaction_doc['nama_pembeli']}\n\n" \
                       f"Alamat : {transaction_doc['alamat_pembeli']}\n\n" \
                       f"Nomor HP : {transaction_doc['no_telp_pembeli']}\n\n" \
                       f"------------------------------------------------------------------\n\n" \
                       f"Tanggal Masuk : {read_entry_date} \n\n" \
                       f"Tanggal Keluar : {read_exit_date} \n\n" \
                       f"------------------------------------------------------------------\n\n" \
                       f"Jasa : {service}\n\n" \
                       f"Harga : Rp{price}\n\n" \
                       f"Berat : {weight} kg\n\n" \
                       f"------------------------------------------------------------------\n\n" \
                       f"Total Harga : Rp{total_price}"

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
            items_per_page = 3  # Define the number of transactions to display per page
            num_pages = math.ceil(num_transactions / items_per_page)

            # Determine the current page based on the transactions length and items per page
            current_page = 1

            def show_page(page):
                # Clear the previous page's contents
                for widget in transaction_frame.winfo_children():
                    widget.destroy()

                start_index = (page - 1) * items_per_page
                end_index = start_index + items_per_page

                # Display the transactions for the current page
                for i, transaction in enumerate(unfinished_transactions[start_index:end_index]):
                    transaction_text = f"Nama: {transaction['nama_pembeli']}\n" \
                                        f"Alamat: {transaction['alamat_pembeli']}\n" \
                                        f"No. Telp: {transaction['no_telp_pembeli']}\n" \
                                        f"Status: {transaction['status']}\n"

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

                    if i < items_per_page - 1:
                        separator = ttk.Separator(transaction_frame, orient='horizontal')
                        separator.pack(fill='x', padx=10, pady=10)

            def go_to_previous_page():
                nonlocal current_page
                if current_page > 1:
                    current_page -= 1
                    show_page(current_page)

            def go_to_next_page():
                nonlocal current_page
                if current_page < num_pages:
                    current_page += 1
                    show_page(current_page)

            unfinished_label = tk.Label(unfinished_window, text="Transaksi Belum Selesai", font=("Helvetica", 12, "bold"))
            unfinished_label.pack()

            transaction_frame = tk.Frame(unfinished_window)
            transaction_frame.pack(pady=10)

            previous_btn = tk.Button(
                unfinished_window,
                text="Previous",
                command=go_to_previous_page,
                bg="#1976d2",
                fg="white",
                font=("Helvetica", 10, "bold")
            )
            previous_btn.pack(side="left")

            next_btn = tk.Button(
                unfinished_window,
                text="Next",
                command=go_to_next_page,
                bg="#1976d2",
                fg="white",
                font=("Helvetica", 10, "bold")
            )
            next_btn.pack(side="right")

            show_page(current_page)

        else:
            unfinished_window.geometry("400x200")
            no_transactions_label = tk.Label(unfinished_window, text="Tidak ada transaksi yang belum selesai.", font=("Helvetica", 10))
            no_transactions_label.pack()
            
    def continue_transaction(self, transaction_id):
        transaction_ref = self.model.get_transaction_ref_by_id(transaction_id)
        transaction_data = transaction_ref.get().to_dict()

        if transaction_data['status'] == 'unfinished':
            self.choose_service(transaction_id)  # Open the service selection menu
        else:
            messagebox.showerror("Error", "Transaksi ini sedang berjalan atau sudah selesai.")

    def display_exit_message(self):
        self.view.root.destroy()

    def display_invalid_choice_message(self):
        messagebox.showerror("Pilihan salah", "Pilihan salah. Silahkan coba lagi.")
