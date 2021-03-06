import logging
import os
import queue
import tkinter as tk
import configparser
from threading import Thread
from tkinter import LEFT, SOLID, SW, Label, font as tkfont
from tkinter import filedialog, OptionMenu, StringVar, TclError, Toplevel
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
import steg

LOG_LEVEL = 20
CONFIG_PATH = "config/prefs.ini"


color_themes = []
current_theme = "Default"
class App(tk.Tk):
    
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.title_font = tkfont.Font(family='Helvetica',
                                      size=18,
                                      weight="bold",
                                      slant="italic")

        # the container is where we'll stack a bunch of frames
        # on top of each other, then the one we want visible
        # will be raised above the others
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)
        self.title("Netherizer")
        try:
            self.iconbitmap("assets/Icon.ico")
        except TclError:
            pass

        self.frames = {}
        for F in (StartPage, EncodePage, DecodePage):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame

            # put all of the pages in the same location;
            # the one on the top of the stacking order
            # will be the one that is visible.
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("StartPage")

    def show_frame(self, page_name):
        '''Show a frame for the given page name'''
        frame = self.frames[page_name]
        frame.tkraise()

class StartPage(tk.Frame):

    def __init__(self, parent, controller):
        global selected_theme
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.rowconfigure(21, weight=1)
        self.columnconfigure(21, weight=1)
        title = tk.Label(self, text="NETHERIZER v.1.3",
                         font=controller.title_font)
        title.grid(column=1, row=0, sticky="N", padx=250)

        sub_title = tk.Label(self, text="Image Steganography")
        sub_title.grid(column=1, row=1)

        button1 = tk.Button(self, text="Encode", font=controller.title_font,
                            command=lambda: controller.show_frame("EncodePage"),
                            width=10, height=2)
        button2 = tk.Button(self, text="Decode", font=controller.title_font,
                            command=lambda: controller.show_frame("DecodePage"),
                            width=10, height=2)
        button1.grid(column=1, row=2, pady=(50, 0), )
        button2.grid(column=1, row=3, pady=(10, 0), )
        
        themes_label = tk.Label(self, text="Theme:", font=tkfont.Font(family='Helvetica'))
        themes_label.grid(column=1, row=4, pady=(50, 0))
         
        theme_options = [color_themes[x][0] for x in range(len(color_themes))]
        selected_theme = StringVar()
        selected_theme.set(current_theme)

        selected_theme.trace("w", lambda *args: update_theme(selected_theme.get()))

        theme_menu = OptionMenu(self, selected_theme, *theme_options)
        theme_menu.grid(column=1, row=5)

class EncodePage(tk.Frame):
    image_path = None
    file_path_string = None
    file_path = None
    max_input_size_string = None
    max_input_size = None
    input_name = None
    input_size = None
    input_size_string = None
    image_name = None
    bit_depth = "1"
    output_path = None
    state = ""
    counter = 0

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.rowconfigure(21, weight=1)
        self.columnconfigure(21, weight=1)

        backbutton = tk.Button(self, text="Back",
                               command=lambda: controller.show_frame("StartPage"))
        backbutton.grid(column=0, row=0, padx=2, pady=2, sticky=SW)
        title = tk.Label(self, text="Encode", font=controller.title_font)
        title.grid(column=2, row=0, padx=50)

        choose_image_label = tk.Label(self, text="Choose Image to Encode:")
        choose_image_label.grid(column=0, row=1, pady=(100, 0))
        choose_image_button = tk.Button(self, text="Choose Image",
                                        command=lambda: self.choose_encode_image())
        choose_image_button.grid(column=0, row=2, pady=10)

        CreateToolTip(choose_image_button, text='Choose the image\n'
                      'that will be encoded with\n'
                      'data from the input file')

        # Label for image name
        self.image_name = StringVar()
        self.image_name.set("")
        image_name_label = tk.Label(self, textvariable=self.image_name,
                                    font=("Helvetica", "8"))
        image_name_label.grid(column=0, row=3)

        # Label for maximum input file name
        self.max_input_size_string = StringVar()
        self.max_input_size_string.set("")
        max_size_label = tk.Label(self,
                                  textvariable=self.max_input_size_string,
                                  font=("Helvetica", "8"))
        max_size_label.grid(column=0, row=4)

        bit_depth_label = tk.Label(self, text="Choose Bitdepth:")
        bit_depth_label.grid(column=1, row=1, padx=20, sticky="S")

        self.bit_depth = StringVar()
        bit_depth_options = [
            "Auto",
            "1",
            "2",
            "3",
            "4",
            "5",
            "6",
            "7",
            "8",
            "Transparent",
        ]
        self.bit_depth.set("Auto")
        bit_depth_menu = OptionMenu(self, self.bit_depth, *bit_depth_options)
        bit_depth_menu.grid(column=1, row=2, padx=20)
        CreateToolTip(bit_depth_menu,
                      text='Choose how many bits of each pixel value\n'
                      'that will be edited\n'
                      'Larger values will lead to more noticeable changes')
        self.bit_depth.trace("w", self.update_max_input_size)

        choose_input_label = tk.Label(self, text='Choose your input file:')
        choose_input_label.grid(column=2, row=1, sticky='S')

        choose_file_button = tk.Button(self, text="Choose File",
                                       command=lambda: self.choose_input_file())
        choose_file_button.grid(column=2, row=2, pady=10)

        # Label for input file name
        self.input_name = StringVar()
        self.input_name.set("")
        input_name_label = tk.Label(self, textvariable=self.input_name,
                                    font=("Helvetica", "8"))
        input_name_label.grid(column=2, row=3)

        # Label for input file size
        self.input_size_string = StringVar()
        self.input_size_string.set("")
        input_size_label = tk.Label(self, textvariable=self.input_size_string,
                                    font=("Helvetica", "8"))
        input_size_label.grid(column=2, row=4)

        # Label for output path label
        choose_output_location = tk.Label(self, text="Choose output location:")
        choose_output_location.grid(column=3, row=1, sticky="S", padx=20)

        # Choose output path button
        choose_output_button = tk.Button(self, text="Choose Location",
                                         command=lambda: self.get_output_path())
        choose_output_button.grid(column=3, row=2)

        # Output Path Label
        self.output_path = StringVar()
        self.output_path.set("")
        output_path_label = tk.Label(self,
                                     textvariable=self.output_path,
                                     font=("Helvetica", "8"))
        output_path_label.grid(column=3, row=3)

        # Encode Button
        encode_button = tk.Button(self, text="ENCODE",
                                  command=lambda: self.encode())
        encode_button.grid(column=4, row=2, padx=20)

        # Log
        steg.logger = logging.getLogger(__name__)
        logging.basicConfig(level=LOG_LEVEL)

        self.scrolled_text = ScrolledText(self, state='disabled', height=12)
        self.scrolled_text.grid(column=0, row=5, columnspan=5,
                                sticky=("SW", "SE"))
        self.scrolled_text.configure(font='TkFixedFont')
        self.scrolled_text.tag_config('INFO', foreground='black')
        self.scrolled_text.tag_config('DEBUG', foreground='gray')
        self.scrolled_text.tag_config('WARNING', foreground='orange')
        self.scrolled_text.tag_config('ERROR', foreground='red')
        self.scrolled_text.tag_config('CRITICAL', foreground='red',
                                      underline=1)
        # Create a logging handler using a queue
        self.log_queue = queue.Queue()
        self.queue_handler = QueueHandler(self.log_queue)
        steg.logger.addHandler(self.queue_handler)
        # Start polling messages from the queue
        self.controller.after(100, self.poll_log_queue)

    def display(self, record):
        msg = self.queue_handler.format(record)
        self.scrolled_text.configure(state='normal')
        self.scrolled_text.insert(tk.END, msg + '\n', record.levelname)
        self.scrolled_text.configure(state='disabled')
        # Autoscroll to the bottom
        self.scrolled_text.yview(tk.END)

    def poll_log_queue(self):
        # Every 1 second we will output the progress
        # on the current step if applicable
        if self.counter >= 10:
            try:
                steg.logger.log(logging.INFO,
                                f'{steg.state}: {int(steg.progress/steg.target*100)}% ({steg.progress}/{steg.target})')
                self.counter = 0
            except ZeroDivisionError:
                pass
        else:
            self.counter += 1
        # Check every 100ms if there is a new message in the queue to display
        while True:
            try:
                record = self.log_queue.get(block=False)
            except queue.Empty:
                break
            else:
                self.display(record)
        self.controller.after(100, self.poll_log_queue)

    def choose_encode_image(self):
        root = tk.Tk()
        root.withdraw()
        filetypes = (
            ('Image Files', '*.png'),
            ('Image Files', '*.jpg'),
            ('All files', '*.*')
        )
        self.image_path = filedialog.askopenfilename(
            initialdir="/",
            filetypes=filetypes
        )
        self.image_name.set(os.path.basename(self.image_path))
        if self.image_path:
            self.update_max_input_size()
        root.destroy()

    def choose_input_file(self):

        root = tk.Tk()
        root.withdraw()
        filetypes = (
            ('All files', '*.*'),
        )
        self.file_path = filedialog.askopenfilename(
            initialdir="/",
            filetypes=filetypes
        )
        self.input_name.set(os.path.basename(self.file_path))
        if self.file_path != "":
            self.input_size = os.path.getsize(self.file_path)
            self.input_size_string.set(f'Input File Size: {self.input_size/1000}KB')
        else:
            self.input_size = 0
            self.input_size_string.set(f'Input File Size: {0}KB')
        root.destroy()

    def get_output_path(self):
        files = [('PNG', '*.png'),]
        if(self.output_path):
            self.output_path.set(filedialog.asksaveasfilename(filetypes=files,
                                                              defaultextension=files))

    def update_max_input_size(self, *args):
        if self.image_path:
            if self.bit_depth.get() == "Transparent":
                self.max_input_size = steg.max_input_size(self.image_path, 0)
                max_input_size_string = f'''\rMax File input size:\r{self.max_input_size/1000}KB'''
                self.max_input_size_string.set(max_input_size_string)
            elif self.bit_depth.get() == "Auto":
                self.max_input_size = steg.max_input_size(self.image_path, 8)
                max_input_size_string = f'''\rMax File input size:\r{self.max_input_size/1000}KB'''
                self.max_input_size_string.set(max_input_size_string)
            else:
                self.max_input_size = steg.max_input_size(self.image_path,
                                                          int(self.bit_depth.get()))
                max_input_size_string = f'''\rMax File input size:\r{self.max_input_size/1000}KB'''
                self.max_input_size_string.set(max_input_size_string)

    def encode(self):
        if self.bit_depth.get() == "Transparent":
            self.bit_depth = "0"
        if(self.image_path and self.file_path and self.bit_depth.get() and
           self.output_path):
            if steg.state == "Done":
                
                # If bit_depth is set to auto check what the
                # lowest possible value is
                if self.bit_depth.get() == "Auto":
                    # Check the lowest bit_depth starting with transparent
                    for i in range(0, 9):
                        if self.input_size < steg.max_input_size(self.image_path,
                                                                 i):
                            self.bit_depth.set(f'{i}')
                            break

                if self.input_size < self.max_input_size:
                    # Create a new thread for the process
                    thread = Thread(target=steg.encode,
                                    args=(self.image_path,
                                          self.file_path,
                                          int(self.bit_depth.get()),
                                          self.output_path.get()))
                    thread.daemon = True
                    thread.start()
                else:
                    steg.logger.log(logging.WARN, "INPUT FILE TOO LARGE")
            else:
                steg.logger.log(logging.WARN, "PROCESS ONGOING")

class DecodePage(tk.Frame):
    image_path = None
    ouput_path = None
    image_name = None
    output_path_string = None

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.rowconfigure(21, weight=1)
        self.columnconfigure(21, weight=1)

        backbutton = tk.Button(self, text="Back",
                               command=lambda: controller.show_frame("StartPage"))
        backbutton.grid(column=0, row=0, padx=2, pady=2, sticky=SW)
        title = tk.Label(self, text="Decode", font=controller.title_font)
        title.grid(column=1, row=0, padx=25)

        choose_image_label = tk.Label(self, text="Choose Image to Decode:")
        choose_image_label.grid(column=0, row=1, pady=(100, 0), padx=(50, 0))
        choose_image_button = tk.Button(self, text="Choose Image",
                                        command=lambda: self.choose_decode_image())
        choose_image_button.grid(column=0, row=2, pady=10)

        self.image_name = StringVar()
        self.image_name.set("")
        image_name_label = tk.Label(self,
                                    textvariable=self.image_name,
                                    font=("Helvetica", "8"))
        image_name_label.grid(column=0, row=3)

        choose_output_label = tk.Label(self, text="Choose Output Folder:")
        choose_output_label.grid(column=1, row=1, sticky="S", padx=20)
        choose_output_button = tk.Button(self, text="Choose Folder",
                                         command=lambda: self.choose_output_folder())
        choose_output_button.grid(column=1, row=2)

        self.output_path_string = StringVar()
        self.output_path_string.set("")
        output_path_label = tk.Label(self,
                                     textvariable=self.output_path_string,
                                     font=("Helvetica", "8"))
        output_path_label.grid(column=1, row=3)

        decode_button = tk.Button(self, text="DECODE",
                                  command=lambda: self.decode())
        decode_button.grid(column=2, row=2)                       

        steg.logger = logging.getLogger(__name__)
        logging.basicConfig(level=LOG_LEVEL)

        self.scrolled_text = ScrolledText(self, state='disabled', height=12)
        self.scrolled_text.grid(column=0,
                                row=5,
                                columnspan=5,
                                sticky=("SW", "SE"))
        self.scrolled_text.configure(font='TkFixedFont')
        self.scrolled_text.tag_config('INFO', foreground='black')
        self.scrolled_text.tag_config('DEBUG', foreground='gray')
        self.scrolled_text.tag_config('WARNING', foreground='orange')
        self.scrolled_text.tag_config('ERROR', foreground='red')
        self.scrolled_text.tag_config('CRITICAL', foreground='red', underline=1)
        # Create a logging handler using a queue
        self.log_queue = queue.Queue()
        self.queue_handler = QueueHandler(self.log_queue)
        steg.logger.addHandler(self.queue_handler)
        # Start polling messages from the queue
        self.controller.after(100, self.poll_log_queue)

    def display(self, record):
        msg = self.queue_handler.format(record)
        self.scrolled_text.configure(state='normal')
        self.scrolled_text.insert(tk.END, msg + '\n', record.levelname)
        self.scrolled_text.configure(state='disabled')
        # Autoscroll to the bottom
        self.scrolled_text.yview(tk.END)

    def poll_log_queue(self):
        # Check every 100ms if there is a new message in the queue to display
        while True:
            try:
                record = self.log_queue.get(block=False)
            except queue.Empty:
                break
            else:
                self.display(record)
        self.controller.after(100, self.poll_log_queue)

    def choose_decode_image(self):
        root = tk.Tk()
        root.withdraw()
        filetypes = (
            ('Image Files', '*.png'),
            ('Image Files', '*.jpg'),
        )
        self.image_path = filedialog.askopenfilename(
            initialdir="/",
            filetypes=filetypes
        )
        self.image_name.set(os.path.basename(self.image_path))
        root.destroy()

    def choose_output_folder(self):
        self.output_path = filedialog.askdirectory()
        self.output_path_string.set(self.output_path)

    def decode(self):
        if self.image_path and self.output_path:
            if(steg.state == "Done"):
                # Create a new thread for the process
                thread = Thread(target=steg.decode,
                                args=(self.image_path, self.output_path))
                thread.daemon = True
                thread.start()

            else:
                steg.logger.log(logging.WARN, "PROCESS ONGOING")

class ToolTip(object):

    def __init__(self, widget):
        self.widget = widget
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0

    def showtip(self, text):
        "Display text in tooltip window"
        self.text = text
        if self.tipwindow or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 57
        y = y + cy + self.widget.winfo_rooty() + 27
        self.tipwindow = tw = Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = Label(tw, text=self.text, justify=LEFT,
                      background="#ffffe0", relief=SOLID, borderwidth=1,
                      font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

def CreateToolTip(widget, text):
    toolTip = ToolTip(widget)

    def enter(event):
        toolTip.showtip(text)

    def leave(event):
        toolTip.hidetip()
    widget.bind('<Enter>', enter)
    widget.bind('<Leave>', leave)

class QueueHandler(logging.Handler):
    """Class to send logging records to a queue

    It can be used from different threads
    """

    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(record)

def load_color_themes() -> None:
    """
    Load the color themes from config/color-themes.ini
    """
    global color_themes
    
    config = configparser.ConfigParser()
    config.read("config/color-themes.ini")
    
    # Add default theme no matter what
    color_themes.append(("Default", "#FFFFFF", "#000000", "#FFFFFF"))
    
    for section in config.sections():
        # If the section has a widget background (wbg) use it, otherwise use the bg
        if config.has_option(section, "wbg"):
            new_theme = (section, config[section]["bg"], config[section]["fg"], config[section]["wbg"])
        else:
            new_theme = (section, config[section]["bg"], config[section]["fg"], config[section]["bg"])
        color_themes.append(new_theme)
  
def update_theme(theme_name: str) -> None:
    """Updates the fg and bg colors of all widgets and frames

    Args:
        theme_name (str): The name of the theme to change the colors to.
    """
    global color_themes
    global current_theme
    current_theme = theme_name
    #Look for the theme name in color_themes
    theme_index = 0
    for i in range(len(color_themes)):
        if color_themes[i][0] == theme_name:
            bg = color_themes[i][1]
            fg = color_themes[i][2]
            wbg = color_themes[i][3]
            break
    else:
        current_theme = "Default"
        bg = "#FFFFFF"
        fg = "#000000"
        wbg = "#FFFFFF"

    save_pref('main', 'Theme', theme_name)
    selected_theme.set(theme_name)
    
    for frame in app.frames.values():
        frame.config(bg=bg)
        for widget in frame.winfo_children():
            if isinstance(widget, tk.Label):
                widget.config(bg=bg, fg=fg)
            elif isinstance(widget, tk.Button):
                widget.config(bg=wbg, fg=fg)
            elif isinstance(widget, OptionMenu):
                widget.config(bg=wbg, fg=fg)
                widget["menu"].config(bg=wbg, fg=fg)
        
        if hasattr(frame, "scrolled_text"):
            frame.scrolled_text.config(bg=wbg)
            frame.scrolled_text.tag_config('INFO', foreground=fg)
            frame.scrolled_text.tag_config('DEBUG', foreground=fg)

def save_pref(section: str, key: str, value: str) -> None:
    """
    Saves the preferences to CONFIG_PATH
    """
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)
    if not section in config.sections():
        config.add_section(section)
    config.set(section, key, value)

    with open(CONFIG_PATH, 'w') as f:
        config.write(f)

def load_pref() -> None:
    """
    Loads the preferences from CONFIG_PATH
    """
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)

    try:
        update_theme(config.get('main', 'theme'))
    except configparser.NoSectionError:
        update_theme("Default")

if __name__ == "__main__":
    global app
    load_color_themes()
    app = App()
    load_pref()
    app.mainloop()
    