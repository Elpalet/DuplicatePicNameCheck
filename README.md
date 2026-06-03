# 图片文件名检查工具

一个 Windows 使用的文件名检查小工具，面向图片、SVG 和 PDF 文件，使用 Python 标准库和 tkinter 编写，不依赖 pandas、PyQt、OpenCV 等重型库。

## 功能

- 通过可视化界面选择图片文件夹。
- 支持扫描格式：`.jpg`、`.jpeg`、`.png`、`.tif`、`.tiff`、`.bmp`、`.webp`、`.svg`、`.pdf`。
- 默认只扫描当前文件夹，可勾选递归扫描子文件夹。
- 检查重复文件名；递归扫描时，不同子文件夹里的同名图片也会被统计。
- 按相似前缀分组统计图片数量。
- 设置“期望每组文件数”，默认 4；数量不等于期望值的分组会标记为异常分组。
- 表格中可切换查看：全部结果、所有分组、异常分组、重复文件名。
- 点击表格行后，下方显示完整文件名和完整路径。
- 支持导出 CSV，编码为 `utf-8-sig`，Excel 打开中文不乱码。

## 运行方法

确保电脑已安装 Python 3.8 或更高版本，然后在本目录运行：

```bash
python image_name_checker.py
```

Windows 也可以双击 `image_name_checker.py` 运行。如果没有自动打开，可以右键选择 Python 打开。

## 使用方法

1. 点击“选择图片文件夹”。
2. 根据需要勾选“递归扫描子文件夹”。
3. 选择分组规则。
4. 如选择自定义符号分组，在“自定义符号”输入框填写分隔符。
5. 如选择自定义正则表达式，在输入框填写正则。
6. 设置“期望每组文件数”，默认是 `4`。
7. 点击“开始扫描”。
8. 在结果表格中查看全部结果、分组、异常分组和重复文件名。
9. 点击“导出结果 CSV”保存结果。

## 分组规则说明

工具提供四种分组模式：

### 1. 按最后一个 `-` 前的内容分组

这是默认规则。程序会先去掉文件扩展名，再按最后一个短横线切分，取短横线前面的内容作为分组前缀。

例如：

```text
樊惟磊-20260504_0004.tif (green)+5+1-c.tif
樊惟磊-20260504_0004.tif (green)+5+1-g.tif
樊惟磊-20260504_0004.tif (green)+5+1-m.tif
樊惟磊-20260504_0004.tif (green)+5+1-r.tif
```

会归为同一组：

```text
樊惟磊-20260504_0004.tif (green)+5+1
```

### 2. 按最后一个 `_` 前的内容分组

程序会先去掉文件扩展名，再按最后一个下划线切分，取下划线前面的内容作为分组前缀。

### 3. 按自定义符号分割分组

程序会先去掉文件扩展名，再按用户输入的自定义符号进行切分，取最后一次出现该符号前面的内容作为分组前缀。

例如自定义符号填写：

```text
+
```

文件名：

```text
sample+channel1.tif
sample+channel2.tif
```

会归为：

```text
sample
```

如果填写 `-`，效果类似默认的“按最后一个 `-` 前的内容分组”；如果填写 `_`，效果类似“按最后一个 `_` 前的内容分组”。也支持多个字符作为分隔符，例如 `--`、`__`、`通道`。

### 4. 按自定义正则表达式分组

如果正则表达式包含捕获组，程序使用第一个捕获组作为分组前缀。

例如：

```regex
^(.*)-[A-Za-z]\.tif$
```

可以把下面这些文件分到同一组：

```text
sample-c.tif
sample-g.tif
sample-m.tif
sample-r.tif
```

分组前缀为：

```text
sample
```

如果正则没有匹配某个文件名，该文件会使用去掉扩展名后的文件名作为分组前缀。

这条正则：

```regex
^(.*)-[A-Za-z]\.tif$
```

含义是：

- `^`：从文件名开头开始匹配。
- `(.*)`：捕获任意内容，作为分组前缀；程序会使用这个第一个捕获组。
- `-`：匹配一个普通短横线。
- `[A-Za-z]`：匹配一个英文字母，例如 `c`、`g`、`m`、`r`。
- `\.tif`：匹配字面量 `.tif`，这里的 `\.` 表示普通点号，不是正则里的“任意字符”。
- `$`：匹配到文件名结尾。

因此它可以把 `sample-c.tif`、`sample-g.tif` 分到 `sample` 这一组。这个表达式只匹配 `.tif`，不匹配 `.tiff`、`.png` 或大写 `.TIF`；如果需要更通用，可以使用自定义符号分组，或者写更宽松的正则。

## 导出 CSV

CSV 包含以下字段：

- `result_type`
- `group_key_or_filename`
- `count`
- `filenames`
- `paths`

导出文件使用 `utf-8-sig` 编码，适合直接用 Excel 打开。

## 打包方法

打包前先安装 PyInstaller：

```bash
pip install pyinstaller
```

### Windows

双击或在命令行运行：

```bat
build_windows.bat
```

等价命令：

```bat
pyinstaller --onefile --windowed --name 图片文件名检查工具 image_name_checker.py
```

生成的程序通常位于：

```text
dist\图片文件名检查工具.exe
```

### macOS

先给脚本执行权限：

```bash
chmod +x build_macos.sh
```

运行：

```bash
./build_macos.sh
```

等价命令：

```bash
pyinstaller --onefile --windowed --name 图片文件名检查工具 image_name_checker.py
```

生成的 app 或可执行文件通常位于 `dist/` 目录。

### macOS 其他封装方式

如果目标是发给别人双击运行，推荐优先在一台 macOS 电脑上打包。Windows 不能直接打出可正常运行的 macOS `.app`。

可选方案：

- PyInstaller：最简单，适合本工具。命令是 `pyinstaller --onefile --windowed --name 图片文件名检查工具 image_name_checker.py`。
- py2app：macOS 原生 `.app` 打包工具，适合只面向 macOS 分发。
- Briefcase：可以生成更标准的 macOS app 项目结构，但配置比 PyInstaller 多。
- Nuitka：会把 Python 程序编译打包，启动速度和体积可能更好，但安装和配置更复杂。

注意事项：

- 如果要给 Intel 和 Apple Silicon 两类 Mac 使用，最好分别在对应架构上打包，或使用支持 universal2 的 Python 环境。
- 未签名的 `.app` 发给别人后，macOS Gatekeeper 可能提示无法打开。可以右键点击 app 后选择“打开”，或者进一步做 Apple Developer ID 签名和 notarization。
- tkinter 需要打包进应用。使用 python.org 的 macOS Python 通常更省心。

## tkinter 安装说明

tkinter 属于 Python 标准库，但少数系统的 Python 发行版可能没有预装 tkinter。

- Windows：建议从 [python.org](https://www.python.org/) 安装官方 Python，并在安装时勾选 Tcl/Tk。
- macOS：建议从 [python.org](https://www.python.org/) 安装官方 Python；也可以使用 Homebrew Python，但要确认 tkinter 可用。
- Ubuntu / Debian：

```bash
sudo apt install python3-tk
```

测试 tkinter 是否可用：

```bash
python -m tkinter
```

如果弹出一个小窗口，说明 tkinter 可用。

## 常见问题

### 为什么没有扫描到图片？

请确认文件扩展名属于支持列表：`.jpg`、`.jpeg`、`.png`、`.tif`、`.tiff`、`.bmp`、`.webp`、`.svg`、`.pdf`。如果文件在子文件夹中，请勾选“递归扫描子文件夹”。

### 为什么某些文件被标记为异常分组？

当某个分组内图片数量不等于“期望每组文件数”时，会被标记为异常分组。默认期望值为 4，适合 `-c`、`-g`、`-m`、`-r` 这种四通道文件。

### 自定义正则表达式写错会怎样？

程序会弹窗提示正则表达式错误，不会直接崩溃。

### 中文路径和中文文件名支持吗？

支持。程序使用 Python 的标准文件路径处理方式，CSV 导出也使用 `utf-8-sig` 编码。
