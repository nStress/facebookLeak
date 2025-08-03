import os
import sys
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime


def parse_data_line(line):
    parts = line.strip().split(':')
    if len(parts) < 4:
        return None

    record = {}
    fields = [
        "mobilenumber", "userid", "firstname", "lastname", "gender",
        "residence", "birthplace", "relationship", "workplace",
        "joined", "email", "birthdate"
    ]

    for i, field in enumerate(fields):
        record[field] = parts[i] if i < len(parts) else ''

    if record.get("joined"):
        record["joined"] = re.sub(r' [0-9]{1,2}:[0-9]{2}:[0-9]{2} [AP]M', '', record["joined"])

    return record


def calculate_age(birthdate_str):
    if not birthdate_str:
        return None

    try:
        formats = ['%Y-%m-%d', '%d-%m-%Y', '%m-%d-%Y', '%Y/%m/%d', '%d/%m/%Y', '%m/%d/%Y']
        birthdate = None

        for fmt in formats:
            try:
                birthdate = datetime.strptime(birthdate_str, fmt)
                break
            except ValueError:
                continue

        if birthdate:
            today = datetime.now()
            age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
            return age
    except:
        pass

    return None


def read_data_from_files(folder_path):
    data = []
    if not os.path.exists(folder_path):
        return data

    for file_name in os.listdir(folder_path):
        if file_name.endswith(".txt"):
            file_path = os.path.join(folder_path, file_name)
            try:
                encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1', 'utf-16']
                content_read = False

                for encoding in encodings:
                    try:
                        with open(file_path, 'r', encoding=encoding) as f:
                            for line in f:
                                record = parse_data_line(line.strip())
                                if record:
                                    record['country'] = os.path.basename(folder_path)
                                    record['age'] = calculate_age(record.get('birthdate', ''))
                                    data.append(record)
                        content_read = True
                        break
                    except UnicodeDecodeError:
                        continue

                if not content_read:
                    print(f"Warning: Could not read file '{file_path}' with any supported encoding.")

            except Exception as e:
                print(f"Error reading file '{file_path}': {e}")
    return data


def get_available_folders():

    return [d for d in os.listdir('.') if os.path.isdir(d) and not d.startswith('.')]


def search_by_city(city_name, all_data):

    results = []
    city_lower = city_name.lower()

    for record in all_data:
        residence = record.get("residence", "").lower()
        if city_lower in residence:
            words = residence.split()
            for word in words:
                if city_lower in word or word in city_lower:
                    results.append(record)
                    break

    return results


def optimize_search_with_indices(all_data):
    indices = {
        'phone': {},
        'userid': {},
        'email': {},
        'city': {},
        'name': {}
    }

    for record in all_data:

        phone = record.get("mobilenumber", "")
        if phone:
            if phone not in indices['phone']:
                indices['phone'][phone] = []
            indices['phone'][phone].append(record)

        userid = record.get("userid", "")
        if userid:
            if userid not in indices['userid']:
                indices['userid'][userid] = []
            indices['userid'][userid].append(record)

        email = record.get("email", "")
        if email:
            if email not in indices['email']:
                indices['email'][email] = []
            indices['email'][email].append(record)

        residence = record.get("residence", "").lower()
        if residence:
            words = residence.split()
            for word in words:
                clean_word = re.sub(r'[^\w]', '', word)
                if clean_word and len(clean_word) > 1:
                    if clean_word not in indices['city']:
                        indices['city'][clean_word] = []
                    indices['city'][clean_word].append(record)

        firstname = record.get("firstname", "").lower()
        lastname = record.get("lastname", "").lower()
        if firstname:
            if firstname not in indices['name']:
                indices['name'][firstname] = []
            indices['name'][firstname].append(record)
        if lastname:
            if lastname not in indices['name']:
                indices['name'][lastname] = []
            indices['name'][lastname].append(record)

    return indices


class PersonSearchApp:
    def __init__(self, master):
        self.master = master
        master.title("Person Search Application - Advanced Version")
        master.geometry("1400x800")
        master.resizable(True, True)

        self.all_data = []
        self.filtered_data = []
        self.indices = {}
        self.available_countries = ["All Countries"] + sorted(get_available_folders())

        self.create_widgets()

    def create_widgets(self):

        main_container = ttk.PanedWindow(self.master, orient='horizontal')
        main_container.pack(fill='both', expand=True, padx=5, pady=5)

        left_frame = ttk.Frame(main_container, width=350)
        main_container.add(left_frame, weight=0)

        right_frame = ttk.Frame(main_container)
        main_container.add(right_frame, weight=1)

        load_frame = ttk.LabelFrame(left_frame, text="Load Data", padding="10")
        load_frame.pack(pady=5, padx=5, fill="x")

        self.load_data_button = ttk.Button(load_frame, text="📁 Select Country Directory",
                                           command=self.load_data_from_directory)
        self.load_data_button.pack(fill="x", pady=2)

        self.status_label = ttk.Label(load_frame, text="No data loaded", foreground="red")
        self.status_label.pack(pady=2)

        search_frame = ttk.LabelFrame(left_frame, text="Quick Search", padding="10")
        search_frame.pack(pady=5, padx=5, fill="x")

        ttk.Label(search_frame, text="Search Type:").pack(anchor="w")
        self.search_type_var = tk.StringVar()
        self.search_type_combobox = ttk.Combobox(search_frame, textvariable=self.search_type_var,
                                                 values=["city", "name", "phone", "userid", "email"], state="readonly")
        self.search_type_combobox.pack(fill="x", pady=2)
        self.search_type_combobox.set("city")

        ttk.Label(search_frame, text="Search Term:").pack(anchor="w")
        self.search_term_var = tk.StringVar()
        self.search_term_entry = ttk.Entry(search_frame, textvariable=self.search_term_var)
        self.search_term_entry.pack(fill="x", pady=2)
        self.search_term_entry.bind('<Return>', lambda e: self.perform_search())

        self.search_button = ttk.Button(search_frame, text="🔍 Search", command=self.perform_search)
        self.search_button.pack(fill="x", pady=2)

        self.clear_search_button = ttk.Button(search_frame, text="❌ Clear Search", command=self.clear_search)
        self.clear_search_button.pack(fill="x", pady=2)

        filter_frame = ttk.LabelFrame(left_frame, text="Advanced Filters", padding="10")
        filter_frame.pack(pady=5, padx=5, fill="x")

        age_frame = ttk.Frame(filter_frame)
        age_frame.pack(fill="x", pady=2)
        ttk.Label(age_frame, text="Age:").pack(anchor="w")

        age_range_frame = ttk.Frame(age_frame)
        age_range_frame.pack(fill="x")

        ttk.Label(age_range_frame, text="From:").pack(side="left")
        self.min_age_var = tk.StringVar()
        self.min_age_entry = ttk.Entry(age_range_frame, textvariable=self.min_age_var, width=8)
        self.min_age_entry.pack(side="left", padx=2)

        ttk.Label(age_range_frame, text="To:").pack(side="left")
        self.max_age_var = tk.StringVar()
        self.max_age_entry = ttk.Entry(age_range_frame, textvariable=self.max_age_var, width=8)
        self.max_age_entry.pack(side="left", padx=2)

        ttk.Label(filter_frame, text="City:").pack(anchor="w")
        self.city_filter_var = tk.StringVar()
        self.city_filter_entry = ttk.Entry(filter_frame, textvariable=self.city_filter_var)
        self.city_filter_entry.pack(fill="x", pady=2)

        ttk.Label(filter_frame, text="Phone (contains):").pack(anchor="w")
        self.phone_filter_var = tk.StringVar()
        self.phone_filter_entry = ttk.Entry(filter_frame, textvariable=self.phone_filter_var)
        self.phone_filter_entry.pack(fill="x", pady=2)

        ttk.Label(filter_frame, text="Gender:").pack(anchor="w")
        self.gender_filter_var = tk.StringVar()
        self.gender_filter_combobox = ttk.Combobox(filter_frame, textvariable=self.gender_filter_var,
                                                   values=["", "M", "F", "Male", "Female", "Masculin", "Feminin"],
                                                   state="readonly")
        self.gender_filter_combobox.pack(fill="x", pady=2)

        filter_buttons_frame = ttk.Frame(filter_frame)
        filter_buttons_frame.pack(fill="x", pady=5)

        self.apply_filters_button = ttk.Button(filter_buttons_frame, text="🔧 Apply Filters",
                                               command=self.apply_filters)
        self.apply_filters_button.pack(side="left", fill="x", expand=True, padx=2)

        self.clear_filters_button = ttk.Button(filter_buttons_frame, text="🗑️ Clear Filters",
                                               command=self.clear_filters)
        self.clear_filters_button.pack(side="right", fill="x", expand=True, padx=2)

        stats_frame = ttk.LabelFrame(left_frame, text="Statistics", padding="10")
        stats_frame.pack(pady=5, padx=5, fill="x")

        self.total_records_label = ttk.Label(stats_frame, text="Total records: 0")
        self.total_records_label.pack(anchor="w")

        self.filtered_records_label = ttk.Label(stats_frame, text="Displayed: 0")
        self.filtered_records_label.pack(anchor="w")

        self.country_label = ttk.Label(stats_frame, text="Country: -")
        self.country_label.pack(anchor="w")

        results_frame = ttk.LabelFrame(right_frame, text="Results", padding="10")
        results_frame.pack(fill="both", expand=True)

        tree_frame = ttk.Frame(results_frame)
        tree_frame.pack(fill="both", expand=True)

        columns = ("mobilenumber", "userid", "firstname", "lastname", "gender",
                   "age", "residence", "birthplace", "relationship", "workplace",
                   "joined", "email", "birthdate")

        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)

        self.tree.heading("mobilenumber", text="📱 Phone")
        self.tree.heading("userid", text="🆔 ID")
        self.tree.heading("firstname", text="👤 First Name")
        self.tree.heading("lastname", text="👤 Last Name")
        self.tree.heading("gender", text="👫 Gender")
        self.tree.heading("age", text="🎂 Age")
        self.tree.heading("residence", text="🏠 Residence")
        self.tree.heading("birthplace", text="🏥 Birthplace")
        self.tree.heading("relationship", text="💑 Relationship")
        self.tree.heading("workplace", text="🏢 Workplace")
        self.tree.heading("joined", text="📅 Joined")
        self.tree.heading("email", text="📧 Email")
        self.tree.heading("birthdate", text="🎂 Birthdate")

        self.tree.column("mobilenumber", width=120)
        self.tree.column("userid", width=80)
        self.tree.column("firstname", width=100)
        self.tree.column("lastname", width=100)
        self.tree.column("gender", width=60)
        self.tree.column("age", width=60)
        self.tree.column("residence", width=150)
        self.tree.column("birthplace", width=120)
        self.tree.column("relationship", width=100)
        self.tree.column("workplace", width=120)
        self.tree.column("joined", width=100)
        self.tree.column("email", width=180)
        self.tree.column("birthdate", width=100)

        v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)

        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        export_frame = ttk.Frame(right_frame)
        export_frame.pack(fill="x", padx=10, pady=5)

        self.export_button = ttk.Button(export_frame, text="💾 Export Results", command=self.export_results)
        self.export_button.pack(side="right")

    def load_data_from_directory(self):
        folder_path = filedialog.askdirectory(title="Select Country Directory")
        if not folder_path:
            return

        self.status_label.config(text="Loading data...", foreground="orange")
        self.master.update()

        self.all_data = read_data_from_files(folder_path)

        if self.all_data:
            self.indices = optimize_search_with_indices(self.all_data)
            country_name = os.path.basename(folder_path)

            self.status_label.config(text=f"✅ Loaded: {len(self.all_data)} records", foreground="green")
            self.country_label.config(text=f"Country: {country_name}")

            self.filtered_data = self.all_data.copy()
            self.update_table(self.filtered_data)
            self.update_stats()

            messagebox.showinfo("Success",
                                f"Loaded {len(self.all_data)} records from '{country_name}'.\nAll data is displayed in the table.")
        else:
            self.status_label.config(text="❌ No data found", foreground="red")
            self.country_label.config(text="Country: -")
            messagebox.showwarning("Error", "No data found in the selected directory.")

        self.clear_search()
        self.clear_filters()

    def update_table(self, results):
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not results:
            return

        for record in results:
            age_text = str(record.get("age", "")) if record.get("age") is not None else ""

            self.tree.insert("", "end", values=(
                record.get("mobilenumber", ""),
                record.get("userid", ""),
                record.get("firstname", ""),
                record.get("lastname", ""),
                record.get("gender", ""),
                age_text,
                record.get("residence", ""),
                record.get("birthplace", ""),
                record.get("relationship", ""),
                record.get("workplace", ""),
                record.get("joined", ""),
                record.get("email", ""),
                record.get("birthdate", "")
            ))

    def update_stats(self):
        total = len(self.all_data)
        filtered = len(self.filtered_data)

        self.total_records_label.config(text=f"Total records: {total}")
        self.filtered_records_label.config(text=f"Displayed: {filtered}")

    def perform_search(self):
        if not self.all_data:
            messagebox.showwarning("Search", "Please load data first.")
            return

        search_type = self.search_type_var.get()
        search_term = self.search_term_var.get().strip()

        if not search_term:
            messagebox.showwarning("Search", "Please enter a search term.")
            return

        results = []
        if search_type == "phone":
            results = [r for r in self.all_data if search_term in r.get("mobilenumber", "")]
        elif search_type == "userid":
            results = [r for r in self.all_data if search_term in r.get("userid", "")]
        elif search_type == "email":
            results = [r for r in self.all_data if search_term.lower() in r.get("email", "").lower()]
        elif search_type == "city":
            results = search_by_city(search_term, self.all_data)
        elif search_type == "name":
            name_parts = search_term.split()
            if len(name_parts) >= 2:
                last_name = name_parts[0].lower()
                first_name = " ".join(name_parts[1:]).lower()
                results = [
                    record for record in self.all_data
                    if record["firstname"].lower() == first_name and record["lastname"].lower() == last_name
                ]
            else:
                name_lower = search_term.lower()
                results = [
                    record for record in self.all_data
                    if name_lower in record["firstname"].lower() or name_lower in record["lastname"].lower()
                ]

        self.filtered_data = results
        self.update_table(results)
        self.update_stats()

        if not results:
            messagebox.showinfo("Search", f"No results found for '{search_term}' ({search_type}).")

    def clear_search(self):
        self.search_term_var.set("")
        if self.all_data:
            self.filtered_data = self.all_data.copy()
            self.update_table(self.filtered_data)
            self.update_stats()

    def apply_filters(self):
        if not self.all_data:
            messagebox.showwarning("Filters", "Please load data first.")
            return

        if self.search_term_var.get().strip():
            data_to_filter = self.filtered_data.copy()
        else:
            data_to_filter = self.all_data.copy()

        min_age = self.min_age_var.get().strip()
        max_age = self.max_age_var.get().strip()

        if min_age or max_age:
            try:
                min_val = int(min_age) if min_age else 0
                max_val = int(max_age) if max_age else 150

                data_to_filter = [
                    record for record in data_to_filter
                    if record.get('age') is not None and min_val <= record.get('age') <= max_val
                ]
            except ValueError:
                messagebox.showerror("Error", "Please enter valid numeric values for age.")
                return

        city_filter = self.city_filter_var.get().strip().lower()
        if city_filter:
            data_to_filter = [
                record for record in data_to_filter
                if city_filter in record.get("residence", "").lower()
            ]

        phone_filter = self.phone_filter_var.get().strip()
        if phone_filter:
            data_to_filter = [
                record for record in data_to_filter
                if phone_filter in record.get("mobilenumber", "")
            ]

        gender_filter = self.gender_filter_var.get().strip().lower()
        if gender_filter:
            data_to_filter = [
                record for record in data_to_filter
                if gender_filter in record.get("gender", "").lower()
            ]

        self.filtered_data = data_to_filter
        self.update_table(data_to_filter)
        self.update_stats()

        filters_applied = []
        if min_age or max_age:
            filters_applied.append(f"Age: {min_age or '0'}-{max_age or '150'}")
        if city_filter:
            filters_applied.append(f"City: {city_filter}")
        if phone_filter:
            filters_applied.append(f"Phone: {phone_filter}")
        if gender_filter:
            filters_applied.append(f"Gender: {gender_filter}")

        if filters_applied:
            messagebox.showinfo("Filters Applied",
                                f"Active filters: {', '.join(filters_applied)}\nResults: {len(data_to_filter)}")
        else:
            messagebox.showinfo("Filters", "No filters applied.")

    def clear_filters(self):
        self.min_age_var.set("")
        self.max_age_var.set("")
        self.city_filter_var.set("")
        self.phone_filter_var.set("")
        self.gender_filter_var.set("")

        if self.search_term_var.get().strip():
            self.perform_search()
        else:
            if self.all_data:
                self.filtered_data = self.all_data.copy()
                self.update_table(self.filtered_data)
                self.update_stats()

    def export_results(self):
        if not self.filtered_data:
            messagebox.showwarning("Export", "No data to export.")
            return

        file_path = filedialog.asksaveasfilename(
            title="Save results",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if not file_path:
            return

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                headers = ["Phone", "ID", "First Name", "Last Name", "Gender", "Age", "Residence",
                           "Birthplace", "Relationship", "Workplace", "Joined", "Email", "Birthdate"]

                if file_path.endswith('.csv'):
                    f.write(';'.join(headers) + '\n')
                    for record in self.filtered_data:
                        row = [
                            record.get("mobilenumber", ""),
                            record.get("userid", ""),
                            record.get("firstname", ""),
                            record.get("lastname", ""),
                            record.get("gender", ""),
                            str(record.get("age", "")),
                            record.get("residence", ""),
                            record.get("birthplace", ""),
                            record.get("relationship", ""),
                            record.get("workplace", ""),
                            record.get("joined", ""),
                            record.get("email", ""),
                            record.get("birthdate", "")
                        ]
                        f.write(';'.join(row) + '\n')
                else:
                    for record in self.filtered_data:
                        f.write(':'.join([
                            record.get("mobilenumber", ""),
                            record.get("userid", ""),
                            record.get("firstname", ""),
                            record.get("lastname", ""),
                            record.get("gender", ""),
                            record.get("residence", ""),
                            record.get("birthplace", ""),
                            record.get("relationship", ""),
                            record.get("workplace", ""),
                            record.get("joined", ""),
                            record.get("email", ""),
                            record.get("birthdate", "")
                        ]) + '\n')

            messagebox.showinfo("Export",
                                f"Data exported successfully!\nFile: {file_path}\nRecords: {len(self.filtered_data)}")

        except Exception as e:
            messagebox.showerror("Export Error", f"An error occurred during export:\n{str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = PersonSearchApp(root)
    root.mainloop()
