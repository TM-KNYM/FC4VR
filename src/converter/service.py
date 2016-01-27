# -*- coding: utf-8 -*-
import numpy as np
import math
import cv2
from converter.settingkey import KEY_OF_C_MAG
from converter.settingkey import KEY_OF_P_MAG
from converter.settingkey import KEY_OF_R
from converter.settingkey import KEY_OF_CENTER_POS

from converter.settingkey import KEY_OF_CODEC
from converter.settingkey import KEY_OF_IN
from converter.settingkey import KEY_OF_OUT
from converter.settingkey import KEY_OF_SIZE
from converter.settingkey import KEY_OF_FPS

SIZE_OF_4K = (3840, 2160)


class ConvertService():

    def __init__(self):
        self.__converter = Converter()

    def buildTable(self):
        self.__converter.buildTable()

    def setSettingsParam(self, key, val):
        self.__converter.setSettingsParam(key, val)

    def doCreatePreviewImage(self):
        return self.__converter.createPreviewImage()

    def doCreateVRVideo(self):
        self.__converter.createVRVideo()


class Settings(object):

    def __init__(self):
        self._settings = self.getSettings()

    def getSettings(self):
        raise NameError('not impl')

    def hasKey(self, key):
        return key in self._settings

    def setParam(self, key, val):
        if not self.hasKey(key):
            raise NameError('not exist')
        self._settings[key] = val


class Converter():

    def __init__(self):
        self.__tableRepo = TableRepository()
        self.__settings = {
                'imgrepo': ImageRepository(),
                'tableBuilder': ConversionTableBuilder(),
                'proc': Processor(),
                }

    def setSettingsParam(self, key, val):
        for setting in self.__settings.values():
            if setting.hasKey(key):
                setting.setParam(key, val)

    def buildTable(self):
        table = self.__settings['tableBuilder'].build()
        self.__tableRepo.setTable(table)

    def createPreviewImage(self):
        table = self.__tableRepo.getTable()
        im = self.__settings['imgrepo'].getFirstFrameImage()
        self.__settings['proc'].createPreviewImage(im, table)

    def createVRVideo(self):
        vd = self.__settings['imgrepo'].getFrames()
        table = self.__tableRepo.getTable()
        self.__settings['proc'].createVRVideo(vd, table)


class ImageRepository(Settings):

    def __init__(self):
        Settings.__init__(self)

    def getSettings(self):
        return {
                KEY_OF_IN: ''
                }

    def getFrames(self):
        return cv2.VideoCapture(self._settings[KEY_OF_IN])

    def getFirstFrameImage(self):
        en, fr = cv2.VideoCapture(self._settings[KEY_OF_IN]).read()
        return fr if en else None


class TableRepository():
    def __init__(self):
        self.__table = None

    def setTable(self, table):
        self.__table = table

    def saveTable(self, fp):
        np.save(fp, self.__table)

    def getTable(self):
        return self.__table


class ConversionTableBuilder(Settings):
    def __init__(self):
        Settings.__init__(self)

    def getSettings(self):
        return {
            KEY_OF_R: 0,
            KEY_OF_CENTER_POS: (0, 0),
            KEY_OF_P_MAG: 0,
            KEY_OF_C_MAG: 0,
            }

    def check(self):
        if self._settings['r'] == 0:
            print('not set r')
            return False
        if (self._settings['centerPos'][0] - self._settings['r']) < 0:
            print('r > x' + str(self._settings['centerPos'][0]))
            return False
        if (self._settings['centerPos'][1] - self._settings['r']) < 0:
            print('r < y' + str(self._settings['centerPos'][1]))
            return False
        if self._settings['pMag'] == 0:
            print('not set p mag')
            return False
        if self._settings['cMag'] == 0:
            print('not set c mag')
            return False
        if self._settings['pMag'] < self._settings['cMag']:
            print('p < c')
            return False
        return True

    def build(self):
        if not self.check():
            raise NameError('error')

        x, y = self._settings[KEY_OF_CENTER_POS]
        r = self._settings[KEY_OF_R]
        pMag = self._settings[KEY_OF_P_MAG]
        cMag = self._settings[KEY_OF_C_MAG]
        top = y - r
        bot = y + r
        left = x - r
        right = x + r
        longSide = int(r * pMag)
        shortSide = int(r * cMag)
        factory = ProjectiveTransferCmdFactory(r, longSide, shortSide)

        side = int(math.ceil(longSide*2))
        co2px = self.createCo2PxFunc(longSide, longSide)
        px2co = self.createPx2CoFunc(x, y)
        table = np.zeros((side, side, 3), np.int)
        for y in range(top, (bot+1)):
            for x in range(left, (right+1)):
                cx, cy = px2co(x, y)
                cmd = factory.createCmd(cx, cy)
                if cmd.canExecute() is True:
                    dst_x, dst_y = cmd.execute()
                    dst_x, dst_y = co2px(dst_x, dst_y)
                    table[dst_y][dst_x] = (1, y, x)
        return table

    def createCo2PxFunc(self, center_x, center_y):

        def co2px(x, y):
            cvt_x = x + center_x-1  # translate co ->px
            cvt_y = center_y - y-1
            return (cvt_x, cvt_y)
        return co2px

    def createPx2CoFunc(self, center_x, center_y):
        cx = center_x
        cy = center_y

        def px2coordinate(x, y):
            cvt_x = x - cx
            cvt_y = -1*(y-cy)
            return (cvt_x, cvt_y)
        return px2coordinate


class Processor(Settings):

    def __init__(self):
        Settings.__init__(self)

    def getSettings(self):
        return {
                    KEY_OF_FPS: 20,
                    KEY_OF_OUT: 'output.avi',
                    KEY_OF_IN: '',
                    KEY_OF_CODEC: cv2.VideoWriter_fourcc(*'XVID'),
                    KEY_OF_SIZE: SIZE_OF_4K
               }

    def __convertVRImgSize(self, im):
        return cv2.resize(self.__expandImg(im), self._settings[KEY_OF_SIZE])

    def setSettingsParam(self, key, ip):
        if key not in self._settings:
            return
        self._settings[key] = ip

    def __expandImg(self, img):
        h, w, tmp = img.shape
        left_img = self.__create_blank_image(int(w/2), h)
        right_img = self.__create_blank_image(int(w/2), h)
        return np.hstack((np.hstack((left_img, img)), right_img))

    def createPreviewImage(self, im, table):
        im = self.__process(im, table)
        return self.__convertVRImgSize(im)

    def createVRVideo(self, vd, table):
        en, fr = vd.read()
        outV = self.__getWriter()
        # while en is True:
        import time
        for i in range(5):
            ss = time.time()
            outImg = self.__process(fr, table)
            print(time.time()-ss)
            outImg = self.__convertVRImgSize(outImg)
            outV.write(outImg)
            en, fr = vd.read()
        if outV is not None:
            outV.release()

    def __getWriter(self):
        return cv2.VideoWriter(self._settings[KEY_OF_OUT],
                               self._settings[KEY_OF_CODEC],
                               self._settings[KEY_OF_FPS],
                               self._settings[KEY_OF_SIZE])

    def __process(self, srcImg, table):
        height, width, t = table.shape
        dstImg = self.__create_blank_image(width, height)

        def lineProc(y, row):
            counter = 0
            preData = None
            for x, info in enumerate(row):
                en, sy, sx = info
                if en == 1:
                    data = srcImg[sy][sx]
                    dstLine = dstImg[y]
                    dstLine[x] = data
                    if preData is not None:
                        if counter > 1:
                            dstLine[x-int(counter/2):x] = data
                            dstLine[x-counter: x-int(counter/2)] = preData
                        elif counter == 1:
                                dstLine[x-1] = preData
                    elif counter > 0:
                        dstLine[x-counter:x] = data
                    counter = 1
                    preData = data
                else:
                    counter = counter+1

        for y, row in enumerate(table):
            lineProc(y, row)

        return dstImg

    def __create_blank_image(self, w, h):
        return np.zeros((h, w, 3), np.uint8)


class TransferCommand():
    def __init__(self, r, longSide, shortSide, pos):
        self._r = r
        self._a = longSide
        self._b = shortSide
        self._x, self._y = pos

    def canExecute(self):
        x = self._x  # x pos
        y = self._y  # y pos
        r = self._r

        if (r*r) <= (y*y):
            return False
        if (r*r) <= (x*x)+(y*y):
            return False
        if math.sqrt(x*x + y*y) <= 0:
            return False
        return True

    def execute(self):
        x = self._x   # x pos
        y = self._y  # y pos
        r = self._r  # raidus
        a = self._a  # Ellipse long side (summit)
        b = self._b  # Ellipse short side (base)
        # slope of vertex
        M = math.sqrt(r*r - (x*x + y*y))/math.sqrt(x*x + y*y)
        sx = math.sqrt((a*a*b*b)/(b*b+a*a*M*M))
        sy = sx*M
        ex = x * sx / math.sqrt((x*x) + (y*y))
        ey = y * sy / math.sqrt((r*r) - ((x*x) + (y*y)))

        ax = math.sqrt((math.pow(a, 2)*math.pow(ex, 2)) / (math.pow(a, 2)-math.pow(ey, 2)))
        cx = math.fabs(ex)
        ay = math.sqrt(math.pow(ax-cx, 2)+math.pow(ey, 2))

        if ex < 0:
            ax = ax*-1
        if ey < 0:
            ay = ay*-1
        return (int(round(ax)), int(round(ey)))


class ProjectiveTransferCmdFactory():

    def __init__(self, r, longSide, shortSide):
        self._r = r
        self._ls = longSide
        self._ss = shortSide

    def createCmd(self, x, y):
        return TransferCommand(self._r, self._ls, self._ss, (x, y))
