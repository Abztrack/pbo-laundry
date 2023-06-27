from tkinter import messagebox, ttk
import datetime
import re
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import locale


cred = credentials.Certificate('db.json')
firebase_admin.initialize_app(cred)
db = firestore.client()
locale.setlocale(locale.LC_ALL, 'id_ID')

class Model:
    def __init__(self):
        self.__db = db
        self.__transactions_ref = self.__db.collection('transactions')
    
    def get_db(self):
        return self.__db
    
    def get_transaction_ref(self):
        return self.__transactions_ref

    def generate_transaction_id(self):
        return Transaction().generate_transaction_id()

    def get_latest_transaction_id(self):
        return Transaction().get_latest_transaction_id()

    def add_transaction(self, data):
        return Transaction().add_transaction(data)

    def mark_transaction_as_finished(self, transaction_id):
        return Transaction().mark_transaction_as_finished(transaction_id)

    def get_unfinished_transactions(self):
        return Transaction().get_unfinished_transactions()
    
    def get_transaction_ref_by_id(self, transaction_id):
        return Transaction().get_transaction_ref_by_id(transaction_id)

    def filter_nomor(self, no_telp):
        return Filter().filter_nomor(no_telp)
        
    def get_services(self):
        return Services().get_services()

    def get_service_by_id(self, service_id):
        return Services().get_service_by_id(service_id)
    
    def read_date_format(self, timestamp_str):
        return Filter().read_date_format(timestamp_str)

class Filter(Model):
    
    def filter_nomor(self, no_telp):
        pattern = r'^0[0-9]{10,12}$'
        if re.match(pattern, no_telp):
            return no_telp
        else:
            raise ValueError("Format nomor tidak sesuai. Pastikan nomor diawali angka '0' dan 10-12 digit angka setelahnya.")
    
    def read_date_format(self, timestamp_str):
        timestamp = datetime.datetime.strptime(str(timestamp_str), "%Y-%m-%d %H:%M:%S.%f%z")
        formatted_timestamp = timestamp.strftime("%A, %d %B %Y - %H:%M:%S")
        return formatted_timestamp


class Services(Model):

    def get_services(self):
        services_ref = self.get_db().collection('services')
        query = services_ref.get()
        services = []
        for service in query:
            service_dict = service.to_dict()
            service_dict['id'] = service.id  
            services.append(service_dict)
        return services
    
    def get_service_by_id(self, service_id):
        service_doc = self.get_db().collection('services').document(service_id).get().to_dict()
        return service_doc

class Transaction(Model):
    
    def add_transaction(self, data):
        transaction_id = self.generate_transaction_id()
        transaction_ref = self.get_transaction_ref().document(transaction_id)
        transaction_ref.set(data)
        return transaction_id
    
    def generate_transaction_id(self):
        existing_ids = self.get_transaction_ref().stream()
        existing_numbers = [int(doc.id[1:]) for doc in existing_ids if doc.id.startswith('T')]

        if not existing_numbers:
            return 'T001'

        existing_numbers.sort()
        latest_number = existing_numbers[-1]
        new_number = latest_number + 1

        return f'T{str(new_number).zfill(3)}'
    
    def get_latest_transaction_id(self):
        latest_transactions = self.get_transaction_ref().order_by('timestamp', direction='DESCENDING').limit(1).stream()
        for transaction in latest_transactions:
            return transaction.id
        
        transaction_id = self.generate_transaction_id()
        transaction_ref = self.get_transaction_ref().document(transaction_id)
        transaction_data = {'id': transaction_id, 'timestamp': datetime.now()}
        transaction_ref.set(transaction_data)
        return transaction_id
    
    def get_unfinished_transactions(self):
        __transactions_ref = self.get_db().collection('transactions')
        query = __transactions_ref.where('status', '==', 'unfinished').get()
        unfinished_transactions = []
        for transaction in query:
            transaction_dict = transaction.to_dict()
            transaction_dict['id'] = transaction.id  
            unfinished_transactions.append(transaction_dict)
        return unfinished_transactions
    
    def get_transaction_ref_by_id(self, transaction_id):
        return self.get_db().collection('transactions').document(transaction_id)

    def mark_transaction_as_finished(self, transaction_id):
        transaction_ref = self.get_db().collection('transactions').document(transaction_id)
        transaction_ref.update({'status': 'finished'})
        messagebox.showinfo("Berhasil", "Transaksi ditandai sebagai selesai.")

    