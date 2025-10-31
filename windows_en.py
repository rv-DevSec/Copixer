import tkinter as tk
from tkinter import ttk, messagebox
import os
import shutil
import psutil
import time
import threading

class GameCopyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Copixer v1.1")
        self.root.geometry("1500x1000")
        self.root.configure(bg="#f0f0f0")

        # Variables
        # Adjust this path to your Windows username or desired source folder
        self.source_path = tk.StringVar(value="C:\\Users\\YourUsername\\Videos")
        self.selected_drive = tk.StringVar()
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

    def apply_style(self):
        """Apply consistent styling"""
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TButton", padding=6, relief="flat", background="#4CAF50", foreground="white")
        style.configure("TLabel", background="#f0f0f0", font=("Helvetica", 10))
        style.configure("TFrame", background="#f0f0f0")
        style.configure("TProgressbar", background="#4CAF50", troughcolor="#f0f0f0")

    def show_page(self, page_name):
        """Show the specified page"""
        if self.current_page:
            self.current_page.pack_forget()
        self.current_page = self.pages[page_name]
        self.current_page.pack(fill="both", expand=True)

    def create_step1_page(self):
        """Step 1: Search and select games"""
        frame = ttk.Frame(self.container, padding="15")
        
        # Source Path
        path_frame = ttk.Frame(frame)
        path_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(path_frame, text="Source Path:").pack(side="left", padx=5)
        ttk.Entry(path_frame, textvariable=self.source_path, width=50).pack(side="left", padx=5)
        ttk.Button(path_frame, text="Refresh Games", command=self.load_games).pack(side="left", padx=5)

        # Game List
        game_frame = ttk.LabelFrame(frame, text="Available Games", padding="10")
        game_frame.pack(fill="both", expand=True, pady=10)

        search_frame = ttk.Frame(game_frame)
        search_frame.pack(fill="x", pady=(0, 5))
        ttk.Label(search_frame, text="Search:").pack(side="left", padx=5)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_query)
        search_entry.pack(side="left", fill="x", expand=True, padx=5)
        search_entry.bind("<KeyRelease>", self.filter_games)

        self.game_listbox = tk.Listbox(game_frame, selectmode="multiple", height=10, 
                                     bg="white", relief="flat", borderwidth=2, font=("Courier", 10))
        self.game_listbox.pack(fill="both", expand=True)
        scrollbar = ttk.Scrollbar(game_frame, orient="vertical", command=self.game_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.game_listbox.config(yscrollcommand=scrollbar.set)
        self.game_listbox.bind('<<ListboxSelect>>', self.update_selected_info_step1)

        # Selected Info
        info_frame = ttk.Frame(game_frame)
        info_frame.pack(fill="x", pady=5)
        self.size_label_step1 = ttk.Label(info_frame, text="Selected Size: 0.00 GB")
        self.size_label_step1.pack(side="left", padx=5)

        # Next Button
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill="x", pady=10)
        ttk.Button(button_frame, text="Next", command=self.goto_step2).pack()

        # Initial load
        self.root.after(100, self.load_games)
        return frame

    def create_step2_page(self):
        """Step 2: Choose USB drive with size check and error label"""
        frame = ttk.Frame(self.container, padding="15")
        
        # Selected Games Info
        games_frame = ttk.LabelFrame(frame, text="Selected Games", padding="10")
        games_frame.pack(fill="both", expand=True, pady=(0, 10))
        self.games_listbox = tk.Listbox(games_frame, height=5, bg="white", relief="flat", 
                                       borderwidth=2, font=("Courier", 10))
        self.games_listbox.pack(fill="both", expand=True)
        self.size_label_step2 = ttk.Label(games_frame, text="Total Size: 0.00 GB")
        self.size_label_step2.pack(pady=5)

        # Drive Selection
        drive_frame = ttk.LabelFrame(frame, text="Detected Drives", padding="10")
        drive_frame.pack(fill="both", expand=True, pady=10)

        self.drive_combo = ttk.Combobox(drive_frame, textvariable=self.selected_drive, 
                                      state="readonly", width=50)
        self.drive_combo.pack(side="left", padx=5)
        ttk.Button(drive_frame, text="Detect Drives", command=self.detect_drives).pack(side="left", padx=5)

        self.drive_info_label = ttk.Label(drive_frame, text="Select a drive to see details")
        self.drive_info_label.pack(side="left", padx=10)
        
        # Error Label for insufficient space
        self.space_error_label = ttk.Label(drive_frame, text="", foreground="red", font=("Helvetica", 10))
        self.space_error_label.pack(side="left", padx=10)

        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill="x", pady=10)
        ttk.Button(button_frame, text="Back", command=lambda: self.show_page("step1")).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Next", command=self.goto_step3).pack(side="right", padx=5)

        # Initial drive detection and games info update
        self.detect_drives()
        self.update_games_info_step2()
        self.drive_combo.bind('<<ComboboxSelected>>', lambda e: self.update_drive_info())
        return frame

    def create_step3_page(self):
        """Step 3: Show cost and complete payment"""
        frame = ttk.Frame(self.container, padding="15")
        
        # Payment Info
        payment_frame = ttk.LabelFrame(frame, text="Payment", padding="10")
        payment_frame.pack(fill="both", expand=True, pady=10)
        
        self.size_label_step3 = ttk.Label(payment_frame, text="Selected Size: 0.00 GB")
        self.size_label_step3.pack(pady=5)
        self.price_label_step3 = ttk.Label(payment_frame, text="Price: $0.00")
        self.price_label_step3.pack(pady=5)

        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill="x", pady=10)
        ttk.Button(button_frame, text="Back", command=lambda: self.show_page("step2")).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Pay & Finish", command=self.start_copy_with_progress).pack(side="right", padx=5)

        return frame

    def load_games(self):
        """Load all folders into memory and display them"""
        self.game_listbox.delete(0, tk.END)
        self.folder_data.clear()
        self.all_folders.clear()
        
        try:
            if os.path.exists(self.source_path.get()):
                folders = [f for f in os.listdir(self.source_path.get()) 
                         if os.path.isdir(os.path.join(self.source_path.get(), f))]
                for i, folder in enumerate(sorted(folders), 1):
                    folder_path = os.path.join(self.source_path.get(), folder)
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
        """Filter the listbox based on search query"""
        self.game_listbox.delete(0, tk.END)
        query = self.search_query.get().lower()
        
        for display_text, folder, size_gb in self.all_folders:
            if query in folder.lower():
                self.game_listbox.insert(tk.END, display_text)
        self.update_selected_info_step1()

    def update_selected_info_step1(self, event=None):
        """Update display of total size in Step 1"""
        selected_indices = self.game_listbox.curselection()
        total_size_gb = 0
        
        if selected_indices:
            for idx in selected_indices:
                display_text = self.game_listbox.get(idx)
                total_size_gb += self.folder_data[display_text]['size_gb']
        
        self.size_label_step1.config(text=f"Selected Size: {total_size_gb:.2f} GB")

    def detect_drives(self):
        """Detect removable drives on Windows"""
        self.drive_info = {}
        drives = []
        partitions = psutil.disk_partitions()
        
        for partition in partitions:
            # Check for removable drives (e.g., USBs)
            if 'removable' in partition.opts or partition.mountpoint[1:] == ":\\":
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    # Only include drives with free space (likely external drives)
                    if usage.total > 0:
                        self.drive_info[partition.mountpoint] = {
                            'total': usage.total / (1024**3),
                            'used': usage.used / (1024**3),
                            'free': usage.free / (1024**3)
                        }
                        drives.append(partition.mountpoint)
                except:
                    continue

        if drives:
            self.drive_combo['values'] = drives
            self.drive_combo.set(drives[0])
            self.update_drive_info()
        else:
            self.drive_combo['values'] = []
            self.drive_combo.set("")
            self.drive_info_label.config(text="No removable drives detected")
            self.space_error_label.config(text="")
            messagebox.showinfo("Info", "No removable drives detected")

    def update_drive_info(self):
        """Update drive info display and check space"""
        if self.selected_drive.get() in self.drive_info:
            info = self.drive_info[self.selected_drive.get()]
            text = (f"Total: {info['total']:.2f} GB | "
                   f"Used: {info['used']:.2f} GB | "
                   f"Free: {info['free']:.2f} GB")
            self.drive_info_label.config(text=text)

            # Check if selected games fit in the drive
            total_size_gb = sum(self.folder_data[self.game_listbox.get(i)]['size_gb'] 
                              for i in self.game_listbox.curselection())
            if total_size_gb > info['free']:
                self.space_error_label.config(text="Not enough space!", foreground="red")
            else:
                self.space_error_label.config(text="")
        else:
            self.space_error_label.config(text="")

    def update_games_info_step2(self):
        """Update selected games info in Step 2"""
        self.games_listbox.delete(0, tk.END)
        total_size_gb = 0
        for game in self.selected_games:
            self.games_listbox.insert(tk.END, game)
            for display_text, data in self.folder_data.items():
                if data['name'] == game:
                    total_size_gb += data['size_gb']
                    break
        self.size_label_step2.config(text=f"Total Size: {total_size_gb:.2f} GB")
        self.update_drive_info()

    def goto_step2(self):
        """Move from Step 1 to Step 2"""
        selected_indices = self.game_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Warning", "Please select at least one game")
            return
        self.selected_games = [self.folder_data[self.game_listbox.get(i)]['name'] 
                             for i in selected_indices]
        self.show_page("step2")
        self.update_games_info_step2()

    def goto_step3(self):
        """Move from Step 2 to Step 3 with size check"""
        if not self.selected_drive.get():
            messagebox.showwarning("Warning", "Please select a destination drive")
            return

        total_size_gb = sum(self.folder_data[self.game_listbox.get(i)]['size_gb'] 
                          for i in self.game_listbox.curselection())
        if self.selected_drive.get() in self.drive_info:
            free_space_gb = self.drive_info[self.selected_drive.get()]['free']
            if total_size_gb > free_space_gb:
                messagebox.showerror("Error", 
                                   f"Not enough space on the drive!\n"
                                   f"Selected Size: {total_size_gb:.2f} GB\n"
                                   f"Free Space: {free_space_gb:.2f} GB\n"
                                   "Please choose another drive.")
                return

        self.size_label_step3.config(text=f"Selected Size: {total_size_gb:.2f} GB")
        total_size_mb = total_size_gb * 1024
        price = self.calculate_cost(total_size_mb)
        self.price_label_step3.config(text=f"Price: ${price:.2f}")
        self.show_page("step3")

    def calculate_cost(self, total_size_mb):
        """Calculate cost based on 7$ per 4MB"""
        if total_size_mb <= 0:
            return 0
        cost = (total_size_mb / 4) * 7
        return round(cost, 2)

    def start_copy_with_progress(self):
        """Start copying with progress bar in a separate thread"""
        total_size_gb = sum(self.folder_data[self.game_listbox.get(i)]['size_gb'] 
                          for i in self.game_listbox.curselection())
        total_size_mb = total_size_gb * 1024
        cost = self.calculate_cost(total_size_mb)

        self.cancel_copy = False
        self.progress_window = tk.Toplevel(self.root)
        self.progress_window.title("Copying Games")
        self.progress_window.geometry("300x150")
        self.progress_window.configure(bg="#f0f0f0")
        self.progress_window.transient(self.root)
        self.progress_window.grab_set()

        ttk.Label(self.progress_window, text="Copying in progress...").pack(pady=10)
        self.progress_bar = ttk.Progressbar(self.progress_window, length=200, mode="determinate")
        self.progress_bar.pack(pady=10)
        ttk.Button(self.progress_window, text="Cancel", command=self.cancel_copying).pack(pady=10)

        threading.Thread(target=self.finish_and_reset, daemon=True).start()

    def cancel_copying(self):
        """Set flag to cancel copying"""
        self.cancel_copy = True
        self.progress_window.destroy()
        messagebox.showinfo("Cancelled", "Copy operation was cancelled.")
        self.show_page("step3")

    def finish_and_reset(self):
        """Copy games with progress updates and reset"""
        source_path = self.source_path.get()
        dest_path = self.selected_drive.get()

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
                messagebox.showinfo(
                    "Success",
                    f"Payment completed and games copied!\n"
                    f"Total Size: {total_size_gb:.2f} GB\n"
                    f"Total Cost: ${cost}"
                )
                self.reset_app()
            else:
                # Clean up partial copy if cancelled
                for game in self.selected_games:
                    dest_folder = os.path.join(dest_path, self.get_unique_folder_name(dest_path, game))
                    if os.path.exists(dest_folder):
                        shutil.rmtree(dest_folder, ignore_errors=True)

        except Exception as e:
            self.progress_window.destroy()
            messagebox.showerror("Error", f"Failed to copy games: {str(e)}")
            self.reset_app()

    def reset_app(self):
        """Reset the app state"""
        self.selected_games = []
        self.search_query.set("")
        self.game_listbox.selection_clear(0, tk.END)
        self.selected_drive.set("")
        self.drive_combo.set("")
        self.drive_info_label.config(text="Select a drive to see details")
        self.space_error_label.config(text="")
        self.show_page("step1")
        self.load_games()

    def get_unique_folder_name(self, dest_path, folder_name):
        """Generate unique folder name with numeric suffix if needed"""
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