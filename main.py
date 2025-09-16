import tkinter as tk
from tkinter import ttk, messagebox
import keyboard
import threading
import json
import os
from datetime import datetime, timedelta
import winsound
from tkcalendar import DateEntry
import random

CATEGORIES = ["Code", "Edit", "Ghi nhớ", "Giải trí", "Nhật ký", "Ý tưởng"]
STATUS_OPTIONS = ["Chưa hoàn thành", "Đang làm", "Hoàn thành"]


class ModernStickyNotes:

    def __init__(self):
        self.notes = []
        self.note_counter = 0
        self.data_file = "notes_data.json"
        # Khởi tạo biến cho đồng hồ đếm ngược (10 phút = 600 giây)
        self.countdown_time = 600  # Biến lưu thời gian đếm ngược, đơn vị giây
        self.is_countdown_alert_active = False

        self.last_note_time = None  # Thời gian note cuối cùng
        self.dialogues_file = "imouto_dialogues.json"
        self.dialogues = self.load_dialogues()  # Load thoại từ file

        self.note_widgets = {}  # Dictionary lưu trữ note -> {'frame': note_frame, 'info_frame': info_frame}
        self.setup_main_window()
        self.load_notes()

    def load_dialogues(self):
        try:
            if os.path.exists(self.dialogues_file):
                with open(self.dialogues_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                print(
                    f"File {self.dialogues_file} không tồn tại. Sử dụng thoại mặc định."
                )
                return {}  # Hoặc return dict mặc định nếu cần
        except Exception as e:
            print(f"Lỗi load dialogues: {e}")
            return {}
        
    def evaluate_user_behavior(self):
        today = datetime.now().date()
        today_notes = [n for n in self.notes if datetime.fromisoformat(n.created_time).date() == today]
        
        # Số lượng note hôm nay
        note_count = len(today_notes)
        if note_count > 5:
            count_score = 2  # Siêng
        elif note_count >= 3:
            count_score = 1  # Trung lập
        else:
            count_score = -2  # Lười
        
        # Khoảng thời gian không note
        time_score = 0
        if self.last_note_time:
            time_diff = (datetime.now() - self.last_note_time).total_seconds() / 60  # Phút
            if time_diff < 10:
                time_score = 2  # Siêng
            elif time_diff <= 30:
                time_score = 0  # Trung lập
            else:
                time_score = -2  # Lười
        
        # Tỷ lệ chủ đề
        theme_score = 0
        if today_notes:
            entertainment_count = sum(1 for n in today_notes if getattr(n, 'category', '') == 'Giải trí')
            entertainment_ratio = entertainment_count / note_count
            if entertainment_ratio > 0.5:
                theme_score = -2  # Quá nhiều giải trí -> lười
            elif entertainment_count < note_count / 2:
                theme_score = 2  # Ít giải trí -> siêng
        
        # Tổng điểm và chọn loại thoại
        total_score = count_score + time_score + theme_score
        if total_score >= 4:
            return "sweet"
        elif total_score >= 2:
            return "encouraging"
        elif total_score >= 0:
            return "teasing"
        elif total_score >= -2:
            return "angry"
        else:
            return "sad"

    def setup_main_window(self):
        self.main = tk.Tk()
        self.main.title("Modern Sticky Notes")
        self.main.geometry("450x570+700+100")
        self.main.configure(bg="#2b2b2b")
        self.main.resizable(True, True)

        # Style configuration
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Modern.TButton",
            background="#4a90e2",
            foreground="white",
            font=("Segoe UI", 10),
        )
        style.map("Modern.TButton", background=[("active", "#357abd")])

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
            font=("Segoe UI", 18, "bold"),
        )
        title_label.pack()

        # Control panel
        # Control panel
        control_frame = tk.Frame(self.main, bg="#2b2b2b")
        control_frame.pack(fill="x", padx=20, pady=5)

        new_note_btn = ttk.Button(
            control_frame,
            text="➕ Tạo Note Mới",
            style="Modern.TButton",
            command=self.create_new_note,
        )
        new_note_btn.pack(side="left", padx=2)

        show_all_btn = ttk.Button(
            control_frame,
            text="👁 Hiện ALL",
            style="Modern.TButton",
            command=self.show_all_notes,
        )
        show_all_btn.pack(side="left", padx=2)

        hide_all_btn = ttk.Button(
            control_frame,
            text="👁 Ẩn ALL",
            style="Modern.TButton",
            command=self.hide_all_notes,
        )
        hide_all_btn.pack(side="left", padx=2)

        # New frame for schedule buttons
        new_control_frame = tk.Frame(self.main, bg="#2b2b2b")
        new_control_frame.pack(fill="x", padx=20, pady=5)

        save_schedule_btn = ttk.Button(
            new_control_frame,
            text="📅 Lưu TKB",
            style="Modern.TButton",
            command=self.save_schedule,
        )
        save_schedule_btn.pack(side="left", padx=2)

        view_schedule_btn = ttk.Button(
            new_control_frame,
            text="👀 Xem TKB",
            style="Modern.TButton",
            command=self.view_schedule,
        )
        view_schedule_btn.pack(side="left", padx=2)

        # Notes list frame
        list_frame = tk.Frame(self.main, bg="#2b2b2b")
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)

        filter_frame = tk.Frame(self.main, bg="#2b2b2b")
        filter_frame.pack(fill="x", padx=20)

        tk.Label(filter_frame, text="Tiến độ:", bg="#2b2b2b", fg="white").pack(
            side="left", padx=2
        )
        self.status_filter_var = tk.StringVar(value="Tất cả")
        status_filter_box = ttk.Combobox(
            filter_frame,
            textvariable=self.status_filter_var,
            values=["Tất cả"] + STATUS_OPTIONS,
            width=10,
        )
        status_filter_box.pack(side="left", padx=2)
        status_filter_box.bind(
            "<<ComboboxSelected>>", lambda e: self.update_notes_list()
        )

        tk.Label(filter_frame, text="Chủ đề:", bg="#2b2b2b", fg="white").pack(
            side="left"
        )

        self.filter_var = tk.StringVar(value="Tất cả")
        filter_box = ttk.Combobox(
            filter_frame,
            textvariable=self.filter_var,
            values=["Tất cả"] + CATEGORIES,
            width=10,
        )
        filter_box.pack(side="left", padx=2)
        filter_box.bind("<<ComboboxSelected>>", lambda e: self.update_notes_list())

        # Thêm lọc theo thời gian
        # Thêm chọn ngày cụ thể
        tk.Label(filter_frame, text="Ngày:", bg="#2b2b2b", fg="white").pack(
            side="left", padx=2
        )
        self.date_filter = DateEntry(
            filter_frame,
            width=10,
            background="darkblue",
            foreground="white",
            borderwidth=2,
            date_pattern="dd/mm/yyyy",
        )
        self.date_filter.pack(side="left", padx=2)
        self.date_filter.bind(
            "<<DateEntrySelected>>", lambda e: self.update_notes_list()
        )

        tk.Label(
            list_frame,
            text="Danh Sách Notes:",
            bg="#2b2b2b",
            fg="#ffffff",
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w")

        # THÊM ĐỒNG HỒ: Frame để chứa đồng hồ hiện tại và đếm ngược (dán code vào đây trong setup_main_ui, sau phần filter)
        clock_frame = tk.Frame(list_frame, bg="#2b2b2b")
        clock_frame.pack(fill="x", pady=5)

        # Label cho đồng hồ hiện tại
        self.current_time_label = tk.Label(
            clock_frame,
            text="Giờ hiện tại: ",
            bg="#2b2b2b",
            fg="#00ff00",
            font=("Segoe UI", 10, "bold"),
        )
        self.current_time_label.pack(side="left", padx=10)

        # Label cho đồng hồ đếm ngược
        self.countdown_label = tk.Label(
            clock_frame,
            text="Đếm ngược: ",
            bg="#2b2b2b",
            fg="#ff0000",
            font=("Segoe UI", 10, "bold"),
        )
        self.countdown_label.pack(side="right", padx=10)

        # Bắt đầu cập nhật đồng hồ (gọi hàm update_clocks để bắt đầu)
        self.update_clocks()

        # Scrollable list
        list_container = tk.Frame(list_frame, bg="#2b2b2b")
        list_container.pack(fill="both", expand=True, pady=5)

        self.canvas = tk.Canvas(list_container, bg="#3b3b3b", highlightthickness=0)
        scrollbar = ttk.Scrollbar(
            list_container, orient="vertical", command=self.canvas.yview
        )
        self.scrollable_frame = tk.Frame(self.canvas, bg="#3b3b3b")

        # Khi nội dung bên trong thay đổi kích thước → tự cập nhật vùng scroll
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
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
            anchor="w",
        )
        status_bar.pack(fill="x", side="bottom")

    def create_new_note(self, preset_text=""):
        note_window = NoteWindow(self, preset_text)
        note_window.category = CATEGORIES[0]
        self.last_note_time = datetime.now()  # Cập nhật thời gian note cuối
        note_window.create_window(preset_text)  # Gọi create_window cho note mới
        self.notes.append(note_window)
        self.note_counter += 1
        self.update_notes_list()
        self.save_notes()
        self.reset_countdown()

    def update_notes_list(self):
        # Lọc danh sách note còn tồn tại
        self.notes = [
            note
            for note in self.notes
            if note.window
            and note.window.winfo_exists()
            and hasattr(note, "text_widget")
            and note.text_widget.winfo_exists()
        ]

        # Lấy tất cả notes để sắp xếp
        notes_to_show = self.notes[:]

        selected_cat = self.filter_var.get()
        selected_status = self.status_filter_var.get()
        selected_date = self.date_filter.get_date()  # Lấy ngày từ DateEntry

        def get_priority_cat(n):
            if selected_cat == "Tất cả":
                return 0
            return 0 if getattr(n, "category", "Ghi nhớ") == selected_cat else 1

        def get_priority_status(n):
            if selected_status == "Tất cả":
                return 0
            return (
                0 if getattr(n, "status", "Chưa hoàn thành") == selected_status else 1
            )

        def get_priority_date(n):
            dt = datetime.fromisoformat(n.created_time).date()
            return 0 if dt == selected_date else 1

        # Sắp xếp với ưu tiên: ngày được chọn -> chủ đề -> tiến độ -> thời gian tạo (mới nhất trước)
        notes_to_show.sort(
            key=lambda n: (
                get_priority_date(n),  # Ưu tiên ngày được chọn
                get_priority_cat(n),
                get_priority_status(n),
                -datetime.fromisoformat(n.created_time).timestamp(),  # Mới nhất trước
            )
        )

        # Tạo set các note hiện tại để so sánh
        current_notes = set(notes_to_show)
        existing_notes = set(self.note_widgets.keys())

        # Xóa widget của các note không còn hiển thị
        for note in existing_notes - current_notes:
            if note in self.note_widgets:
                self.note_widgets[note]["frame"].destroy()
                del self.note_widgets[note]

        # Cập nhật hoặc tạo widget mới
        for i, note in enumerate(notes_to_show):
            preview_text = "(Trống)"
            if note.text_widget and note.text_widget.winfo_exists():
                content = note.text_widget.get("1.0", "end-1c")
                preview_text = content[:20] + "..." if len(content) > 20 else content

            dt = datetime.fromisoformat(note.created_time)
            days_vi = [
                "Thứ Hai",
                "Thứ Ba",
                "Thứ Tư",
                "Thứ Năm",
                "Thứ Sáu",
                "Thứ Bảy",
                "Chủ Nhật",
            ]
            thu = days_vi[dt.weekday()]
            ngay_thang_nam_gio = dt.strftime("%d/%m/%Y %H:%M")

            if note in self.note_widgets:
                note_frame = self.note_widgets[note]["frame"]
                info_frame = self.note_widgets[note]["info_frame"]
                note_frame.grid(row=i // 2, column=i % 2, padx=5, pady=5, sticky="nsew")
                labels = [
                    w for w in info_frame.winfo_children() if isinstance(w, tk.Label)
                ]
                if len(labels) >= 5:
                    labels[0].config(text=f"Note #{notes_to_show.index(note)+1}")
                    labels[1].config(text=preview_text or "(Trống)")
                    labels[2].config(text=f"[{getattr(note, 'category', 'Ghi nhớ')}]")
                    labels[3].config(
                        text=f"Tiến độ: {getattr(note, 'status', 'Chưa hoàn thành')}"
                    )
                    labels[4].config(text=f"Tạo: {thu}, {ngay_thang_nam_gio}")
                else:
                    print(
                        f"Warning: note_frame for note #{notes_to_show.index(note)+1} has only {len(labels)} labels"
                    )
            else:
                note_frame = tk.Frame(
                    self.scrollable_frame,
                    bg="#4a4a4a",
                    relief="raised",
                    bd=1,
                    width=180,
                    height=120,
                )
                note_frame.grid(row=i // 2, column=i % 2, padx=5, pady=5, sticky="nsew")
                note_frame.grid_propagate(False)

                info_frame = tk.Frame(note_frame, bg="#4a4a4a")
                info_frame.pack(fill="x", padx=5, pady=3)

                tk.Label(
                    info_frame,
                    text=f"Note #{i+1}",
                    bg="#4a4a4a",
                    fg="#ffffff",
                    font=("Segoe UI", 10, "bold"),
                ).pack(anchor="w")

                tk.Label(
                    info_frame,
                    text=preview_text or "(Trống)",
                    bg="#4a4a4a",
                    fg="#cccccc",
                    font=("Segoe UI", 9),
                    wraplength=160,
                ).pack(anchor="w")

                tk.Label(
                    info_frame,
                    text=f"[{getattr(note, 'category', 'Ghi nhớ')}]",
                    bg="#4a4a4a",
                    fg="#ffcc00",
                    font=("Segoe UI", 9, "italic"),
                ).pack(anchor="w")

                tk.Label(
                    info_frame,
                    text=f"Tiến độ: {getattr(note, 'status', 'Chưa hoàn thành')}",
                    bg="#4a4a4a",
                    fg="#00ff00",
                    font=("Segoe UI", 8),
                ).pack(anchor="w")

                tk.Label(
                    info_frame,
                    text=f"Tạo: {thu}, {ngay_thang_nam_gio}",
                    bg="#4a4a4a",
                    fg="#00ff00",
                    font=("Segoe UI", 8),
                ).pack(anchor="w")

                btn_frame = tk.Frame(note_frame, bg="#4a4a4a")
                btn_frame.pack(fill="x", padx=5, pady=3)

                tk.Button(
                    btn_frame,
                    text="👁",
                    bg="#4a90e2",
                    fg="white",
                    font=("Segoe UI", 8),
                    width=3,
                    command=lambda n=note: n.show_window(),
                ).pack(side="left", padx=2)

                tk.Button(
                    btn_frame,
                    text="👁",
                    bg="#f39c12",
                    fg="white",
                    font=("Segoe UI", 8),
                    width=3,
                    command=lambda n=note: n.hide_window(),
                ).pack(side="left", padx=2)

                tk.Button(
                    btn_frame,
                    text="🗑",
                    bg="#e74c3c",
                    fg="white",
                    font=("Segoe UI", 8),
                    width=3,
                    command=lambda n=note: self.delete_note(n),
                ).pack(side="left", padx=2)

                self.note_widgets[note] = {
                    "frame": note_frame,
                    "info_frame": info_frame,
                }

        self.scrollable_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.status_var.set(f"Tổng cộng {len(notes_to_show)} notes đã sắp xếp")

    def delete_note(self, note):
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa note này?"):
            note.close_window()
            if note in self.notes:
                self.notes.remove(note)
            if note in self.note_widgets:
                self.note_widgets[note]["frame"].destroy()
                del self.note_widgets[note]
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
                    notes_data.append(
                        {
                            "text": note.text_widget.get("1.0", "end-1c"),
                            "category": getattr(note, "category", "Ghi nhớ"),
                            "status": getattr(note, "status", "Chưa hoàn thành"),
                            "geometry": note.window.geometry(),
                            "created_time": getattr(
                                note, "created_time", datetime.now().isoformat()
                            ),
                        }
                    )

            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(notes_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Lỗi khi lưu: {e}")

    def load_notes(self):
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, "r", encoding="utf-8") as f:
                    notes_data = json.load(f)

                for data in notes_data:
                    # print(f"[load_notes] Đọc created_time từ database: {data.get('created_time', 'Không có')}")
                    note_window = NoteWindow(self, data["text"])
                    note_window.category = data.get("category", "Ghi nhớ")
                    note_window.status = data.get("status", "Chưa hoàn thành")
                    try:
                        dt = datetime.fromisoformat(
                            data.get("created_time", datetime.now().isoformat())
                        )
                        note_window.created_time = dt.isoformat()
                        # print(f"[load_notes] Gán created_time cho note: {note_window.created_time}")
                    except ValueError as ve:
                        # print(f"[load_notes] Lỗi parse created_time: {ve}. Sử dụng thời gian hiện tại.")
                        note_window.created_time = datetime.now().isoformat()
                        # print(f"[load_notes] Fallback created_time: {note_window.created_time}")

                    note_window.create_window(data["text"])  # Gọi create_window trước
                    # print(f"[load_notes] Đã tạo window: {note_window.window is not None}")
                    note_window.update_colors_based_on_status()
                    note_window.apply_styles()
                    note_window.update_category_combo()
                    note_window.update_status_combo()
                    if "geometry" in data:
                        note_window.window.geometry(data["geometry"])
                    note_window.hide_window()  # Ẩn note ngay sau khi tạo

                    self.notes.append(note_window)

                self.update_notes_list()
        except Exception as e:
            print(f"[load_notes] Lỗi khi tải: {e}")

    # HÀM MỚI: Cập nhật đồng hồ hiện tại và đếm ngược (dán hàm này vào class ModernStickyNotes, sau load_notes)
    def update_clocks(self):
        # Cập nhật giờ hiện tại
        current_time = datetime.now().strftime("%H:%M:%S")
        self.current_time_label.config(text=f"Giờ hiện tại: {current_time}")

        # Cập nhật đếm ngược
        minutes, seconds = divmod(self.countdown_time, 60)
        countdown_str = f"{minutes:02d}:{seconds:02d}"
        self.countdown_label.config(text=f"Đếm ngược: {countdown_str}")

        # Giảm thời gian đếm ngược
        if self.countdown_time > 0:
            self.countdown_time -= 1
        else:
            if not self.is_countdown_alert_active:
                self.handle_countdown_zero()

        # Lặp lại sau 1 giây (1000 ms)
        self.main.after(1000, self.update_clocks)

    # HÀM MỚI: Xử lý khi đếm ngược về 0 (dán hàm này vào class, sau update_clocks)
    def handle_countdown_zero(self):
        self.is_countdown_alert_active = True
        self.main.lift()
        self.main.deiconify()
        self.main.focus_force()
        try:
            winsound.Beep(1000, 500)
        except:
            print("Không thể phát âm thanh")

        # Đánh giá hành vi và chọn loại thoại
        dialogue_type = self.evaluate_user_behavior()

        # Nhắc nhở chính
        reminder_dialogues = self.dialogues.get("reminder", {}).get(dialogue_type, ["Onii-chan, đã đến lúc viết note! Bạn có muốn tạo note mới không? (≧▽≦)"])
        reminder_msg = random.choice(reminder_dialogues)

        response = messagebox.askyesno(
            "Nhắc nhở",
            reminder_msg,
            parent=self.main,
        )
        if response:
            self.create_new_note()
        else:
            # Cảnh báo 1: Thái độ
            attitude_dialogues = self.dialogues.get("attitude_warning", {}).get(dialogue_type, ["Onii-chan đang phớt lờ em! Viết note đi nha~ (¬‿¬)"])
            messagebox.showwarning(
                "Cảnh báo thái độ",
                random.choice(attitude_dialogues),
                parent=self.main,
            )
            # Cảnh báo cuối: Chức năng (nhắc sẽ lặp lại sau 1 phút)
            final_dialogues = self.dialogues.get("final_warning", {}).get(dialogue_type, ["Em sẽ nhắc lại sau 1 phút để onii-chan viết note! (´；ω；`)"])
            messagebox.showerror(
                "Cảnh báo cuối",
                random.choice(final_dialogues),
                parent=self.main,
            )
            self.countdown_time = 60  # Reset về 1 phút để nhắc lại

        self.is_countdown_alert_active = False

    def reset_countdown(self):
        self.countdown_time = 600  # Reset về 10 phút

    def save_schedule(self):
        selected_date = self.date_filter.get_date()
        selected_notes = [
            n
            for n in self.notes
            if datetime.fromisoformat(n.created_time).date() == selected_date
        ]

        if not selected_notes:
            messagebox.showinfo(
                "Thông báo",
                f"Không có note nào vào ngày {selected_date.strftime('%d/%m/%Y')} để lưu thời khóa biểu.",
            )
            return

        selected_notes.sort(key=lambda n: datetime.fromisoformat(n.created_time))

        schedule_content = f"Thời Khóa Biểu Ngày {selected_date.strftime('%d/%m/%Y')}\n"
        schedule_content += "-" * 50 + "\n\n"

        for note in selected_notes:
            dt = datetime.fromisoformat(note.created_time)
            time_str = dt.strftime("%H:%M")
            category = getattr(note, "category", "Ghi nhớ")
            status = getattr(note, "status", "Chưa hoàn thành")
            content = (
                note.text_widget.get("1.0", "end-1c").strip()[:50] + "..."
                if len(note.text_widget.get("1.0", "end-1c").strip()) > 50
                else note.text_widget.get("1.0", "end-1c").strip()
            )
            schedule_content += f"{time_str} - [{category}] ({status}): {content}\n\n"

        file_name = f"schedule_{selected_date.strftime('%Y-%m-%d')}.txt"
        try:
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(schedule_content)
            messagebox.showinfo(
                "Thành công", f"Đã lưu thời khóa biểu vào file: {file_name}"
            )
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi khi lưu file: {e}")

    def view_schedule(self):
        selected_date = self.date_filter.get_date()
        selected_notes = [
            n
            for n in self.notes
            if datetime.fromisoformat(n.created_time).date() == selected_date
        ]

        if not selected_notes:
            messagebox.showinfo(
                "Thông báo",
                f"Không có note nào vào ngày {selected_date.strftime('%d/%m/%Y')} để hiển thị.",
            )
            return

        selected_notes.sort(key=lambda n: datetime.fromisoformat(n.created_time))

        schedule_content = f"Thời Khóa Biểu Ngày {selected_date.strftime('%d/%m/%Y')}\n"
        schedule_content += "-" * 50 + "\n\n"

        for note in selected_notes:
            dt = datetime.fromisoformat(note.created_time)
            time_str = dt.strftime("%H:%M")
            category = getattr(note, "category", "Ghi nhớ")
            status = getattr(note, "status", "Chưa hoàn thành")
            content = (
                note.text_widget.get("1.0", "end-1c").strip()[:50] + "..."
                if len(note.text_widget.get("1.0", "end-1c").strip()) > 50
                else note.text_widget.get("1.0", "end-1c").strip()
            )
            schedule_content += f"{time_str} - [{category}] ({status}): {content}\n\n"

        schedule_window = tk.Toplevel(self.main)
        schedule_window.title(f"Thời Khóa Biểu - {selected_date.strftime('%d/%m/%Y')}")
        schedule_window.geometry("400x400")
        schedule_window.configure(bg="#2b2b2b")

        text_widget = tk.Text(
            schedule_window,
            bg="#3b3b3b",
            fg="#ffffff",
            font=("Segoe UI", 10),
            wrap="word",
            relief="flat",
            borderwidth=0,
        )
        text_widget.pack(fill="both", expand=True, padx=10, pady=10)
        text_widget.insert("1.0", schedule_content)
        text_widget.config(state="disabled")

    def hotkey_listener(self):
        # print("🚀 Modern Sticky Notes đã khởi chạy!")
        # print("⌨️  Nhấn Ctrl+Alt+N để tạo note nhanh")
        # print("🛑 Nhấn Esc để thoát")

        keyboard.add_hotkey(
            "ctrl+alt+n", lambda: self.main.after(0, lambda: self.create_new_note())
        )
        keyboard.wait("esc")
        self.main.quit()

    def run(self):
        # Start hotkey listener in separate thread
        threading.Thread(target=self.hotkey_listener, daemon=True).start()
        self.main.mainloop()


class NoteWindow:
    def __init__(self, parent_app, initial_text=""):
        self.parent_app = parent_app
        self.bg_color = "#fffa77"  # Mặc định, sẽ được cập nhật bởi status
        self.text_color = "black"
        self.font_family = "Roboto"
        self.font_size = 11
        self.created_time = datetime.now().isoformat()
        # print(f"[__init__] Khởi tạo self.created_time: {self.created_time}")
        self.category = "Ghi nhớ"  # Mặc định chủ đề
        self.status = "Chưa hoàn thành"  # Mặc định tiến độ
        self.window = None
        self.text_widget = None

        self.update_colors_based_on_status()  # Gọi sau khi status được khởi tạo

    def update_colors_based_on_status(self):
        # Định nghĩa màu dựa trên status
        if self.status == "Chưa hoàn thành":
            self.bg_color = "#fffa77"  # Vàng nhạt
            self.text_color = "black"
        elif self.status == "Đang làm":
            self.bg_color = "#ffa500"  # Cam
            self.text_color = "black"
        elif self.status == "Hoàn thành":
            self.bg_color = "#90ee90"  # Xanh lá nhạt
            self.text_color = "black"
        else:
            self.bg_color = "#fffa77"  # Default
            self.text_color = "black"

    def close_window(self):
        if self.window:
            self.window.destroy()
            if self in self.parent_app.notes:
                self.parent_app.notes.remove(self)
                self.parent_app.update_notes_list()
                self.parent_app.save_notes()

    def create_window(self, initial_text):
        # print(f"[create_window] Giá trị self.created_time trước khi hiển thị: {self.created_time}")
        self.window = tk.Toplevel()
        self.window.title("📝 Sticky Note")
        self.window.geometry("520x70+0+0")
        self.window.overrideredirect(True)  # Bỏ thanh tiêu đề
        self.window.configure(bg=self.bg_color)
        self.window.attributes("-topmost", True)

        self.window.resizable(True, True)

        self.update_colors_based_on_status()
        self.window.configure(bg=self.bg_color)

        header_frame = tk.Frame(self.window, bg=self.bg_color)
        header_frame.pack(fill="x", padx=5, pady=2)

        # Nút kéo di chuyển
        self.drag_start_x = 0
        self.drag_start_y = 0

        def start_drag(event):
            self.drag_start_x = event.x_root - self.window.winfo_x()
            self.drag_start_y = event.y_root - self.window.winfo_y()

        def do_drag(event):
            x = event.x_root - self.drag_start_x
            y = event.y_root - self.drag_start_y
            self.window.geometry(f"+{x}+{y}")

        def stop_drag(event):
            self.drag_start_x = 0
            self.drag_start_y = 0

        drag_btn = tk.Button(
            header_frame,
            text="↔",
            font=("Roboto", 10),
            width=2,
            command=lambda: None,  # Không cần lệnh, chỉ để kéo
            bg="#00536b",
            fg="white",
            relief="flat",
        )
        drag_btn.pack(side="left", padx=1)
        drag_btn.bind("<Button-1>", start_drag)
        drag_btn.bind("<B1-Motion>", do_drag)
        drag_btn.bind("<ButtonRelease-1>", stop_drag)

        # Tiêu đề và thời gian
        dt = datetime.fromisoformat(self.created_time)
        days_vi = [
            "Thứ Hai",
            "Thứ Ba",
            "Thứ Tư",
            "Thứ Năm",
            "Thứ Sáu",
            "Thứ Bảy",
            "Chủ Nhật",
        ]
        thu = days_vi[dt.weekday()]
        ngay_thang_nam_gio = dt.strftime("%d/%m/%Y %H:%M")
        title_text = f"Note - {thu}, {ngay_thang_nam_gio}"
        # print(f"[create_window] Tiêu đề hiển thị: {title_text}")

        self.title_var = tk.StringVar(value=title_text)
        title_label = tk.Label(
            header_frame,
            textvariable=self.title_var,
            bg=self.bg_color,
            fg=self.text_color,
            font=("Roboto", 10, "bold"),
        )
        title_label.pack(side="left")

        self.category_var = tk.StringVar(value=self.category)
        category_combo = ttk.Combobox(
            header_frame, textvariable=self.category_var, values=CATEGORIES, width=10
        )
        category_combo.pack(side="left", padx=5)
        category_combo.bind("<<ComboboxSelected>>", self.on_category_change)

        self.status_var = tk.StringVar(value=self.status)
        status_combo = ttk.Combobox(
            header_frame, textvariable=self.status_var, values=STATUS_OPTIONS, width=12
        )
        status_combo.pack(side="left", padx=5)
        status_combo.bind("<<ComboboxSelected>>", self.on_status_change)

        btn_frame = tk.Frame(header_frame, bg=self.bg_color)
        btn_frame.pack(side="right")

        self.pin_var = tk.BooleanVar(value=True)
        pin_btn = tk.Button(
            btn_frame,
            text="📌",
            font=("Roboto", 10),
            width=2,
            command=self.toggle_pin,
            bg="#ffffff",
            relief="flat",
        )
        pin_btn.pack(side="left", padx=1)

        hide_btn = tk.Button(
            btn_frame,
            text="👁",
            font=("Roboto", 10),
            width=2,
            command=self.hide_window,
            bg="#f39c12",
            fg="white",
            relief="flat",
        )
        hide_btn.pack(side="left", padx=1)

        close_btn = tk.Button(
            btn_frame,
            text="✖",
            font=("Roboto", 10),
            width=2,
            command=self.close_window,
            bg="#ff6b6b",
            fg="white",
            relief="flat",
        )
        close_btn.pack(side="left", padx=1)

        text_frame = tk.Frame(self.window, bg=self.bg_color)
        text_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.text_widget = tk.Text(
            text_frame,
            bg=self.bg_color,
            fg=self.text_color,
            font=("Roboto", 11),
            wrap="word",
            relief="flat",
            selectbackground="#4a90e2",
            insertbackground=self.text_color,
            borderwidth=0,
        )

        scrollbar = ttk.Scrollbar(
            text_frame, orient="vertical", command=self.text_widget.yview
        )
        self.text_widget.configure(yscrollcommand=scrollbar.set)

        self.text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        if initial_text:
            self.text_widget.insert("1.0", initial_text)

        self.text_widget.bind(
            "<KeyRelease>",
            lambda e: (
                self.update_char_count(),
                self.parent_app.save_notes(),
                self.parent_app.update_notes_list(),
            ),
        )

        self.status_frame = tk.Frame(self.window, bg=self.bg_color, height=20)
        self.status_frame.pack(fill="x", side="bottom")

        self.char_count_var = tk.StringVar()
        char_label = tk.Label(
            self.status_frame,
            textvariable=self.char_count_var,
            bg=self.bg_color,
            fg=self.text_color,
            font=("Roboto", 8),
        )
        char_label.pack(side="right", padx=5)

        self.update_char_count()
        # Đặt con trỏ vào ô văn bản ngay khi tạo note
        self.text_widget.focus_set()

    def on_category_change(self, event):
        self.category = self.category_var.get()
        self.parent_app.save_notes()
        self.parent_app.update_notes_list()  # Cập nhật danh sách khi thay đổi chủ đề

    def on_status_change(self, event):
        self.status = self.status_var.get()
        self.update_colors_based_on_status()  # Cập nhật màu dựa trên status mới
        self.apply_styles()  # Áp dụng style mới
        self.parent_app.save_notes()
        self.parent_app.update_notes_list()

    def update_category_combo(self):
        self.category_var.set(self.category)  # Cập nhật combobox khi load

    def update_status_combo(self):
        if hasattr(self, "status_var"):
            self.status_var.set(self.status)

    def update_char_count(self):
        content = self.text_widget.get("1.0", "end-1c")
        char_count = len(content)
        word_count = len(content.split()) if content.strip() else 0
        self.char_count_var.set(f"{word_count} từ | {char_count} ký tự")

    def toggle_pin(self):
        current_state = self.window.attributes("-topmost")
        self.window.attributes("-topmost", not current_state)

    def apply_styles(self):
        # print(f"[apply_styles] Kiểm tra: self.window = {self.window is not None}, self.text_widget = {self.text_widget is not None}")
        if self.window and self.text_widget:
            self.window.configure(bg=self.bg_color)
            self.text_widget.configure(
                bg=self.bg_color,
                fg=self.text_color,
                font=("Roboto", 11),
                insertbackground=self.text_color,
            )

            for widget in self.window.winfo_children():
                if isinstance(widget, tk.Frame):
                    widget.configure(bg=self.bg_color)
                    for child in widget.winfo_children():
                        if isinstance(child, tk.Label):
                            child.configure(bg=self.bg_color, fg=self.text_color)
        else:
            print("[apply_styles] Lỗi: self.window hoặc self.text_widget là None")

    def show_window(self):
        if self.window:
            self.window.deiconify()
            self.window.lift()

    def hide_window(self):
        if self.window:
            self.window.withdraw()


# Run the application
if __name__ == "__main__":
    app = ModernStickyNotes()
    app.run()
