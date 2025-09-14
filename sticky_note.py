import tkinter as tk
from tkinter import ttk, messagebox, colorchooser, font
import keyboard
import threading
import json
import os
from datetime import datetime

class ModernStickyNotes:
    def __init__(self):
        self.notes = []
        self.note_counter = 0
        self.data_file = "notes_data.json"
        self.setup_main_window()
        self.load_notes()
        
    def setup_main_window(self):
        self.main = tk.Tk()
        self.main.title("Modern Sticky Notes")
        self.main.geometry("400x500+100+100")
        self.main.configure(bg="#2b2b2b")
        self.main.resizable(True, True)
        
        # Style configuration
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Modern.TButton', 
                       background='#4a90e2', 
                       foreground='white',
                       font=('Segoe UI', 10))
        style.map('Modern.TButton',
                 background=[('active', '#357abd')])
        
        self.setup_main_ui()
        
    def setup_main_ui(self):
        # Header
        header_frame = tk.Frame(self.main, bg="#2b2b2b")
        header_frame.pack(fill="x", pady=10)
        
        title_label = tk.Label(
            header_frame,
            text="📝 Modern Sticky Notes",
            bg="#2b2b2b",
            fg="#ffffff",
            font=("Segoe UI", 18, "bold")
        )
        title_label.pack()
        
        # Control panel
        control_frame = tk.Frame(self.main, bg="#2b2b2b")
        control_frame.pack(fill="x", padx=20, pady=10)
        
        new_note_btn = ttk.Button(
            control_frame,
            text="➕ Tạo Note Mới",
            style='Modern.TButton',
            command=self.create_new_note
        )
        new_note_btn.pack(side="left", padx=5)
        
        show_all_btn = ttk.Button(
            control_frame,
            text="👁 Hiện Tất Cả",
            style='Modern.TButton',
            command=self.show_all_notes
        )
        show_all_btn.pack(side="left", padx=5)
        
        hide_all_btn = ttk.Button(
            control_frame,
            text="🙈 Ẩn Tất Cả",
            style='Modern.TButton',
            command=self.hide_all_notes
        )
        hide_all_btn.pack(side="left", padx=5)
        
        # Notes list frame
        list_frame = tk.Frame(self.main, bg="#2b2b2b")
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        tk.Label(
            list_frame,
            text="Danh Sách Notes:",
            bg="#2b2b2b",
            fg="#ffffff",
            font=("Segoe UI", 12, "bold")
        ).pack(anchor="w")
        
        # Scrollable list
        list_container = tk.Frame(list_frame, bg="#2b2b2b")
        list_container.pack(fill="both", expand=True, pady=5)
        
        self.canvas = tk.Canvas(list_container, bg="#3b3b3b", highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#3b3b3b")
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Sẵn sàng - Nhấn Ctrl+Alt+N để tạo note nhanh")
        status_bar = tk.Label(
            self.main,
            textvariable=self.status_var,
            bg="#4a4a4a",
            fg="#ffffff",
            font=("Segoe UI", 9),
            anchor="w"
        )
        status_bar.pack(fill="x", side="bottom")
        
    def create_new_note(self, preset_text=""):
        note_window = NoteWindow(self, preset_text)
        self.notes.append(note_window)
        self.note_counter += 1
        self.update_notes_list()
        self.save_notes()
        
    def update_notes_list(self):
        # Clear existing items
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
            
        for i, note in enumerate(self.notes):
            if note.window and note.window.winfo_exists():
                note_frame = tk.Frame(self.scrollable_frame, bg="#4a4a4a", relief="raised", bd=1)
                note_frame.pack(fill="x", pady=2, padx=5)
                
                # Note preview
                preview_text = note.text_widget.get("1.0", "1.20") + "..." if len(note.text_widget.get("1.0", "end-1c")) > 20 else note.text_widget.get("1.0", "end-1c")
                
                info_frame = tk.Frame(note_frame, bg="#4a4a4a")
                info_frame.pack(fill="x", padx=5, pady=3)
                
                tk.Label(
                    info_frame,
                    text=f"Note #{i+1}",
                    bg="#4a4a4a",
                    fg="#ffffff",
                    font=("Segoe UI", 10, "bold")
                ).pack(anchor="w")
                
                tk.Label(
                    info_frame,
                    text=preview_text,
                    bg="#4a4a4a",
                    fg="#cccccc",
                    font=("Segoe UI", 9),
                    wraplength=300
                ).pack(anchor="w")
                
                # Buttons
                btn_frame = tk.Frame(note_frame, bg="#4a4a4a")
                btn_frame.pack(fill="x", padx=5, pady=3)
                
                show_btn = tk.Button(
                    btn_frame,
                    text="👁",
                    bg="#4a90e2",
                    fg="white",
                    font=("Segoe UI", 8),
                    width=3,
                    command=lambda n=note: n.show_window()
                )
                show_btn.pack(side="left", padx=2)
                
                hide_btn = tk.Button(
                    btn_frame,
                    text="🙈",
                    bg="#f39c12",
                    fg="white",
                    font=("Segoe UI", 8),
                    width=3,
                    command=lambda n=note: n.hide_window()
                )
                hide_btn.pack(side="left", padx=2)
                
                delete_btn = tk.Button(
                    btn_frame,
                    text="🗑",
                    bg="#e74c3c",
                    fg="white",
                    font=("Segoe UI", 8),
                    width=3,
                    command=lambda n=note: self.delete_note(n)
                )
                delete_btn.pack(side="left", padx=2)
        
        self.status_var.set(f"Tổng cộng {len(self.notes)} notes")
        
    def delete_note(self, note):
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa note này?"):
            note.close_window()
            self.notes.remove(note)
            self.update_notes_list()
            self.save_notes()
    
    def show_all_notes(self):
        for note in self.notes:
            note.show_window()
            
    def hide_all_notes(self):
        for note in self.notes:
            note.hide_window()
    
    def save_notes(self):
        try:
            notes_data = []
            for note in self.notes:
                if note.window and note.window.winfo_exists():
                    notes_data.append({
                        'text': note.text_widget.get("1.0", "end-1c"),
                        'bg_color': note.bg_color,
                        'text_color': note.text_color,
                        'font_family': note.font_family,
                        'font_size': note.font_size,
                        'geometry': note.window.geometry(),
                        'created_time': getattr(note, 'created_time', datetime.now().isoformat())
                    })
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(notes_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Lỗi khi lưu: {e}")
    
    def load_notes(self):
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    notes_data = json.load(f)
                
                for data in notes_data:
                    note_window = NoteWindow(self, data['text'])
                    note_window.bg_color = data.get('bg_color', '#fffa77')
                    note_window.text_color = data.get('text_color', 'black')
                    note_window.font_family = data.get('font_family', 'Segoe UI')
                    note_window.font_size = data.get('font_size', 11)
                    note_window.created_time = data.get('created_time', datetime.now().isoformat())
                    
                    note_window.apply_styles()
                    if 'geometry' in data:
                        note_window.window.geometry(data['geometry'])
                    
                    self.notes.append(note_window)
                    
                self.update_notes_list()
        except Exception as e:
            print(f"Lỗi khi tải: {e}")
    
    def hotkey_listener(self):
        print("🚀 Modern Sticky Notes đã khởi chạy!")
        print("⌨️  Nhấn Ctrl+Alt+N để tạo note nhanh")
        print("🛑 Nhấn Esc để thoát")
        
        keyboard.add_hotkey("ctrl+alt+n", lambda: self.main.after(0, lambda: self.create_new_note()))
        keyboard.wait("esc")
        self.main.quit()
    
    def run(self):
        # Start hotkey listener in separate thread
        threading.Thread(target=self.hotkey_listener, daemon=True).start()
        self.main.mainloop()

class NoteWindow:
    def __init__(self, parent_app, initial_text=""):
        self.parent_app = parent_app
        self.bg_color = '#fffa77'
        self.text_color = 'black'
        self.font_family = 'Segoe UI'
        self.font_size = 11
        self.created_time = datetime.now().isoformat()
        
        self.create_window(initial_text)
        
    def create_window(self, initial_text):
        self.window = tk.Toplevel()
        self.window.title("📝 Sticky Note")
        self.window.geometry("350x250+200+200")
        self.window.configure(bg=self.bg_color)
        self.window.attributes("-topmost", True)
        
        # Make window resizable and modern
        self.window.resizable(True, True)
        
        # Header with controls
        header_frame = tk.Frame(self.window, bg=self.bg_color)
        header_frame.pack(fill="x", padx=5, pady=2)
        
        # Title
        self.title_var = tk.StringVar(value=f"Note - {datetime.now().strftime('%H:%M')}")
        title_label = tk.Label(
            header_frame,
            textvariable=self.title_var,
            bg=self.bg_color,
            fg=self.text_color,
            font=(self.font_family, 10, "bold")
        )
        title_label.pack(side="left")
        
        # Control buttons
        btn_frame = tk.Frame(header_frame, bg=self.bg_color)
        btn_frame.pack(side="right")
        
        # Color button
        color_btn = tk.Button(
            btn_frame,
            text="🎨",
            font=("Segoe UI", 10),
            width=2,
            command=self.change_color,
            bg="#ffffff",
            relief="flat"
        )
        color_btn.pack(side="left", padx=1)
        
        # Font button
        font_btn = tk.Button(
            btn_frame,
            text="🔤",
            font=("Segoe UI", 10),
            width=2,
            command=self.change_font,
            bg="#ffffff",
            relief="flat"
        )
        font_btn.pack(side="left", padx=1)
        
        # Pin/Unpin button
        self.pin_var = tk.BooleanVar(value=True)
        pin_btn = tk.Button(
            btn_frame,
            text="📌",
            font=("Segoe UI", 10),
            width=2,
            command=self.toggle_pin,
            bg="#ffffff",
            relief="flat"
        )
        pin_btn.pack(side="left", padx=1)
        
        # Close button
        close_btn = tk.Button(
            btn_frame,
            text="✖",
            font=("Segoe UI", 10),
            width=2,
            command=self.close_window,
            bg="#ff6b6b",
            fg="white",
            relief="flat"
        )
        close_btn.pack(side="left", padx=1)
        
        # Text area with scrollbar
        text_frame = tk.Frame(self.window, bg=self.bg_color)
        text_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.text_widget = tk.Text(
            text_frame,
            bg=self.bg_color,
            fg=self.text_color,
            font=(self.font_family, self.font_size),
            wrap="word",
            relief="flat",
            selectbackground="#4a90e2",
            insertbackground=self.text_color,
            borderwidth=0
        )
        
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.text_widget.yview)
        self.text_widget.configure(yscrollcommand=scrollbar.set)
        
        self.text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Set initial text
        if initial_text:
            self.text_widget.insert("1.0", initial_text)
        
        # Auto-save on text change
        self.text_widget.bind("<KeyRelease>", lambda e: self.parent_app.save_notes())
        
        # Status bar
        self.status_frame = tk.Frame(self.window, bg=self.bg_color, height=20)
        self.status_frame.pack(fill="x", side="bottom")
        
        self.char_count_var = tk.StringVar()
        char_label = tk.Label(
            self.status_frame,
            textvariable=self.char_count_var,
            bg=self.bg_color,
            fg=self.text_color,
            font=("Segoe UI", 8)
        )
        char_label.pack(side="right", padx=5)
        
        # Update character count
        self.update_char_count()
        self.text_widget.bind("<KeyRelease>", lambda e: self.update_char_count())
        
    def update_char_count(self):
        content = self.text_widget.get("1.0", "end-1c")
        char_count = len(content)
        word_count = len(content.split()) if content.strip() else 0
        self.char_count_var.set(f"{word_count} từ | {char_count} ký tự")
        
    def change_color(self):
        color = colorchooser.askcolor(title="Chọn màu nền")[1]
        if color:
            self.bg_color = color
            self.apply_styles()
            self.parent_app.save_notes()
            
    def change_font(self):
        font_window = tk.Toplevel(self.window)
        font_window.title("Chọn Font")
        font_window.geometry("300x200")
        font_window.transient(self.window)
        
        tk.Label(font_window, text="Font Family:").pack(pady=5)
        family_var = tk.StringVar(value=self.font_family)
        family_combo = ttk.Combobox(font_window, textvariable=family_var)
        family_combo['values'] = list(font.families())
        family_combo.pack(pady=5)
        
        tk.Label(font_window, text="Font Size:").pack(pady=5)
        size_var = tk.StringVar(value=str(self.font_size))
        size_combo = ttk.Combobox(font_window, textvariable=size_var)
        size_combo['values'] = [str(i) for i in range(8, 25)]
        size_combo.pack(pady=5)
        
        def apply_font():
            self.font_family = family_var.get()
            self.font_size = int(size_var.get())
            self.apply_styles()
            self.parent_app.save_notes()
            font_window.destroy()
            
        tk.Button(font_window, text="Áp dụng", command=apply_font).pack(pady=10)
        
    def toggle_pin(self):
        current_state = self.window.attributes("-topmost")
        self.window.attributes("-topmost", not current_state)
        
    def apply_styles(self):
        self.window.configure(bg=self.bg_color)
        self.text_widget.configure(
            bg=self.bg_color,
            fg=self.text_color,
            font=(self.font_family, self.font_size),
            insertbackground=self.text_color
        )
        
        # Update all frame backgrounds
        for widget in self.window.winfo_children():
            if isinstance(widget, tk.Frame):
                widget.configure(bg=self.bg_color)
                for child in widget.winfo_children():
                    if isinstance(child, tk.Label):
                        child.configure(bg=self.bg_color, fg=self.text_color)
        
    def show_window(self):
        if self.window:
            self.window.deiconify()
            self.window.lift()
            
    def hide_window(self):
        if self.window:
            self.window.withdraw()
            
    def close_window(self):
        if self.window:
            self.window.destroy()

# Run the application
if __name__ == "__main__":
    app = ModernStickyNotes()
    app.run()