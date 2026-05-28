import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from datetime import datetime
import re

# Импортируем твои модули
from db_connect import ConnMang
import capi

class BackupManagerWindow(tk.Toplevel):
    """Второе окно: открывается для управления конкретной игрой."""
    def __init__(self, parent, game_id, game_name):
        super().__init__(parent)
        self.parent = parent
        self.game_id = game_id
        self.game_name = game_name

        self.title(f"Управление бэкапами — {self.game_name}")
        self.geometry("650x450")
        self.minsize(550, 350)

        self.transient(parent)
        self.grab_set()

        paths = self.parent.db.get_game_paths(self.game_id)
        self.game_path = paths[0] if paths else "Путь отсутствует"

        self.build_ui()
        self.refresh_backups_list()

    def build_ui(self):
        info_frame = ttk.Frame(self, padding=15)
        info_frame.pack(fill=tk.X)

        ttk.Label(info_frame, text=self.game_name, font=("Segoe UI", 14, "bold"), foreground="#2980b9").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Путь на диске: {self.game_path}", font=("Segoe UI", 9), foreground="#7f8c8d", wraplength=600).pack(anchor=tk.W, pady=(5, 0))

        table_frame = ttk.Frame(self, padding=(15, 0))
        table_frame.pack(fill=tk.BOTH, expand=True)

        self.backup_tree = ttk.Treeview(table_frame, columns=("id", "time"), show="headings", selectmode="browse")
        self.backup_tree.heading("id", text="ID Бэкапа")
        self.backup_tree.heading("time", text="Дата и время создания резервной копии")
        self.backup_tree.column("id", width=80, stretch=tk.NO, anchor=tk.CENTER)
        self.backup_tree.column("time", width=400, stretch=tk.YES)

        scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.backup_tree.yview)
        self.backup_tree.configure(yscrollcommand=scroll.set)

        self.backup_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.backup_tree.bind("<<TreeviewSelect>>", lambda e: self.btn_restore.state(["!disabled"]) or self.btn_delete.state(["!disabled"]))

        actions_frame = ttk.Frame(self, padding=15)
        actions_frame.pack(fill=tk.X, side=tk.BOTTOM)

        ttk.Button(actions_frame, text="💾 Создать новый бэкап", style="Accent.TButton", command=self.create_backup).pack(side=tk.LEFT, padx=3, expand=True, fill=tk.X)

        self.btn_restore = ttk.Button(actions_frame, text="🔄 Восстановить выбранный", command=self.restore_backup)
        self.btn_restore.pack(side=tk.LEFT, padx=3, expand=True, fill=tk.X)
        self.btn_restore.state(["disabled"])

        self.btn_delete = ttk.Button(actions_frame, text="❌ Удалить точку", command=self.delete_backup)
        self.btn_delete.pack(side=tk.LEFT, padx=3, expand=True, fill=tk.X)
        self.btn_delete.state(["disabled"])

    def refresh_backups_list(self):
        for row in self.backup_tree.get_children():
            self.backup_tree.delete(row)

        backups = self.parent.db.get_backups_by_game(self.game_id)
        for b_id, b_time in backups:
            time_str = b_time.strftime("%Y-%m-%d %H:%M:%S") if hasattr(b_time, "strftime") else str(b_time)
            self.backup_tree.insert("", tk.END, values=(b_id, time_str))

        self.btn_restore.state(["disabled"])
        self.btn_delete.state(["disabled"])

    def create_backup(self):
        if self.game_path == "Путь отсутствует": return
        self.parent.log(f"Запуск резервного копирования для '{self.game_name}'...")

        success = capi.do_single_game_backup(self.game_id, self.game_path)
        if success:
            self.parent.log(f"УСПЕХ: Новая точка бэкапа для '{self.game_name}' сохранена в БД.")
            self.refresh_backups_list()
        else:
            self.parent.log("ОШИБКА: Не удалось упаковать файлы через DLL.")
            messagebox.showerror("Ошибка", "Сбой при вызове функций упаковщика.")

    def restore_backup(self):
        selected = self.backup_tree.selection()
        if not selected: return
        backup_id, _ = self.backup_tree.item(selected[0])["values"]

        msg = f"Восстановить бэкап #{backup_id}?\nТекущие сохранения игры '{self.game_name}' будут перезаписаны!"
        if messagebox.askyesno("Восстановление", msg):
            self.parent.log(f"Запрос архивов из БД для бэкапа #{backup_id}...")
            success = capi.restore_game_backup(backup_id, self.game_path)
            if success:
                self.parent.log(f"УСПЕХ: Бэкап #{backup_id} распакован DLL в {self.game_path}")
                messagebox.showinfo("Успех", "Сохранения успешно возвращены в игру!")
            else:
                self.parent.log(f"ОШИБКА: Сбой восстановления бэкапа #{backup_id}.")
                messagebox.showerror("Ошибка", "Не удалось извлечь или распаковать данные.")

    def delete_backup(self):
        selected = self.backup_tree.selection()
        if not selected: return
        backup_id, b_time = self.backup_tree.item(selected[0])["values"]

        if messagebox.askyesno("Удаление", f"Удалить точку бэкапа #{backup_id} от {b_time}?"):
            try:
                self.parent.db.delete_single_backup(backup_id)
                self.parent.log(f"Точка бэкапа #{backup_id} удалена из Базы Данных.")
                self.refresh_backups_list()
            except Exception as e:
                self.parent.log(f"Ошибка удаления бэкапа: {e}")


class GameBackupApp(tk.Tk):
    """Главное окно приложения: Список игр + Системный лог."""
    def __init__(self):
        super().__init__()
        self.title("SaveVault — Менеджер сохранений игр")
        self.geometry("900x550")
        self.minsize(800, 450)

        self.db = ConnMang()
        self.db.open()

        self.setup_styles()
        self.build_ui()
        self.refresh_games_list()
        self.log("Приложение запущено. База данных PostgreSQL подключена успешно.")

    def setup_styles(self):
        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self.style.configure(".", background="#f5f6f8", foreground="#2c3e50", font=("Segoe UI", 10))
        self.style.configure("TLabelframe", background="#f5f6f8", borderwidth=1, relief="solid")
        self.style.configure("TLabelframe.Label", font=("Segoe UI", 10, "bold"), foreground="#34495e", background="#f5f6f8")
        self.style.configure("Treeview", background="#ffffff", fieldbackground="#ffffff", rowheight=26, borderwidth=0)
        self.style.map("Treeview", background=[("selected", "#3498db")], foreground=[("selected", "#ffffff")])
        self.style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#e2e8f0", relief="flat")
        self.style.configure("TButton", font=("Segoe UI", 9, "bold"), padding=8, background="#e2e8f0", borderwidth=0)
        self.style.map("TButton", background=[("active", "#cbd5e1"), ("pressed", "#94a3b8")])
        self.style.configure("Accent.TButton", background="#2ecc71", foreground="white")
        self.style.map("Accent.TButton", background=[("active", "#27ae60")])

    def build_ui(self):
        # Шапка
        header = ttk.Frame(self, padding=(15, 10))
        header.pack(fill=tk.X)
        ttk.Label(header, text="🎮 SaveVault c-API Manager", font=("Segoe UI", 16, "bold"), foreground="#2c3e50").pack(side=tk.LEFT)
        ttk.Label(header, text="[ Двухоконный режим ]", font=("Segoe UI", 10, "italic"), foreground="#7f8c8d").pack(side=tk.LEFT, padx=10, ipady=5)

        # Рабочая область списка игр
        main_container = ttk.LabelFrame(self, text=" Отслеживаемые игры (Двойной клик для управления бэкапами) ", padding=10)
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        # ИСПРАВЛЕНО: Создаем контейнер для кнопок справа до упаковки таблицы!
        actions = ttk.Frame(main_container, padding=(10, 0, 0, 0))
        actions.pack(side=tk.RIGHT, fill=tk.Y)

        ttk.Button(actions, text="🔍 Сканировать ПК", command=self.scan_pc).pack(fill=tk.X, pady=3)
        ttk.Button(actions, text="➕ Добавить вручную", command=self.add_game_manual).pack(fill=tk.X, pady=3)

        self.btn_manage = ttk.Button(actions, text="🛠 Управлять бэкапами", command=self.open_backup_manager)
        self.btn_manage.pack(fill=tk.X, pady=3)
        self.btn_manage.state(["disabled"])

        self.btn_delete_game = ttk.Button(actions, text="❌ Удалить игру", command=self.delete_game)
        self.btn_delete_game.pack(fill=tk.X, pady=3)
        self.btn_delete_game.state(["disabled"])

        # Скроллбар таблицы (будет слева от блока кнопок)
        scroll = ttk.Scrollbar(main_container, orient=tk.VERTICAL)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Таблица игр (займет всё оставшееся пространство слева)
        self.game_tree = ttk.Treeview(main_container, columns=("id", "name"), show="headings", selectmode="browse", yscrollcommand=scroll.set)
        self.game_tree.heading("id", text="ID")
        self.game_tree.heading("name", text="Название игры")
        self.game_tree.column("id", width=50, stretch=tk.NO, anchor=tk.CENTER)
        self.game_tree.column("name", width=400, stretch=tk.YES)

        self.game_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.config(command=self.game_tree.yview)

        self.game_tree.bind("<Double-1>", self.open_backup_manager)
        self.game_tree.bind("<<TreeviewSelect>>", lambda e: self.btn_manage.state(["!disabled"]) or self.btn_delete_game.state(["!disabled"]))

        # Консоль логов внизу главного окна
        log_frame = ttk.LabelFrame(self, text=" Журнал событий (Лог работы системы) ", padding=5)
        log_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=15, pady=10)

        self.log_text = tk.Text(log_frame, height=6, bg="#1e1e1e", fg="#d4d4d4", font=("Consolas", 9), state=tk.DISABLED)
        log_scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.update_idletasks()

    def open_backup_manager(self, event=None):
        selected = self.game_tree.selection()
        if not selected: return
        game_id, game_name = self.game_tree.item(selected[0])["values"]
        BackupManagerWindow(self, game_id, game_name)

    def parse_game_name(self, path_str: str) -> str:
        path = Path(path_str)
        if path.is_file(): path = path.parent
        while 'save' in path.name.lower():
            if path.parent.name != 'Users': path = path.parent
            else: break
        name = re.sub(r'[_\-\s]', '', str(path.name))
        return re.sub(r'([a-z])([A-Z0-9])', r'\1 \2', name)

    def refresh_games_list(self):
        for row in self.game_tree.get_children():
            self.game_tree.delete(row)
        games = self.db.get_all_games()
        for g_id, g_name in games:
            self.game_tree.insert("", tk.END, values=(g_id, g_name))
        self.btn_manage.state(["disabled"])
        self.btn_delete_game.state(["disabled"])

    def scan_pc(self):
        self.log("Запущено сканирование ПК на наличие сохранений (*.sav)...")
        home_path = Path.home()
        try:
            found_saves = list(home_path.glob("**/*.sav"))
            count = 0
            for i in found_saves:
                if not list(i.parent.glob("*.vdf")):
                    g_path = str(i.parent)
                    g_name = self.parse_game_name(i.parent)
                    game_id = self.db.add_game(g_name)
                    self.db.add_path(game_id, g_path)
                    count += 1
                    self.log(f"Найдено: '{g_name}' -> {g_path}")
            self.log(f"Сканирование завершено. Добавлено/обновлено игр: {count}")
            messagebox.showinfo("Сканирование", f"Успешно обработано игр: {count}")
        except Exception as e:
            self.log(f"ОШИБКА сканирования: {e}")
        finally:
            self.refresh_games_list()

    def add_game_manual(self):
        dir_path = filedialog.askdirectory(title="Выберите папку с сохранениями игры")
        if not dir_path: return
        g_name = self.parse_game_name(dir_path)
        game_id = self.db.add_game(g_name)
        self.db.add_path(game_id, dir_path)
        self.log(f"Вручную добавлена игра '{g_name}'")
        self.refresh_games_list()

    def delete_game(self):
        selected = self.game_tree.selection()
        if not selected: return
        game_id, game_name = self.game_tree.item(selected[0])["values"]

        if messagebox.askyesno("Удаление игры", f"Удалить игру '{game_name}' и ВСЕ её бэкапы?"):
            try:
                with self.db.getconnection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("DELETE FROM games WHERE id = %s;", [game_id])
                self.log(f"Игра '{game_name}' каскадно удалена из базы данных.")
                self.refresh_games_list()
            except Exception as e:
                self.log(f"Ошибка удаления игры: {e}")

    def destroy(self):
        self.db.close()
        super().destroy()

if __name__ == "__main__":
    app = GameBackupApp()
    app.mainloop()