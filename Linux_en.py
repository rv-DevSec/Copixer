import tkinter as tk
from tkinter import ttk, messagebox
import os
import shutil
import psutil
import time
import threading
from datetime import datetime

class GameCopyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Copixer v1.2")
        self.root.geometry("700x500")
        self.root.configure(bg="#1A1A1A")  # Dark Gray background

        # Hardcoded source path
        self.source_path = "/home/alcardox/Videos"
        self.selected_drive = None  # Will store full mountpoint of auto-selected drive
        self.search_query = tk.StringVar()
        self.selected_games = []
        self.drive_info = {}
        self.folder_data = {}
        self.all_folders = []
        self.cancel_copy = False

        # Container for pages
        self.container = ttk.Frame(self.root)
        self.container.pack(fill="both", expand=True)

        # Pages dictionary
        self.pages = {}
        self.current_page = None

        # Create pages
        self.pages["step1"] = self.create_step1_page()
        self.pages["step2"] = self.create_step2_page()
        self.pages["step3"] = self.create_step3_page()

        # Show first page
        self.show_page("step1")

        # Apply style
        self.apply_style()

        # Auto-detect USB drives periodically
        self.root.after(1000, self.auto_detect_drives)

    def apply_style(self):
        """Apply high-contrast dark theme"""
        style = ttk.Style()
        style.theme_use('clam')

        style.configure("TFrame", background="#1A1A1A")  # Dark Gray
        style.configure("TLabelframe", background="#333333", foreground="#FFFFFF")  # Medium Gray, White text
        style.configure("TLabelframe.Label", background="#333333", foreground="#FFFFFF", font=("Helvetica", 12, "bold"))

        style.configure("TLabel", background="#1A1A1A", foreground="#FFFFFF", font=("Helvetica", 10))
        style.configure("TScrollbar", background="#00BFFF", troughcolor="#1A1A1A", arrowcolor="#FFFFFF")
        style.configure("TProgressbar", background="#00BFFF", troughcolor="#1A1A1A")

    def show_page(self, page_name):
        if self.current_page:
            self.current_page.pack_forget()
        self.current_page = self.pages[page_name]
        self.current_page.pack(fill="both", expand=True)
        if page_name == "step2":
            self.detect_drives()  # Auto-detect when entering Step 2

    def create_button(self, parent, text, command):
        btn = tk.Button(parent, text=text, command=command,
                       bg="#00BFFF", fg="#FFFFFF", activebackground="#66CCFF", activeforeground="#FFFFFF",
                       relief="flat", font=("Helvetica", 10, "bold"))
        btn.bind("<Enter>", lambda e: btn.config(bg="#66CCFF"))
        btn.bind("<Leave>", lambda e: btn.config(bg="#00BFFF"))
        return btn

    def create_step1_page(self):
        frame = ttk.Frame(self.container, padding="15")
        
        refresh_frame = ttk.Frame(frame)
        refresh_frame.pack(fill="x", pady=(0, 10))
        self.create_button(refresh_frame, "Refresh Games", self.load_games).pack(side="left", padx=5)

        game_frame = ttk.LabelFrame(frame, text="Available Games", padding="10")
        game_frame.pack(fill="both", expand=True, pady=10)

        search_frame = ttk.Frame(game_frame)
        search_frame.pack(fill="x", pady=(0, 5))
        ttk.Label(search_frame, text="Search:").pack(side="left", padx=5)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_query, 
                                background="#1A1A1A", foreground="#FFFFFF")
        search_entry.pack(side="left", fill="x", expand=True, padx=5)
        search_entry.bind("<KeyRelease>", self.filter_games)

        self.game_listbox = tk.Listbox(game_frame, selectmode="multiple", height=10, 
                                     bg="#1A1A1A", fg="#FFFFFF", selectbackground="#00BFFF", selectforeground="#FFFFFF",
                                     relief="flat", borderwidth=2, font=("Courier", 10))
        self.game_listbox.pack(fill="both", expand=True)
        scrollbar = ttk.Scrollbar(game_frame, orient="vertical", command=self.game_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.game_listbox.config(yscrollcommand=scrollbar.set)
        self.game_listbox.bind('<<ListboxSelect>>', self.update_selected_info_step1)

        info_frame = ttk.Frame(game_frame)
        info_frame.pack(fill="x", pady=5)
        self.size_label_step1 = ttk.Label(info_frame, text="Selected Size: 0.00 GB", font=("Helvetica", 10, "bold"))
        self.size_label_step1.pack(side="left", padx=5)

        button_frame = ttk.Frame(frame)
        button_frame.pack(fill="x", pady=10)
        self.create_button(button_frame, "Next", self.goto_step2).pack()

        self.root.after(100, self.load_games)
        return frame

    def create_step2_page(self):
        frame = ttk.Frame(self.container, padding="15")
        
        games_frame = ttk.LabelFrame(frame, text="Selected Games", padding="10")
        games_frame.pack(fill="both", expand=True, pady=(0, 10))
        self.games_listbox = tk.Listbox(games_frame, height=5, 
                                       bg="#1A1A1A", fg="#FFFFFF", selectbackground="#00BFFF", selectforeground="#FFFFFF",
                                       relief="flat", borderwidth=2, font=("Courier", 10))
        self.games_listbox.pack(fill="both", expand=True)
        self.size_label_step2 = ttk.Label(games_frame, text="Total Size: 0.00 GB", font=("Helvetica", 10, "bold"))
        self.size_label_step2.pack(pady=5)

        drive_frame = ttk.LabelFrame(frame, text="Detected Drive", padding="10")
        drive_frame.pack(fill="both", expand=True, pady=10)

        self.drive_name_label = ttk.Label(drive_frame, text="No USB detected", font=("Helvetica", 16, "bold"))
        self.drive_name_label.pack(side="left", padx=10)
        self.drive_info_label = ttk.Label(drive_frame, text="Insert a USB drive", font=("Helvetica", 10))
        self.drive_info_label.pack(side="left", padx=10)
        self.space_error_label = ttk.Label(drive_frame, text="", foreground="#FF5555", font=("Helvetica", 10, "bold"))
        self.space_error_label.pack(side="left", padx=10)

        button_frame = ttk.Frame(frame)
        button_frame.pack(fill="x", pady=10)
        self.create_button(button_frame, "Back", lambda: self.show_page("step1")).pack(side="left", padx=5)
        self.create_button(button_frame, "Next", self.goto_step3).pack(side="right", padx=5)

        self.update_games_info_step2()
        return frame

    def create_step3_page(self):
        frame = ttk.Frame(self.container, padding="15")
        
        payment_frame = ttk.LabelFrame(frame, text="Payment", padding="10")
        payment_frame.pack(fill="both", expand=True, pady=10)
        
        self.size_label_step3 = ttk.Label(payment_frame, text="Selected Size: 0.00 GB", font=("Helvetica", 10, "bold"))
        self.size_label_step3.pack(pady=5)
        self.price_label_step3 = ttk.Label(payment_frame, text="Price: $0.00", font=("Helvetica", 10, "bold"))
        self.price_label_step3.pack(pady=5)

        button_frame = ttk.Frame(frame)
        button_frame.pack(fill="x", pady=10)
        self.create_button(button_frame, "Back", lambda: self.show_page("step2")).pack(side="left", padx=5)
        self.create_button(button_frame, "Pay & Finish", self.start_copy_with_progress).pack(side="right", padx=5)

        return frame

    def load_games(self):
        self.game_listbox.delete(0, tk.END)
        self.folder_data.clear()
        self.all_folders.clear()
        
        try:
            if os.path.exists(self.source_path):
                folders = [f for f in os.listdir(self.source_path) 
                         if os.path.isdir(os.path.join(self.source_path, f))]
                for i, folder in enumerate(sorted(folders), 1):
                    folder_path = os.path.join(self.source_path, folder)
                    folder_size = sum(os.path.getsize(os.path.join(dirpath, filename)) 
                                    for dirpath, _, filenames in os.walk(folder_path) 
                                    for filename in filenames)
                    size_gb = folder_size / (1024 * 1024 * 1024)
                    display_text = f"{i:3d} | {folder:<40} | {size_gb:>6.2f} GB"
                    self.all_folders.append((display_text, folder, size_gb))
                    self.folder_data[display_text] = {'name': folder, 'size_gb': size_gb}
                self.filter_games()
            else:
                messagebox.showerror("Error", "Invalid source path")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load games: {str(e)}")
        self.update_selected_info_step1()

    def filter_games(self, event=None):
        self.game_listbox.delete(0, tk.END)
        query = self.search_query.get().lower()
        for display_text, folder, size_gb in self.all_folders:
            if query in folder.lower():
                self.game_listbox.insert(tk.END, display_text)
        self.update_selected_info_step1()

    def update_selected_info_step1(self, event=None):
        selected_indices = self.game_listbox.curselection()
        total_size_gb = sum(self.folder_data[self.game_listbox.get(i)]['size_gb'] 
                          for i in selected_indices) if selected_indices else 0
        self.size_label_step1.config(text=f"Selected Size: {total_size_gb:.2f} GB")

    def auto_detect_drives(self):
        """Periodically check for USB drives"""
        if self.current_page == self.pages["step2"]:
            self.detect_drives()
        self.root.after(1000, self.auto_detect_drives)

    def detect_drives(self):
        self.drive_info = {}
        drives = []
        partitions = psutil.disk_partitions()
        for partition in partitions:
            if ('removable' in partition.opts or 'usb' in partition.device.lower() or 
                partition.mountpoint.startswith('/media') or partition.mountpoint.startswith('/mnt')):
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    drive_name = os.path.basename(partition.mountpoint)
                    self.drive_info[partition.mountpoint] = {
                        'name': drive_name,
                        'total': usage.total / (1024**3),
                        'used': usage.used / (1024**3),
                        'free': usage.free / (1024**3)
                    }
                    drives.append(partition.mountpoint)
                except:
                    continue
        if drives:
            self.selected_drive = drives[0]  # Auto-select first drive
            self.drive_name_label.config(text=self.drive_info[self.selected_drive]['name'])
            self.update_drive_info()
        else:
            self.selected_drive = None
            self.drive_name_label.config(text="No USB detected")
            self.drive_info_label.config(text="Insert a USB drive")
            self.space_error_label.config(text="")

    def update_drive_info(self):
        if self.selected_drive and self.selected_drive in self.drive_info:
            info = self.drive_info[self.selected_drive]
            text = (f"Total: {info['total']:.2f} GB | Used: {info['used']:.2f} GB | Free: {info['free']:.2f} GB")
            self.drive_info_label.config(text=text)
            total_size_gb = sum(self.folder_data[self.game_listbox.get(i)]['size_gb'] 
                              for i in self.game_listbox.curselection())
            if total_size_gb > info['free']:
                self.space_error_label.config(text="Not enough space!")
            else:
                self.space_error_label.config(text="")
        else:
            self.space_error_label.config(text="")

    def update_games_info_step2(self):
        self.games_listbox.delete(0, tk.END)
        total_size_gb = 0
        for game in self.selected_games:
            self.games_listbox.insert(tk.END, game)
            for display_text, data in self.folder_data.items():
                if data['name'] == game:
                    total_size_gb += data['size_gb']
                    break
        self.size_label_step2.config(text=f"Total Size: {total_size_gb:.2f} GB")
        self.detect_drives()

    def goto_step2(self):
        selected_indices = self.game_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Warning", "Please select at least one game")
            return
        self.selected_games = [self.folder_data[self.game_listbox.get(i)]['name'] 
                             for i in selected_indices]
        self.show_page("step2")

    def goto_step3(self):
        if not self.selected_drive:
            messagebox.showwarning("Warning", "No USB drive detected. Please insert a drive.")
            return
        total_size_gb = sum(self.folder_data[self.game_listbox.get(i)]['size_gb'] 
                          for i in self.game_listbox.curselection())
        free_space_gb = self.drive_info[self.selected_drive]['free']
        if total_size_gb > free_space_gb:
            messagebox.showerror("Error", 
                               f"Not enough space on the drive!\nSelected Size: {total_size_gb:.2f} GB\nFree Space: {free_space_gb:.2f} GB")
            return
        self.size_label_step3.config(text=f"Selected Size: {total_size_gb:.2f} GB")
        total_size_mb = total_size_gb * 1024
        price = self.calculate_cost(total_size_mb)
        self.price_label_step3.config(text=f"Price: ${price:.2f}")
        self.show_page("step3")

    def calculate_cost(self, total_size_mb):
        if total_size_mb <= 0:
            return 0
        cost = (total_size_mb / 4) * 7
        return round(cost, 2)

    def process_payment(self, total_cost):
        print(f"Simulating payment request for ${total_cost:.2f}")
        return True

    def log_transaction(self, total_size_gb, cost):
        with open("copixer_log.txt", "a") as log_file:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_file.write(f"{timestamp} | Size: {total_size_gb:.2f} GB | Cost: ${cost:.2f}\n")

    def start_copy_with_progress(self):
        total_size_gb = sum(self.folder_data[self.game_listbox.get(i)]['size_gb'] 
                          for i in self.game_listbox.curselection())
        total_size_mb = total_size_gb * 1024
        cost = self.calculate_cost(total_size_mb)

        payment_success = self.process_payment(cost)
        if payment_success:
            self.cancel_copy = False
            self.progress_window = tk.Toplevel(self.root)
            self.progress_window.title("Copying Games")
            self.progress_window.geometry("300x150")
            self.progress_window.configure(bg="#1A1A1A")
            self.progress_window.transient(self.root)
            self.progress_window.grab_set()

            ttk.Label(self.progress_window, text="Copying in progress...", 
                     background="#1A1A1A", foreground="#FFFFFF").pack(pady=10)
            self.progress_bar = ttk.Progressbar(self.progress_window, length=200, mode="determinate")
            self.progress_bar.pack(pady=10)
            self.create_button(self.progress_window, "Cancel", self.cancel_copying).pack(pady=10)

            threading.Thread(target=self.finish_and_reset, daemon=True).start()
        else:
            messagebox.showerror("Payment Failed", "Payment was not successful.")

    def cancel_copying(self):
        self.cancel_copy = True
        self.progress_window.destroy()
        messagebox.showinfo("Cancelled", "Copy operation was cancelled.")
        self.show_page("step3")

    def finish_and_reset(self):
        source_path = self.source_path
        dest_path = self.selected_drive

        total_size = sum(os.path.getsize(os.path.join(dirpath, filename)) 
                        for game in self.selected_games 
                        for dirpath, _, filenames in os.walk(os.path.join(source_path, game)) 
                        for filename in filenames)
        copied_size = 0
        self.progress_bar["maximum"] = total_size

        try:
            for game in self.selected_games:
                if self.cancel_copy:
                    break
                source_folder = os.path.join(source_path, game)
                unique_name = self.get_unique_folder_name(dest_path, game)
                dest_folder = os.path.join(dest_path, unique_name)
                
                for dirpath, _, filenames in os.walk(source_folder):
                    if self.cancel_copy:
                        break
                    for filename in filenames:
                        if self.cancel_copy:
                            break
                        src_file = os.path.join(dirpath, filename)
                        rel_path = os.path.relpath(src_file, source_folder)
                        dest_file = os.path.join(dest_folder, rel_path)
                        os.makedirs(os.path.dirname(dest_file), exist_ok=True)
                        shutil.copy2(src_file, dest_file)
                        copied_size += os.path.getsize(src_file)
                        self.progress_bar["value"] = copied_size
                        self.root.update_idletasks()
                        time.sleep(0.01)

            if not self.cancel_copy:
                self.progress_window.destroy()
                total_size_gb = sum(self.folder_data[self.game_listbox.get(i)]['size_gb'] 
                                  for i in self.game_listbox.curselection())
                total_size_mb = total_size_gb * 1024
                cost = self.calculate_cost(total_size_mb)
                self.log_transaction(total_size_gb, cost)
                messagebox.showinfo("Success", 
                                  f"Payment completed and games copied!\nTotal Size: {total_size_gb:.2f} GB\nTotal Cost: ${cost}")
                self.reset_app()
            else:
                for game in self.selected_games:
                    dest_folder = os.path.join(dest_path, self.get_unique_folder_name(dest_path, game))
                    if os.path.exists(dest_folder):
                        shutil.rmtree(dest_folder, ignore_errors=True)

        except Exception as e:
            self.progress_window.destroy()
            messagebox.showerror("Error", f"Failed to copy games: {str(e)}")
            self.reset_app()

    def reset_app(self):
        self.selected_games = []
        self.search_query.set("")
        self.game_listbox.selection_clear(0, tk.END)
        self.selected_drive = None
        self.drive_name_label.config(text="No USB detected")
        self.drive_info_label.config(text="Insert a USB drive")
        self.space_error_label.config(text="")
        self.show_page("step1")
        self.load_games()

    def get_unique_folder_name(self, dest_path, folder_name):
        base_name = folder_name
        counter = 1
        new_path = os.path.join(dest_path, folder_name)
        while os.path.exists(new_path):
            folder_name = f"{base_name}_{counter}"
            new_path = os.path.join(dest_path, folder_name)
            counter += 1
        return folder_name

def main():
    root = tk.Tk()
    app = GameCopyApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()