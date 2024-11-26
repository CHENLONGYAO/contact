import requests
import re
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import List, Tuple
import unicodedata

# URL to be scraped
URL = "https://csie.ncut.edu.tw/content.php?key=86OP82WJQO"

def setup_database() -> None:
    """
    Set up SQLite database and create contacts table if it does not exist.
    """
    conn = sqlite3.connect("contacts.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS contacts (
            iid INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            title TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE
        )
        """
    )
    conn.commit()
    conn.close()

def save_to_database(contacts: List[Tuple[str, str, str]]) -> None:
    """
    Save contact information to SQLite database.

    :param contacts: List of tuples containing name, title, and email.
    """
    conn = sqlite3.connect("contacts.db")
    cursor = conn.cursor()
    for name, title, email in contacts:
        try:
            cursor.execute(
                "INSERT INTO contacts (name, title, email) VALUES (?, ?, ?)",
                (name, title, email),
            )
        except sqlite3.IntegrityError:
            # Ignore duplicates
            pass
    conn.commit()
    conn.close()

def scrape_contacts() -> List[Tuple[str, str, str]]:
    """
    Scrape contact information from the specified URL.

    :return: List of tuples containing name, title, and email.
    """
    try:
        response = requests.get(URL)
        response.raise_for_status()
    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 404:
            # 顯示 404 錯誤的特定視窗
            messagebox.showerror("網路錯誤", "無法取得網頁：404")
        else:
            # 顯示一般的 HTTP 錯誤
            messagebox.showerror("網路錯誤", f"HTTP 錯誤：{response.status_code}")
        return []
    except requests.exceptions.RequestException as e:
        # 一般網路錯誤通知
        messagebox.showerror("網路錯誤", f"無法連接網站：\n{str(e)}")
        return []

    # Use regex to extract contact details from the HTML
    contacts = []
    html_content = response.text

    # Improved regex pattern to extract name, title, and email
    pattern = re.compile(r'<div\s+class="member_name">.*?<a\s+href="content_teacher_detail\.php\?teacher_rkey=.*?">\s*(.*?)\s*</a>.*?<div\s+class="member_info_content">\s*(.*?)\s*</div>.*?<a\s+href="mailto:(.*?)">', re.DOTALL)
    matches = pattern.findall(html_content)

    for match in matches:
        name, title, email = match
        name = re.sub(r'\s+', ' ', name)  # Remove extra whitespace within the name
        email = email.replace('//', '')  # Remove any unwanted characters like '//' from email
        contacts.append((name.strip(), title.strip(), email.strip()))

    return contacts



def get_display_width(s: str) -> int:
    """計算字串在終端機顯示時的寬度。"""
    width = 0
    for ch in s:
        if unicodedata.east_asian_width(ch) in ('F', 'W', 'A'):
            width += 2  # 全形字符寬度為2
        else:
            width += 1  # 半形字符寬度為1
    return width

def pad_string(s: str, total_width: int) -> str:
    """根據顯示寬度來填充字串，使其達到指定的總寬度。"""
    padding = total_width - get_display_width(s)
    return s + ' ' * max(padding, 0)

def display_contacts(contacts: List[Tuple[str, str, str]]) -> None:
    """
    Display the contact information in the Tkinter GUI.

    :param contacts: List of tuples containing name, title, and email.
    """
    contact_text.configure(state="normal")
    contact_text.delete(1.0, tk.END)

    # Define the headers and column widths for alignment
    headers = ['姓名', '職稱', 'Email']
    widths = [12, 30, 30]  # Adjust the widths for better alignment

    # Create the header line with padding
    header_line = ''.join(pad_string(header, width) for header, width in zip(headers, widths))
    contact_text.insert(tk.END, header_line + "\n")
    separator = ''.join('-' * width for width in widths)
    contact_text.insert(tk.END, separator + "\n")

    # Insert each contact's information with aligned columns
    for name, title, email in contacts:
        row = [
            pad_string(name, widths[0]),
            pad_string(title, widths[1]),
            pad_string(email, widths[2])
        ]
        contact_text.insert(tk.END, ''.join(row) + "\n")

    contact_text.configure(state="disabled")

# Tkinter GUI setup
root = tk.Tk()
root.title("聯絡資訊爬蟲")
root.geometry("640x480")
root.columnconfigure(1, weight=1)
root.rowconfigure(1, weight=1)

# URL Entry
url_label = ttk.Label(root, text="URL:")
url_label.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)

url_entry = ttk.Entry(root, width=60)
url_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
url_entry.insert(0, URL)

# Fetch Button
fetch_button = ttk.Button(root, text="抓取", command=lambda: display_contacts(scrape_contacts()))
fetch_button.grid(row=0, column=2, sticky=tk.E, padx=5, pady=5)

# ScrolledText for displaying contacts
contact_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, state="disabled", font=("Consolas", 10))
contact_text.grid(row=1, column=0, columnspan=3, sticky=tk.NSEW, padx=5, pady=5)

# Set up the database
setup_database()

# Start the Tkinter event loop
root.mainloop()
