import tkinter as tk
from tkinter import ttk, messagebox
import threading
import webbrowser
import os
import timetable_logic # Import our logic file

class TimetableApp:
    def __init__(self, root):
        self.root = root
        self.root.title("BK Birla College - Timetable Generator")
        self.root.geometry("500x300")
        
        # Style configuration
        style = ttk.Style(self.root)
        style.theme_use('clam')
        style.configure('TButton', font=('Segoe UI', 12), padding=10)
        style.configure('TLabel', font=('Segoe UI', 11))
        style.configure('TProgressbar', thickness=20)

        # Main frame
        main_frame = ttk.Frame(self.root, padding="20 20 20 20")
        main_frame.pack(expand=True, fill=tk.BOTH)

        # --- Widgets ---
        self.status_label = ttk.Label(main_frame, text="Ready to generate timetable.", wraplength=460)
        self.status_label.pack(pady=(0, 20))

        self.progress_bar = ttk.Progressbar(main_frame, orient='horizontal', mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=10)

        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(pady=20)
        
        self.generate_button = ttk.Button(buttons_frame, text="Generate Timetable", command=self.start_generation_thread)
        self.generate_button.pack(side=tk.LEFT, padx=10)
        
        self.view_button = ttk.Button(buttons_frame, text="View Timetable", state="disabled", command=self.view_timetable)
        self.view_button.pack(side=tk.LEFT, padx=10)

        self.worker_thread = None

    def start_generation_thread(self):
        # Disable buttons to prevent multiple runs
        self.generate_button.config(state="disabled")
        self.view_button.config(state="disabled")
        self.status_label.config(text="Initializing evolution... Please wait.")
        self.progress_bar['value'] = 0
        
        # Run the AI logic in a separate thread to prevent the GUI from freezing
        self.worker_thread = threading.Thread(target=self.run_genetic_algorithm)
        self.worker_thread.start()
        
        # Periodically check the thread's progress
        self.root.after(100, self.check_thread)

    def run_genetic_algorithm(self):
        try:
            # Pass the GUI update function to the logic
            timetable_logic.run_evolution(self.update_progress)
            self.root.after(0, self.on_generation_complete)
        except FileNotFoundError as e:
            messagebox.showerror("Error", f"Could not find a required data file: {e.filename}\nPlease make sure all CSV files are in the same folder.")
            self.root.after(0, self.reset_ui)
        except Exception as e:
            messagebox.showerror("An Error Occurred", str(e))
            self.root.after(0, self.reset_ui)

    def update_progress(self, generation, total_generations, fitness):
        # This function is called from the worker thread, so we update the GUI safely
        progress = (generation / total_generations) * 100
        self.progress_bar['value'] = progress
        status_text = f"Generation {generation}/{total_generations} | Best Fitness: {fitness:.4f}"
        self.status_label.config(text=status_text)

    def check_thread(self):
        # If the thread is still running, check again after 100ms
        if self.worker_thread.is_alive():
            self.root.after(100, self.check_thread)

    def on_generation_complete(self):
        self.status_label.config(text="Generation complete! Timetable saved to timetable.html")
        self.progress_bar['value'] = 100
        self.generate_button.config(state="normal")
        self.view_button.config(state="normal")
        messagebox.showinfo("Success", "Timetable has been successfully generated and saved!")

    def reset_ui(self):
        self.status_label.config(text="Ready to generate timetable.")
        self.progress_bar['value'] = 0
        self.generate_button.config(state="normal")
        self.view_button.config(state="disabled")

    def view_timetable(self):
        filepath = os.path.abspath("timetable.html")
        if os.path.exists(filepath):
            webbrowser.open_new_tab(f"file://{filepath}")
        else:
            messagebox.showerror("Error", "timetable.html not found. Please generate the timetable first.")

if __name__ == "__main__":
    root = tk.Tk()
    app = TimetableApp(root)
    root.mainloop()
