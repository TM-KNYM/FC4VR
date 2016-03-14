from presenter.converter import service, settingkey

ID_NONE = 'none'
ID_NOTIFY_LOADED_VIDEO = 'load_video'


class EventNotifier():

    def __init__(self):
        self.__callbackList = list()

    def notifyEvent(self, notifyId=ID_NONE):
        for func in self.__callbackList:
            func(notifyId)

    def addCallBack(self, func):
        self.__callbackList.append(func)

    def removeCallback(self, func):
        self.__callbackList.remove(func)


class Presenter():

    def __init__(self):
        self.service = service
        self.notifier = EventNotifier()

    def setVideoPath(self, path=None):
        self.service.setSettingsParam(settingkey.KEY_OF_IN, path)
        self.notifier.notifyEvent(ID_NOTIFY_LOADED_VIDEO)

    def getPreviewImage(self):
        return self.service.doCreatePreviewImage()

    def addEventCallback(self, func):
        self.notifier.addCallBack(func)

    def removeCallback(self, func):
        self.notifier.removeCallback(func)

