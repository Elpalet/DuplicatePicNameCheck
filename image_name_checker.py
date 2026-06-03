import csv
import os
import re
import sys
import tkinter as tk
from collections import defaultdict
from dataclasses import dataclass
from tkinter import filedialog, messagebox, ttk


SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp", ".svg", ".pdf"}

MODE_LAST_HYPHEN = "last_hyphen"
MODE_LAST_UNDERSCORE = "last_underscore"
MODE_CUSTOM_DELIMITER = "custom_delimiter"
MODE_REGEX = "regex"

MODE_LABELS = {
    "按最后一个 - 前的内容分组": MODE_LAST_HYPHEN,
    "按最后一个 _ 前的内容分组": MODE_LAST_UNDERSCORE,
    "按自定义符号分割分组": MODE_CUSTOM_DELIMITER,
    "按自定义正则表达式分组": MODE_REGEX,
}

MODE_DISPLAY = {value: label for label, value in MODE_LABELS.items()}


@dataclass
class ResultItem:
    result_type: str
    key: str
    count: int
    filenames: list
    paths: list


def collect_image_files(folder, recursive):
    """Collect image files from a folder."""
    if not folder or not os.path.isdir(folder):
        raise ValueError("请选择有效的图片文件夹。")

    image_files = []
    if recursive:
        for root, _, filenames in os.walk(folder):
            for filename in filenames:
                if os.path.splitext(filename)[1].lower() in SUPPORTED_EXTENSIONS:
                    image_files.append(os.path.abspath(os.path.join(root, filename)))
    else:
        with os.scandir(folder) as entries:
            for entry in entries:
                if entry.is_file() and os.path.splitext(entry.name)[1].lower() in SUPPORTED_EXTENSIONS:
                    image_files.append(os.path.abspath(entry.path))

    return sorted(image_files, key=lambda path: (os.path.basename(path).lower(), path.lower()))


def find_duplicate_filenames(files):
    """Return image files grouped by duplicate basename."""
    by_name = defaultdict(list)
    for path in files:
        by_name[os.path.basename(path)].append(path)
    return {filename: paths for filename, paths in by_name.items() if len(paths) > 1}


def get_group_key(filename, mode, regex_pattern=None, delimiter=None):
    """Get a grouping key from a filename."""
    if mode == MODE_LAST_HYPHEN:
        stem, _ = os.path.splitext(filename)
        if "-" not in stem:
            return stem
        return stem.rsplit("-", 1)[0]

    if mode == MODE_LAST_UNDERSCORE:
        stem, _ = os.path.splitext(filename)
        if "_" not in stem:
            return stem
        return stem.rsplit("_", 1)[0]

    if mode == MODE_CUSTOM_DELIMITER:
        if not delimiter:
            raise ValueError("使用自定义符号分割分组时，请先输入分隔符。")
        stem, _ = os.path.splitext(filename)
        if delimiter not in stem:
            return stem
        return stem.rsplit(delimiter, 1)[0]

    if mode == MODE_REGEX:
        if not regex_pattern:
            raise ValueError("使用自定义正则表达式分组时，请先输入正则表达式。")
        match = re.search(regex_pattern, filename)
        if not match:
            return os.path.splitext(filename)[0]
        if match.groups():
            return match.group(1)
        return match.group(0)

    raise ValueError(f"未知分组模式：{mode}")


def group_similar_prefixes(files, mode, regex_pattern=None, delimiter=None):
    """Group image files by similar filename prefix."""
    groups = defaultdict(list)
    for path in files:
        filename = os.path.basename(path)
        key = get_group_key(filename, mode, regex_pattern, delimiter)
        groups[key].append(path)
    return dict(groups)


def build_results(duplicates, groups, expected_count=4):
    """Build table-ready result rows from duplicates and groups."""
    results = []

    for filename, paths in sorted(duplicates.items(), key=lambda item: (-len(item[1]), item[0].lower())):
        results.append(
            ResultItem(
                result_type="重复文件名",
                key=filename,
                count=len(paths),
                filenames=[os.path.basename(path) for path in paths],
                paths=sorted(paths, key=str.lower),
            )
        )

    sorted_groups = sorted(groups.items(), key=lambda item: (-len(item[1]), item[0].lower()))
    for key, paths in sorted_groups:
        result_type = "正常分组" if len(paths) == expected_count else "异常分组"
        sorted_paths = sorted(paths, key=lambda path: os.path.basename(path).lower())
        results.append(
            ResultItem(
                result_type=result_type,
                key=key,
                count=len(paths),
                filenames=[os.path.basename(path) for path in sorted_paths],
                paths=sorted_paths,
            )
        )

    return results


def export_results_to_csv(results, output_path):
    """Export scan results to a UTF-8 BOM CSV file for Excel."""
    with open(output_path, "w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=["result_type", "group_key_or_filename", "count", "filenames", "paths"],
        )
        writer.writeheader()
        for item in results:
            writer.writerow(
                {
                    "result_type": item.result_type,
                    "group_key_or_filename": item.key,
                    "count": item.count,
                    "filenames": "\n".join(item.filenames),
                    "paths": "\n".join(item.paths),
                }
            )


def short_join(values, max_length=110):
    text = "；".join(values)
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def parse_expected_count(value):
    try:
        expected = int(value)
    except ValueError as exc:
        raise ValueError("期望每组文件数必须是正整数。") from exc
    if expected <= 0:
        raise ValueError("期望每组文件数必须大于 0。")
    return expected


class ImageNameCheckerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("图片文件名检查工具")
        self.root.geometry("1180x760")
        self.root.minsize(920, 620)

        self.folder_var = tk.StringVar()
        self.recursive_var = tk.BooleanVar(value=False)
        self.mode_var = tk.StringVar(value="按最后一个 - 前的内容分组")
        self.delimiter_var = tk.StringVar(value="-")
        self.regex_var = tk.StringVar(value=r"^(.*)-[A-Za-z]\.tif$")
        self.expected_count_var = tk.StringVar(value="4")
        self.filter_var = tk.StringVar(value="全部结果")
        self.status_var = tk.StringVar(value="请选择图片文件夹后开始扫描。")

        self.all_results = []
        self.filtered_results = []
        self.result_by_iid = {}

        self._build_ui()
        self._update_regex_state()

    def _build_ui(self):
        outer = ttk.Frame(self.root, padding=12)
        outer.pack(fill=tk.BOTH, expand=True)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(2, weight=1)

        folder_frame = ttk.LabelFrame(outer, text="扫描设置", padding=10)
        folder_frame.grid(row=0, column=0, sticky="ew")
        folder_frame.columnconfigure(1, weight=1)
        folder_frame.columnconfigure(4, weight=1)

        ttk.Button(folder_frame, text="选择图片文件夹", command=self.choose_folder).grid(
            row=0, column=0, sticky="w", padx=(0, 8), pady=4
        )
        ttk.Entry(folder_frame, textvariable=self.folder_var, state="readonly").grid(
            row=0, column=1, columnspan=5, sticky="ew", pady=4
        )

        ttk.Checkbutton(folder_frame, text="递归扫描子文件夹", variable=self.recursive_var).grid(
            row=1, column=0, sticky="w", padx=(0, 8), pady=4
        )

        ttk.Label(folder_frame, text="分组规则").grid(row=1, column=1, sticky="e", padx=(8, 6), pady=4)
        mode_box = ttk.Combobox(
            folder_frame,
            textvariable=self.mode_var,
            values=list(MODE_LABELS.keys()),
            state="readonly",
            width=28,
        )
        mode_box.grid(row=1, column=2, sticky="w", pady=4)
        mode_box.bind("<<ComboboxSelected>>", lambda _event: self._update_regex_state())

        ttk.Label(folder_frame, text="自定义符号").grid(row=1, column=3, sticky="e", padx=(14, 6), pady=4)
        self.delimiter_entry = ttk.Entry(folder_frame, textvariable=self.delimiter_var, width=10)
        self.delimiter_entry.grid(row=1, column=4, sticky="w", pady=4)

        ttk.Label(folder_frame, text="自定义正则").grid(row=2, column=1, sticky="e", padx=(8, 6), pady=4)
        self.regex_entry = ttk.Entry(folder_frame, textvariable=self.regex_var)
        self.regex_entry.grid(row=2, column=2, columnspan=3, sticky="ew", pady=4)

        ttk.Label(folder_frame, text="期望每组文件数").grid(row=1, column=5, sticky="e", padx=(14, 6), pady=4)
        ttk.Entry(folder_frame, textvariable=self.expected_count_var, width=8).grid(
            row=1, column=6, sticky="w", pady=4
        )

        action_frame = ttk.Frame(outer)
        action_frame.grid(row=1, column=0, sticky="ew", pady=(10, 8))
        action_frame.columnconfigure(3, weight=1)

        ttk.Button(action_frame, text="开始扫描", command=self.scan).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(action_frame, text="导出结果 CSV", command=self.export_csv).grid(row=0, column=1, padx=(0, 18))

        ttk.Label(action_frame, text="显示").grid(row=0, column=2, padx=(0, 6))
        filter_box = ttk.Combobox(
            action_frame,
            textvariable=self.filter_var,
            values=["全部结果", "所有分组", "异常分组", "重复文件名"],
            state="readonly",
            width=14,
        )
        filter_box.grid(row=0, column=3, sticky="w")
        filter_box.bind("<<ComboboxSelected>>", lambda _event: self.refresh_table())

        ttk.Label(action_frame, textvariable=self.status_var).grid(row=0, column=4, sticky="e")

        result_pane = ttk.PanedWindow(outer, orient=tk.VERTICAL)
        result_pane.grid(row=2, column=0, sticky="nsew")

        table_frame = ttk.Frame(result_pane)
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        columns = ("type", "key", "count", "filenames", "paths")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("type", text="类型")
        self.tree.heading("key", text="名称或分组前缀")
        self.tree.heading("count", text="数量")
        self.tree.heading("filenames", text="文件名列表简略显示")
        self.tree.heading("paths", text="路径列表简略显示")
        self.tree.column("type", width=95, anchor="center", stretch=False)
        self.tree.column("key", width=260, anchor="w")
        self.tree.column("count", width=70, anchor="center", stretch=False)
        self.tree.column("filenames", width=320, anchor="w")
        self.tree.column("paths", width=430, anchor="w")
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self.show_detail)

        y_scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        y_scroll.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=y_scroll.set)

        x_scroll = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        x_scroll.grid(row=1, column=0, sticky="ew")
        self.tree.configure(xscrollcommand=x_scroll.set)

        result_pane.add(table_frame, weight=4)

        detail_frame = ttk.LabelFrame(result_pane, text="完整详情", padding=8)
        detail_frame.rowconfigure(0, weight=1)
        detail_frame.columnconfigure(0, weight=1)

        self.detail_text = tk.Text(detail_frame, height=10, wrap=tk.NONE)
        self.detail_text.grid(row=0, column=0, sticky="nsew")
        detail_y_scroll = ttk.Scrollbar(detail_frame, orient=tk.VERTICAL, command=self.detail_text.yview)
        detail_y_scroll.grid(row=0, column=1, sticky="ns")
        detail_x_scroll = ttk.Scrollbar(detail_frame, orient=tk.HORIZONTAL, command=self.detail_text.xview)
        detail_x_scroll.grid(row=1, column=0, sticky="ew")
        self.detail_text.configure(yscrollcommand=detail_y_scroll.set, xscrollcommand=detail_x_scroll.set)

        result_pane.add(detail_frame, weight=1)

    def choose_folder(self):
        folder = filedialog.askdirectory(title="选择图片文件夹")
        if folder:
            self.folder_var.set(folder)
            self.status_var.set("已选择文件夹，点击开始扫描。")

    def _update_regex_state(self):
        mode = MODE_LABELS.get(self.mode_var.get(), MODE_LAST_HYPHEN)
        regex_state = "normal" if mode == MODE_REGEX else "disabled"
        delimiter_state = "normal" if mode == MODE_CUSTOM_DELIMITER else "disabled"
        self.regex_entry.configure(state=regex_state)
        self.delimiter_entry.configure(state=delimiter_state)

    def scan(self):
        folder = self.folder_var.get()
        if not folder:
            messagebox.showwarning("请选择文件夹", "请先选择一个图片文件夹。")
            return

        mode = MODE_LABELS.get(self.mode_var.get(), MODE_LAST_HYPHEN)
        regex_pattern = self.regex_var.get().strip() if mode == MODE_REGEX else None
        delimiter = self.delimiter_var.get() if mode == MODE_CUSTOM_DELIMITER else None

        try:
            expected_count = parse_expected_count(self.expected_count_var.get().strip())
            if regex_pattern:
                re.compile(regex_pattern)
            files = collect_image_files(folder, self.recursive_var.get())
            if not files:
                self.all_results = []
                self.refresh_table()
                self._set_detail("未找到支持格式文件。请确认文件夹中包含支持的图片、SVG 或 PDF 文件。")
                self.status_var.set("未找到支持格式文件。")
                messagebox.showinfo("扫描完成", "该文件夹中没有找到支持格式的图片、SVG 或 PDF 文件。")
                return

            duplicates = find_duplicate_filenames(files)
            groups = group_similar_prefixes(files, mode, regex_pattern, delimiter)
            self.all_results = build_results(duplicates, groups, expected_count)
            self.refresh_table()

            duplicate_count = len(duplicates)
            abnormal_count = sum(1 for item in self.all_results if item.result_type == "异常分组")
            if duplicate_count == 0:
                duplicate_text = "未发现重复文件名"
            else:
                duplicate_text = f"发现 {duplicate_count} 个重复文件名"
            self.status_var.set(
                f"扫描完成：{len(files)} 个图片，{len(groups)} 个分组，{abnormal_count} 个异常分组，{duplicate_text}。"
            )
            if self.filtered_results:
                first_iid = self.tree.get_children()[0]
                self.tree.selection_set(first_iid)
                self.tree.focus(first_iid)
                self.show_detail()
            else:
                self._set_detail(duplicate_text)
        except re.error as exc:
            messagebox.showerror("正则表达式错误", f"自定义正则表达式无效：\n{exc}")
        except ValueError as exc:
            messagebox.showwarning("输入有误", str(exc))
        except OSError as exc:
            messagebox.showerror("扫描失败", f"读取文件夹时出错：\n{exc}")

    def refresh_table(self):
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        self.result_by_iid.clear()

        selected_filter = self.filter_var.get()
        if selected_filter == "所有分组":
            self.filtered_results = [item for item in self.all_results if item.result_type in {"正常分组", "异常分组"}]
        elif selected_filter == "异常分组":
            self.filtered_results = [item for item in self.all_results if item.result_type == "异常分组"]
        elif selected_filter == "重复文件名":
            self.filtered_results = [item for item in self.all_results if item.result_type == "重复文件名"]
        else:
            self.filtered_results = list(self.all_results)

        for index, item in enumerate(self.filtered_results):
            iid = str(index)
            self.result_by_iid[iid] = item
            self.tree.insert(
                "",
                tk.END,
                iid=iid,
                values=(
                    item.result_type,
                    item.key,
                    item.count,
                    short_join(item.filenames),
                    short_join(item.paths),
                ),
            )

        if not self.filtered_results:
            if selected_filter == "重复文件名":
                self._set_detail("未发现重复文件名。")
            elif selected_filter == "异常分组":
                self._set_detail("未发现异常分组。")
            elif selected_filter == "所有分组":
                self._set_detail("暂无分组结果。")
            else:
                self._set_detail("暂无结果。")

    def show_detail(self, _event=None):
        selection = self.tree.selection()
        if not selection:
            return
        item = self.result_by_iid.get(selection[0])
        if not item:
            return

        lines = [
            f"类型：{item.result_type}",
            f"名称或分组前缀：{item.key}",
            f"数量：{item.count}",
            "",
            "文件名：",
        ]
        lines.extend(f"  {filename}" for filename in item.filenames)
        lines.extend(["", "完整路径："])
        lines.extend(f"  {path}" for path in item.paths)
        self._set_detail("\n".join(lines))

    def _set_detail(self, text):
        self.detail_text.configure(state="normal")
        self.detail_text.delete("1.0", tk.END)
        self.detail_text.insert("1.0", text)
        self.detail_text.configure(state="disabled")

    def export_csv(self):
        if not self.all_results:
            messagebox.showwarning("没有可导出的结果", "请先完成扫描并生成结果。")
            return

        output_path = filedialog.asksaveasfilename(
            title="导出结果 CSV",
            defaultextension=".csv",
            filetypes=[("CSV 文件", "*.csv"), ("所有文件", "*.*")],
            initialfile="image_name_check_results.csv",
        )
        if not output_path:
            return

        try:
            export_results_to_csv(self.all_results, output_path)
            messagebox.showinfo("导出完成", f"结果已导出：\n{output_path}")
            self.status_var.set(f"结果已导出：{output_path}")
        except OSError as exc:
            messagebox.showerror("导出失败", f"写入 CSV 时出错：\n{exc}")


def main():
    root = tk.Tk()
    try:
        style = ttk.Style(root)
        if sys.platform == "win32":
            style.theme_use("vista")
        elif "clam" in style.theme_names():
            style.theme_use("clam")
    except tk.TclError:
        pass
    ImageNameCheckerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
