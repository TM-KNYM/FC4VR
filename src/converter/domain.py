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


class DomainModel():

    def __init__(self):
        self.convManager = ConversionTableManager()
        self.movieUtil = CvMovieUtil()

    def captureFirstFrame(self):
        im = self.movieUtil.getFirstFrameImage()
        return im

    def genTable(self):
        self.convManager.buildTable()

    def setConvertParam(self, key, val):
        self.convManager.setTableParam(key, val)

    def setImageFileParam(self, key, val):
        self.movieUtil.setImgFileParam(key, val)

    def doCreatePreviewImage(self):
        table = self.convManager.getTable()
        im = self.captureFirstFrame()
        im = TableAllcator.arrangePosition(im, table)
        im = self.movieUtil.convertVRImgSize(im)
        return im

    def doCreateVRVideo(self):
        vd = self.movieUtil.getFrames()
        en, fr = vd.read()
        outV = self.movieUtil.getWriter()
        table = self.convManager.getTable()
        # while en is True:
        import time
        for i in range(5):
            ss = time.time()
            outImg = TableAllcator.arrangePosition(fr, table)
            print(time.time()-ss)
            outImg = self.movieUtil.convertVRImgSize(outImg)
            outV.write(outImg)
            en, fr = vd.read()
        if outV is not None:
            outV.release()


class ConversionTableManager():
    def __init__(self):
        self.__table = None
        self.__tableBuilder = ConversionTableBuilder()

    def getTable(self):
        return self.__table

    def setTableParam(self, key, val):
        self.__tableBuilder.setParam(key, val)

    def buildTable(self):
        self.__table = self.__tableBuilder.build()


# ConvertionParam


class ConversionTableBuilder():
    
    def __init__(self):
        self.settings = {
            KEY_OF_R: 0,       
            KEY_OF_CENTER_POS: (0,0),       
            KEY_OF_P_MAG: 0,       
            KEY_OF_C_MAG: 0,       
                }
    
    def setParam(self, key, val):
        if key not in self.settings:
            raise ('not exist key')
        self.settings[key] = val

    def check(self):
        if self.settings['r'] == 0:
            print('not set r')
            return False
        if (self.settings['centerPos'][0] - self.settings['r']) <0 :
            print('r > x' + str(self.settings['centerPos'][0]))
            return False
        if (self.settings['centerPos'][1] - self.settings['r']) <0 :
            print('r < y' + str(self.settings['centerPos'][1]))
            return False
        if self.settings['pMag'] == 0:
            print('not set p mag')
            return False
        if self.settings['cMag'] == 0:
            print('not set c mag')
            return False
        if self.settings['pMag'] < self.settings['cMag']:
            print('p < c')
            return False
        return True

    def build(self):
        
        if not self.check():
            raise NameError('error')

        x, y = self.settings[KEY_OF_CENTER_POS]
        r = self.settings[KEY_OF_R]
        pMag = self.settings[KEY_OF_P_MAG]
        cMag = self.settings[KEY_OF_C_MAG]
        top = y - r
        bot = y + r
        left = x - r
        right = x + r
        longSide = int(r * pMag)
        shortSide = int(r * cMag)
        factory = ProjectiveTransferCmdFactory(r, longSide, shortSide)

        side = int(math.ceil(longSide*2))
        co2px = createCo2PxFunc(longSide, longSide)
        px2co = createPx2CoFunc(x, y)
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

SIZE_OF_4K = (3840, 2160)


class CvMovieUtil():

    def __init__(self):
        self.outPutSettings = {
                    KEY_OF_FPS: 20,
                    KEY_OF_OUT: 'output.avi',
                    KEY_OF_IN: '',
                    KEY_OF_CODEC: cv2.VideoWriter_fourcc(*'XVID'),
                    KEY_OF_SIZE: SIZE_OF_4K
                    }

    def convertVRImgSize(self, im):
        return cv2.resize(self.expandImg(im), self.outPutSettings[KEY_OF_SIZE])

    def setImgFileParam(self, key, ip):
        self.outPutSettings[key] = ip

    def setImgSize(self, size):
        self.size = size

    def getFrames(self):
        return cv2.VideoCapture(self.outPutSettings[KEY_OF_IN])

    def getFirstFrameImage(self):
        en, fr = cv2.VideoCapture(self.outPutSettings[KEY_OF_IN]).read()
        return fr if en else None

    def expandImg(self, img):
        h, w, tmp = img.shape
        left_img = create_blank_image(int(w/2), h)
        right_img = create_blank_image(int(w/2), h)
        return np.hstack((np.hstack((left_img, img)), right_img))

    def setCodec(self, cc):
        self.fourcc = cv2.VideoWriter_fourcc(*cc)

    def getWriter(self):
        return cv2.VideoWriter(self.outPutSettings[KEY_OF_OUT],
                               self.outPutSettings[KEY_OF_CODEC],
                               self.outPutSettings[KEY_OF_FPS],
                               self.outPutSettings[KEY_OF_SIZE])


def create_blank_image(w, h):
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


def createCo2PxFunc(center_x, center_y):

    def co2px(x, y):
        cvt_x = x + center_x-1  # translate co ->px
        cvt_y = center_y - y-1
        return (cvt_x, cvt_y)
    return co2px


def createPx2CoFunc(center_x, center_y):
    cx = center_x
    cy = center_y

    def px2coordinate(x, y):
        cvt_x = x - cx
        cvt_y = -1*(y-cy)
        return (cvt_x, cvt_y)
    return px2coordinate


class TableAllcator():
    @classmethod
    def arrangePosition(self, srcImg, table):
        height, width, t = table.shape
        dstImg = np.zeros((height, width, 3), np.uint8)
        for y, row in enumerate(table):
            counter = 0
            preData = None
            for x, info in enumerate(row):
                en, sy, sx = info
                if en == 1:
                    data = srcImg[sy][sx]
                    dstImg[y][x] = data
                    if preData is not None:
                        if counter != 0 and counter != 1:
                            for i in range(1, int(counter/2)):
                                dstImg[y][x-i] = data
                            for i in range(int(counter/2), counter):
                                dstImg[y][x-i] = preData
                        elif counter == 1:
                                dstImg[y][x-1] = preData
                    elif counter > 0:
                        for i in range(1, counter):
                            dstImg[y][x-i] = data
                    counter = 1
                    preData = data
                else:
                    counter = counter+1
        return dstImg

if __name__ == '__main__':

    fp = 'video/test.3gp'
    center_pos = (539, 1078)
    r = 523
    out = 'result.avi'
    peripheral_mag = 1.2
    center_mag = 0.6

    core = DomainModel()
    core.setConvertParam(KEY_OF_R, r)
    core.setConvertParam(KEY_OF_CENTER_POS, center_pos)
    core.setConvertParam(KEY_OF_C_MAG, center_mag)
    core.setConvertParam(KEY_OF_P_MAG, peripheral_mag)
    core.genTable()

    core.setImageFileParam(KEY_OF_IN, fp)
    core.setImageFileParam(KEY_OF_OUT, 'out.avi')
    im = core.doCreateVRVideo()
    # cv2.imwrite('test.jpg', im)
