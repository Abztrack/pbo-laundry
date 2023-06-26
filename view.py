import tkinter as tk

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