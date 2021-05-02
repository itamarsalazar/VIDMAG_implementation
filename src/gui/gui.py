import os
import tkinter
import PIL.Image
import PIL.ImageTk
from tkinter import filedialog

import gui.constants as c
from gui.helpers import MyVideoCapture
from processing.processing import vidmag_fn


class App:
    def __init__(self, window, window_title, vid_source=c.INIT_VIDEO_SOURCE):

        self.window = window
        self.window.title(window_title)
        self.window.iconbitmap(c.ICON_DIR)

        self.video_source = vid_source
        self.video_output = ""
        self.filename = ""

        # open video source
        self.vid_original = MyVideoCapture(self.video_source)
        self.vid_result = MyVideoCapture(self.video_source)

        # grid
        self.frame_vid = tkinter.Frame(self.window)
        self.frame_vid.grid(row=0, column=0)
        self.frame_buttons_nav = tkinter.Frame(self.window)
        self.frame_buttons_nav.grid(row=1, column=0)
        self.frame_buttons = tkinter.Frame(self.window)
        self.frame_buttons.grid(row=2, column=0, sticky=tkinter.W)

        # Create a canvas that fits video source
        self.canvas_1 = tkinter.Canvas(self.frame_vid, width=self.vid_original.width, height=self.vid_original.height)
        self.canvas_1.grid(row=0, column=0)
        self.canvas_2 = tkinter.Canvas(self.frame_vid, width=self.vid_result.width, height=self.vid_result.height)
        self.canvas_2.grid(row=0, column=1)

        # To select video
        self.label_1 = tkinter.Label(self.frame_buttons, text="Video source:")
        self.label_1.grid(row=0, column=0, sticky="sw", padx=10)
        self.path = tkinter.StringVar()
        self.entry_1 = tkinter.Entry(self.frame_buttons, textvariable=self.path, width=30).grid(row=0, column=1,
                                                                                                padx=10)
        self.btn_search = tkinter.Button(self.frame_buttons, text="...", command=self.search_file)
        self.btn_search.grid(row=0, column=2)

        # algorithm parameters
        self.label_2 = tkinter.Label(self.frame_buttons, text="Alpha:")
        self.label_2.grid(row=1, column=0, sticky=tkinter.W, padx=10)
        self.alpha = tkinter.DoubleVar()
        self.alpha.set(c.DEFAULT_ALPHA)
        self.entry_2 = tkinter.Entry(self.frame_buttons, textvariable=self.alpha, width=30).grid(row=1, column=1,
                                                                                                 padx=10)

        self.label_3 = tkinter.Label(self.frame_buttons, text="Lambda:")
        self.label_3.grid(row=2, column=0, sticky=tkinter.W, padx=10)
        self.lambda_c = tkinter.DoubleVar()
        self.lambda_c.set(c.DEFAULT_LAMBDA_C)
        self.entry_3 = tkinter.Entry(self.frame_buttons, textvariable=self.lambda_c, width=30).grid(row=2, column=1,
                                                                                                    padx=10)

        self.label_4 = tkinter.Label(self.frame_buttons, text="Low freq. (Hz):")
        self.label_4.grid(row=3, column=0, sticky=tkinter.W, padx=10)
        self.FL = tkinter.DoubleVar()
        self.FL.set(c.DEFAULT_FL)
        self.entry_4 = tkinter.Entry(self.frame_buttons, textvariable=self.FL, width=30).grid(row=3, column=1, padx=10)

        self.label_5 = tkinter.Label(self.frame_buttons, text="High freq. (Hz):")
        self.label_5.grid(row=4, column=0, sticky=tkinter.W, padx=10)
        self.FH = tkinter.DoubleVar()
        self.FH.set(c.DEFAULT_FH)
        self.entry_5 = tkinter.Entry(self.frame_buttons, textvariable=self.FH, width=30).grid(row=4, column=1, padx=10)

        self.label_6 = tkinter.Label(self.frame_buttons, text="Chrom. Att.:")
        self.label_6.grid(row=5, column=0, sticky=tkinter.W, padx=10)
        self.chrom_att = tkinter.DoubleVar()
        self.chrom_att.set(c.DEFAULT_CHROM_ATTENUATION)
        self.entry_6 = tkinter.Entry(self.frame_buttons, textvariable=self.chrom_att, width=30).grid(row=5, column=1,
                                                                                                     padx=10)
        self.label_7 = tkinter.Label(self.frame_buttons, text="# levels:")
        self.label_7.grid(row=6, column=0, sticky=tkinter.W, padx=10)
        self.nlevels = tkinter.IntVar()
        self.nlevels.set(c.DEFAULT_NLEVELS)
        self.entry_7 = tkinter.Entry(self.frame_buttons, textvariable=self.nlevels, width=30).grid(row=6, column=1,
                                                                                                   padx=10)
        # visualization button
        self.btn_visualize = tkinter.Button(self.frame_buttons, text="Visualize", width=20, command=self.visualize)
        self.btn_visualize.grid(row=0, column=3, sticky=tkinter.E)

        # processing button
        self.btn_process = tkinter.Button(self.frame_buttons, text="Processing", width=20, command=self.process)
        self.btn_process.grid(row=1, column=3, sticky=tkinter.E)

        # play video buttons
        self.btn_original = tkinter.Button(self.frame_buttons_nav, text="Original", width=40,
                                           command=self.visualize_original)
        self.btn_original.grid(row=0, column=0, sticky=tkinter.E)

        self.btn_res = tkinter.Button(self.frame_buttons_nav, text="Result", width=40, command=self.visualize_result)
        self.btn_res.grid(row=0, column=1, sticky=tkinter.W)

        # After it is called once, the update method will be automatically called every delay milliseconds
        self.delay = int(1000 / self.vid_original.fps)
        self.update()

        self.window.mainloop()

    def process(self):
        parameters = {
            'alpha': self.alpha.get(),
            'lambda_c': self.lambda_c.get(),
            'fl': self.FL.get(),
            'fh': self.FH.get(),
            'samplingRate': self.vid_original.fps,
            'chromAttenuation': self.chrom_att.get(),
            'nlevels': self.nlevels.get(),
        }
        # Function that process video using vidmag
        self.video_output = vidmag_fn(self.video_source, parameters)
        self.vid_result.vid.release()
        self.vid_result = MyVideoCapture(self.video_output)
        self.vid_original.vid.release()
        self.vid_original = MyVideoCapture(self.video_source)

    def visualize(self):
        if not self.path.get() == "" and not self.path.get() == "0":
            self.video_source = self.path.get()
            self.vid_original.vid.release()
            self.vid_original = MyVideoCapture(self.video_source)
            self.canvas_1.config(width=int(self.vid_original.width / 2), height=int(self.vid_original.height / 2))
            self.canvas_2.config(width=int(self.vid_original.width / 2), height=int(self.vid_original.height / 2))
        else:
            pass

    def visualize_original(self):
        self.vid_original.vid.release()
        self.vid_original = MyVideoCapture(self.video_source)

    def visualize_result(self):
        if os.path.exists(self.video_output):
            self.vid_result.vid.release()
            self.vid_result = MyVideoCapture(self.video_output)

    def update(self):
        # Get a frame from the video source
        ret, frame = self.vid_original.get_frame()

        if ret:
            self.photo_1 = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(frame))
            self.canvas_1.create_image(0, 0, image=self.photo_1, anchor=tkinter.NW)

        ret, frame = self.vid_result.get_frame()

        if ret:
            self.photo_2 = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(frame))
            self.canvas_2.create_image(0, 0, image=self.photo_2, anchor=tkinter.NW)

        self.delay = int(1000/self.vid_original.fps)
        self.window.after(self.delay, self.update)

    def search_file(self):
        self.filename = tkinter.filedialog.askopenfilename(initialdir=c.RAW_VIDEO_DIR, title="Select file",
                                                           filetypes=(("mp4 files", "*.mp4"), ("all files", "*.*")))
        print(self.filename)
        self.path.set(self.filename)
