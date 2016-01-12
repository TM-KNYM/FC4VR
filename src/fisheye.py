# -*- coding: utf-8 -*-
from PIL import Image
import numpy as np
import math
import cv2


def load_image(fp):
    return Image.open(fp)


def create_blank_image(w, h):
    return np.zeros((h, w, 3), np.uint8)


class EllipseShiftCalculator():

    def __init__(self, r, longSide, shortSide):
        self._r = r
        self._a = longSide
        self._b = shortSide

    def setPos(self, x, y):
        self._x = x
        self._y = y

    def canExecute(self):
        x = self._x  # x pos
        y = self._y  # y pos
        r = self._r

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
        sx = x * sx / math.sqrt((x*x) + (y*y))
        sy = y * sy / math.sqrt((r*r) - ((x*x) + (y*y)))
        return (int(round(sx)), int(round(sy)))


def createCo2PxFunc(width, height):
    w = width
    h = height

    def co2px(x, y):
        cvt_x = x + int(w/2)-1  # translate co ->px
        cvt_y = int(h/2) - y-1
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


class ImageShifter():

    def __init__(self, calc, px2co, co2px):
        self.px2co = px2co
        self.co2px = co2px
        self.cmd = calc
        self.tmp_list = []
        print('cmd init')

    def createMap(self, srcImg):
        w, h, clr = srcImg.shape
        pxMap = []
        for y in range(0, h):
            for x in range(0, w):
                cx, cy = self.px2co(x, y)
                cmd = self.cmd
                cmd.setPos(cx, cy)
                if cmd.canExecute() is True:
                    dst_x, dst_y = cmd.execute()
                    dst_x, dst_y = self.co2px(dst_x, dst_y)
                    pxMap.append({'src': (x, y), 'dst': (dst_x, dst_y)})
        return pxMap


def createPxShiftMap(srcImg, peripheral_mag, center_mag, r, center_pos):
    center_x, center_y = center_pos
    longSide = int(r * peripheral_mag)
    shortSide = int(r * center_mag)
    calc = EllipseShiftCalculator(r, longSide, shortSide)

    # create dst image
    side = longSide*2
    co2px = createCo2PxFunc(side, side)
    px2co = createPx2CoFunc(center_x, center_y)

    shfiter = ImageShifter(calc, px2co, co2px)
    return shfiter.createMap(srcImg)

def arrangePosition(srcImg, dstImg, pxMap):
    for px in pxMap:
        dx, dy = px['dst']
        sx, sy = px['src']
        dstImg[dx][dy] = srcImg[sx][sy]

def expandImg(img):
    w, h, tmp = img.shape
    left_img = create_blank_image(int(w/2), h)
    right_img = create_blank_image(int(w/2), h)
    return np.hstack((np.hstack((left_img, img)), right_img))

def doFisheyeCorrection4Img(fp, peripheral_mag, center_mag, op, r, center_pos):
    center_x, center_y = center_pos
    im = load_image(fp).crop((center_x-r, center_y-r, r*2, r*2))
    srcImg = np.asarray(im, dtype=np.uint8)
    print(srcImg.shape)

    # shift
    longSide = int(r * peripheral_mag)
    shortSide = int(r * center_mag)
    calc = EllipseShiftCalculator(r, longSide, shortSide)

    # create dst image
    side = longSide*2
    co2px = createCo2PxFunc(side, side)
    px2co = createPx2CoFunc(center_x, center_y)

    shfiter = ImageShifter(calc, px2co, co2px)
    pxMap = shfiter.createMap(srcImg)

    resultImg = create_blank_image(side, side)
    for px in pxMap:
        dx, dy = px['dst']
        sx, sy = px['src']
        resultImg[dx][dy] = srcImg[sx][sy]

    h, w, tmp = resultImg.shape
    # expand 360 from 180
    left_img = create_blank_image(int(w/2), h)
    right_img = create_blank_image(int(w/2), h)
    print(left_img.shape)
    print(right_img.shape)
    resultImg = np.hstack((np.hstack((left_img, resultImg)), right_img))
    print(resultImg.shape)

    from PIL import ImageFilter
    Image.fromarray(np.uint8(resultImg)).filter(ImageFilter.GaussianBlur).filter(ImageFilter.MedianFilter(size=5)).resize((1920, 1080)).save(op, 'JPEG')


def doFisheyeCorrection4Video(fp, peripheral_mag, center_mag, op, r, center_pos):
    vd = cv2.VideoCapture('video/sample.3gp')
    k4 = (3840, 2160) # 3840x2160
    en, fr = vd.read()
    x, y = center_pos
    top = y - r
    bot = y + r
    left = x - r
    right = x + r
    pxMap = None
    outV = None
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    while en is True:
        crop_fr = fr[top:bot, left:right]

        if pxMap is None:
            pxMap = createPxShiftMap(crop_fr, peripheral_mag, center_mag, r, (r, r)) 
            side = r * peripheral_mag * 2
        outImg = create_blank_image(side, side)
        arrangePosition(crop_fr, outImg, pxMap)
        outImg = cv2.medianBlur(outImg, 5)
        outImg = expandImg(outImg)
        outImg = cv2.resize(outImg, k4)
        print(outImg.shape)
        if outV is None:
            oh, ow, tmp = outImg.shape
            outV = cv2.VideoWriter(op, fourcc, 25.0, k4)
        outV.write(outImg)
        en, fr = vd.read()
    outV.release()

def captureFirstFrame(fp, out):
    vd = cv2.VideoCapture('video/sample.3gp')
    en, fr = vd.read()
    Image.fromarray(np.uint8(fr)).save(out, 'JPEG')

if __name__ == '__main__':
    # load img date
    # fp = 'koala.jpg'
    # args

    # size 1800
    # R = 900
    '''
    # for Image
    fp = 'image/koala_min.jpg'
    peripheral_mag = 0.8
    center_mag = 0.3
    op = 'result.jpg'
    center_pos = (900, 900)
    R = 900

    doFisheyeCorrection4Img(fp, peripheral_mag, center_mag, op, R, center_pos)
    print('comp')
    '''

    # first capture
    captureFirstFrame(fp='video/sample.3gp', out='1.jpg')
    
    center_pos = (531, 1110)
    r = 510
    fp = 'video/sample.3gp'
    out = 'result.avi'
    peripheral_mag = 1.2
    center_mag = 0.6
    doFisheyeCorrection4Video(fp, peripheral_mag, center_mag, op=out, r=r, center_pos=center_pos)
