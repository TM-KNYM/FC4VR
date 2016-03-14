import tkinter as tk
from tkinter import filedialog
from presenter.presenter import Presenter
from presenter.presenter import ID_NONE, ID_NOTIFY_LOADED_VIDEO
import cv2


class ImageViewer():
    def recivedEvent(self, notifyId):
        if notifyId ==  ID_NOTIFY_LOADED_VIDEO:
            im = self.__presenter.getPreviewImage()
            print(im)
            if im is not None:
                cv2.startWindowThread()
                cv2.namedWindow("preview")
                cv2.imshow("preview", im)

    def __init__(self, presenter):
        self.__presenter = presenter
        self.__presenter.addEventCallback(self.recivedEvent)


class Controller(tk.Frame):

    def __init__(self, master, presenter):
        tk.Frame.__init__(self, master)
        self.pack()
        master.geometry('500x500')
        self.createWidgets()
        self.presenter = presenter

    def createFileDialog(self):
        self.fileFrame = tk.Frame(self)
        self.fileFrame.pack()

        def openDialog():
            path = filedialog.askopenfilename()
            self.presenter.setVideoPath(path)

        self.openDialog = tk.Button(self.fileFrame)
        self.openDialog['command'] = openDialog
        self.openDialog['text'] = 'open'
        self.openDialog.grid(row=0, column=0)
        self.inPutPath = tk.Label(self.fileFrame, text='--')
        self.inPutPath.grid(row=0, column=1)

    def createTableBuildSettings(self):
        self.tableFrame = tk.Frame(self)
        self.tableFrame.pack()
        self.tableLabel = tk.Label(self.tableFrame, text='Convertion Table Settings')
        self.tableLabel.grid(row=0, column=0)
        self.buildButton = tk.Button(self.tableFrame)
        self.buildButton['text'] = 'build'
        self.buildButton.grid(row=0, column=1)

        self.radiusLabel = tk.Label(self.tableFrame, text='Radius')
        self.radiusEntry = tk.Entry(self.tableFrame)
        self.radiusLabel.grid(row=1, column=0)
        self.radiusEntry.grid(row=1, column=1)

        self.magLabel = tk.Label(self.tableFrame, text='mag')
        self.magEntry = tk.Entry(self.tableFrame)
        self.magLabel.grid(row=2, column=0)
        self.magEntry.grid(row=2, column=1)

        self.centerLabel = tk.Label(self.tableFrame, text='Center position X')
        self.centerXEntry = tk.Entry(self.tableFrame)
        self.centerYLabel = tk.Label(self.tableFrame, text='Y')
        self.centerYEntry = tk.Entry(self.tableFrame)
        self.centerLabel.grid(row=3, column=0)
        self.centerXEntry.grid(row=3, column=1)
        self.centerYLabel.grid(row=4, column=0)
        self.centerYEntry.grid(row=4, column=1)

    def createWidgets(self):
        self.createFileDialog()
        self.createTableBuildSettings()

if __name__ == '__main__':
    root = tk.Tk()
    root.title = 'MEZASHI'
    presenter = Presenter()
    viewr = ImageViewer(presenter)

    app = Controller(master=root, presenter=presenter)
    app.mainloop()
