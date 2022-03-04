import logging
import os
import queue
import tkinter as tk
from threading import Thread
from tkinter import LEFT, SOLID, SW, Label, OptionMenu, StringVar, Toplevel, font as tkfont
from tkinter import filedialog
from tkinter.scrolledtext import ScrolledText
from turtle import color, title
import steg

LOG_LEVEL = 20

class App(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        self.title_font = tkfont.Font(family='Helvetica', size=18, weight="bold", slant="italic")

        # the container is where we'll stack a bunch of frames
        # on top of each other, then the one we want visible
        # will be raised above the others
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)
        self.title("Netherizer")

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
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.rowconfigure(21, weight=1)
        self.columnconfigure(21, weight=1)
        label = tk.Label(self, text="NETHERIZER v.0.6", font=controller.title_font)
        label.grid(column=0, row=0, sticky="N")

        button1 = tk.Button(self, text="Encode",
                            command=lambda: controller.show_frame("EncodePage"),
                            width=10, height=2)
        button2 = tk.Button(self, text="Decode",
                            command=lambda: controller.show_frame("DecodePage"),
                            width=10, height=2)
        button1.grid(column=0, row=1, padx=350)
        button2.grid(column=0, row=2, padx=350)


class EncodePage(tk.Frame):
    image_path = None
    file_path_string = None
    file_path = None
    max_input_size_string = None
    max_input_size = None
    input_name = None
    input_size = None
    image_name = None
    bit_depth = "1"
    output_path = None
    state = ""

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
        choose_image_label.grid(column=0, row=1, pady=(100,0))
        choose_image_button = tk.Button(self, text="Choose Image",
                                        command=lambda: self.choose_encode_image())
        choose_image_button.grid(column=0, row=2, pady=10)

        CreateToolTip(choose_image_button, text= 'Choose the image\n'
                                    'that will be encoded with\n'
                                    'data from the input file')

        #Label for image name
        self.image_name = StringVar()
        self.image_name.set("")
        image_name_label = tk.Label(self, textvariable=self.image_name, font=("Helvetica", "8"))
        image_name_label.grid(column=0, row=3)

        #Label for maximum input file name
        self.max_input_size_string = StringVar()
        self.max_input_size_string.set("")
        max_size_label = tk.Label(self, textvariable=self.max_input_size_string, font=("Helvetica", "8"))
        max_size_label.grid(column=0, row=4)

        bit_depth_label = tk.Label(self, text="Choose Bitdepth:")
        bit_depth_label.grid(column=1, row=1, padx=20, sticky="S")

        self.bit_depth = StringVar()
        bit_depth_options = [
            "1",
            "2",
            "3",
            "4",
            "5",
            "6",
            "7",
            "8",
        ]
        self.bit_depth.set("1")
        bit_depth_menu = OptionMenu(self, self.bit_depth, *bit_depth_options)
        bit_depth_menu.grid(column=1, row=2, padx=20)
        CreateToolTip(bit_depth_menu, text='Choose how many bits of each pixel value\n'
                                'that will be edited\n'
                                'Larger values will lead to more noticeable changes')
        self.bit_depth.trace("w", self.update_max_input_size)

        choose_input_label = tk.Label(self, text='Choose your input file:')
        choose_input_label.grid(column=2, row=1, sticky='S')

        choose_file_button = tk.Button(self, text="Choose File",
                                        command=lambda: self.choose_input_file())
        choose_file_button.grid(column=2, row=2, pady=10)

        #Label for input file name
        self.input_name = StringVar()
        self.input_name.set("")
        input_name_label = tk.Label(self, textvariable=self.input_name, font=("Helvetica", "8"))
        input_name_label.grid(column=2, row=3)

        #Label for input file size
        self.input_size = StringVar()
        self.input_size.set("")
        input_size_label = tk.Label(self, textvariable=self.input_size, font=("Helvetica", "8"))
        input_size_label.grid(column=2, row=4)

        #Label for output path label
        choose_output_location = tk.Label(self, text="Choose output location:")
        choose_output_location.grid(column=3, row=1, sticky="S", padx=20)

        #Choose output path button
        choose_output_button = tk.Button(self, text="Choose Location",
                                        command=lambda: self.get_output_path())
        choose_output_button.grid(column=3, row=2)

        #Output Path Label
        self.output_path = StringVar()
        self.output_path.set("")
        output_path_label = tk.Label(self, textvariable=self.output_path, font=("Helvetica", "8"))
        output_path_label.grid(column=3, row=3)

        #Encode Button
        encode_button = tk.Button(self, text="ENCODE",
                           command=lambda: self.encode())
        encode_button.grid(column=4, row=2, padx=20)

        #Log
        steg.logger = logging.getLogger(__name__)
        logging.basicConfig(level = LOG_LEVEL)

        self.scrolled_text = ScrolledText(self, state='disabled', height=12)
        self.scrolled_text.grid(column=0, row=5, columnspan=5, sticky=("SW", "SE"))
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

    def choose_encode_image(self):
        path = ""
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
            max_input_size_string = f'''\rMax File input size:\r{steg.max_input_size_from_path(self.image_path, int(self.bit_depth.get()))/1000}KB'''
            self.max_input_size_string.set(max_input_size_string)
            self.max_input_size = int(steg.max_input_size_from_path(self.image_path, int(self.bit_depth.get()))/1000)
        root.destroy()
    
    def choose_input_file(self):
        path = ""
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
            self.input_size.set(f'Input File Size: {os.path.getsize(self.file_path)/1000}KB')
        else:
            self.input_size.set(f'Input File Size: {0}KB')
        root.destroy()

    def get_output_path(self):
        files = [('PNG', '*.png'),]
        if(self.output_path):
            self.output_path.set(filedialog.asksaveasfilename(filetypes = files, defaultextension = files))

    def update_max_input_size(self, *args):
        if self.image_path:
            max_input_size_string = f'''\rMax File input size:\r{steg.max_input_size_from_path(self.image_path, int(self.bit_depth.get()))/1000}KB'''
            self.max_input_size_string.set(max_input_size_string)
    
    def encode(self):
        #print(self.image_path, self.file_path, int(self.bit_depth.get()), self.output_path)
        if(self.image_path and self.file_path and self.bit_depth.get() and self.output_path):
            if(steg.state == "Ready"):
                #Create a new thread for the process
                thread = Thread(target=steg.encode, args = (self.image_path, self.file_path, 
                                                            int(self.bit_depth.get()), self.output_path.get()))
                thread.daemon = True
                thread.start()
                #thread.join()
                #steg.encode(self.image_path, self.file_path, int(self.bit_depth.get()), self.output_path.get())
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
        title.grid(column=2, row=0, padx=50)

        choose_image_label = tk.Label(self, text="Choose Image to Decode:")
        choose_image_label.grid(column=0, row=1, pady=(100,0))
        choose_image_button = tk.Button(self, text="Choose Image",
                                        command=lambda: self.choose_decode_image())
        choose_image_button.grid(column=0, row=2, pady=10)

        self.image_name = StringVar()
        self.image_name.set("")
        image_name_label = tk.Label(self, textvariable=self.image_name, font=("Helvetica", "8"))
        image_name_label.grid(column=0, row=3)

        choose_output_label = tk.Label(self, text="Choose Output Folder:")
        choose_output_label.grid(column=1, row=1, sticky="S", padx=20)
        choose_output_button = tk.Button(self, text="Choose Folder",
                                        command=lambda: self.choose_output_folder())
        choose_output_button.grid(column=1, row=2)

        self.output_path_string = StringVar()
        self.output_path_string.set("")
        output_path_label = tk.Label(self, textvariable=self.output_path_string, font=("Helvetica", "8"))
        output_path_label.grid(column=1, row=3)

        decode_button = tk.Button(self, text="DECODE",
                                command=lambda: self.decode())
        decode_button.grid(column=2, row=2)                       

        steg.logger = logging.getLogger(__name__)
        logging.basicConfig(level = LOG_LEVEL)

        self.scrolled_text = ScrolledText(self, state='disabled', height=12)
        self.scrolled_text.grid(column=0, row=5, columnspan=5, sticky=("SW", "SE"))
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
        path = ""
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
            if(steg.state == "Ready"):
                #Create a new thread for the process
                thread = Thread(target=steg.decode, args = (self.image_path, self.output_path))
                thread.daemon = True
                thread.start()
                #thread.join()
                #steg.encode(self.image_path, self.file_path, int(self.bit_depth.get()), self.output_path.get())
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
        y = y + cy + self.widget.winfo_rooty() +27
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


if __name__ == "__main__":
    app = App()
    app.mainloop()