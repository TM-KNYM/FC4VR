from converter import service
from converter.settingkey import KEY_OF_C_MAG
from converter.settingkey import KEY_OF_P_MAG
from converter.settingkey import KEY_OF_R
from converter.settingkey import KEY_OF_CENTER_POS

from converter.settingkey import KEY_OF_IN
from converter.settingkey import KEY_OF_OUT

if __name__ == '__main__':

    fp = 'video/test.avi'
    center_pos = (539, 1078)
    r = 523
    out = 'result.avi'
    peripheral_mag = 1.2
    center_mag = 0.6

    core = service
    core.setSettingsParam(KEY_OF_R, r)
    core.setSettingsParam(KEY_OF_CENTER_POS, center_pos)
    core.setSettingsParam(KEY_OF_C_MAG, center_mag)
    core.setSettingsParam(KEY_OF_P_MAG, peripheral_mag)
    core.buildTable()

    core.setSettingsParam(KEY_OF_IN, fp)
    core.setSettingsParam(KEY_OF_OUT, 'out.avi')
    im = core.doCreateVRVideo()
