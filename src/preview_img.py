from converter import domain
from converter.settingkey import KEY_OF_C_MAG
from converter.settingkey import KEY_OF_P_MAG
from converter.settingkey import KEY_OF_R
from converter.settingkey import KEY_OF_CENTER_POS

from converter.settingkey import KEY_OF_IN
from converter.settingkey import KEY_OF_OUT
import cv2

if __name__ == '__main__':

    fp = 'video/test.3gp'
    center_pos = (539, 1078)
    r = 523
    out = 'result.avi'
    peripheral_mag = 1.2
    center_mag = 0.6

    core = domain
    core.setConvertParam(KEY_OF_R, r)
    core.setConvertParam(KEY_OF_CENTER_POS, center_pos)
    core.setConvertParam(KEY_OF_C_MAG, center_mag)
    core.setConvertParam(KEY_OF_P_MAG, peripheral_mag)
    core.genTable()

    core.setImageFileParam(KEY_OF_IN, fp)
    core.setImageFileParam(KEY_OF_OUT, 'out.avi')
    im = core.doCreatePreviewImage()
    cv2.imwrite('test.jpg', im)
