import sdcard
import machine
import time 
import os
from ds3231 import DS3231
from machine_i2c_lcd import I2cLcd
import json

WELCOME_TEXT = 'ONLINE MONITORING v4\nwww.irfomous.com\n\nEWS LONGSOR MALANG'
monthNames = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

def init(i2c, rtc):
    try:
        lcd = I2cLcd(i2c, 0x27, 4, 20)
        lcd.clear()
        lcd.putstr(WELCOME_TEXT)
        time.sleep(1)
        lcd.clear()
    except:
        print('NO LCD')
        lcd = None
    pass


    try:
        rtc2 = DS3231(i2c, 0x68)

        rtc.datetime((2000 + rtc2.getYear(), rtc2.getMonth(), rtc2.getDay(),rtc2.getDayOfWeek,rtc2.getHour(), rtc2.getMinutes(), rtc2.getSeconds(),0))

    except Exception as e:
        rtc2 = None
        print('#ERROR RTC:', e)
    pass

    return (lcd, rtc2)


def updateLCD(rtc, DATA,lcd):
    if (lcd == None):
        return
    dt = rtc.datetime()
    day = dt[2]
    month = dt[1]
    year = dt[0]
    hour = dt[4]
    minutes = dt[5]
    seconds = dt[6]
 
    lcd.move_to(0, 0)
    if (DATA['SD'] == False and seconds % 2 == 0):
                #12345678901234567890
        lcd.putstr('  **SDCARD ERROR**  ')
    else:
        lcd.putstr('%02d %s %02d %02d:%02d:%02d' % (day,  monthNames[month-1],  year , hour,  minutes, seconds))

    try:
        lcd.move_to(0,1)
        lcd.putstr('RI: %5d RC: %6d' % ((DATA['arr_count'] - DATA['arr_last']) * 6, DATA['arr_count']))
    except Exception as e:
        print(e)
        pass
    
    try:
        lcd.move_to(0,2)
        lcd.putstr('TX: %+5.1f TY:  %+4.1f' % (DATA.get('tilt_x',-999)/10, DATA.get('tilt_y',-999)/10) )
    except Exception as e:
        print(e)
        pass


    try:
        lcd.move_to(0,3)
        lcd.putstr('EX:  %+04d VI: %5.2f ' % (DATA.get('extenso',-999) ,((DATA['volt_1'] / 4095) * 1.1 * 21) + 0.8))
    except:
        pass

  

def writeSD(rtc, DATA, vspi):

    dt = rtc.datetime()
    
    dtx = '%04d-%02d-%02d' % (dt[0], dt[1], dt[2])
    
    try:
        sd = sdcard.SDCard(vspi, machine.Pin(5))
    except Exception as e:
        return False
    

    i = 0
    while True:
        try:
            i = i +1
            if (i > 10):
                break

            os.mount(sd, '/sd')
      
            break
        except OSError as e:
            
            pass
        except Exception as e:
            return False
 
    try:    
        os.chdir('/sd')
    except Exception as e:
        pass

    try:
        f = open('.send_' + dtx + '.log','a')
        f.write(json.dumps(DATA))
        f.write("\r\n\r\n")
        f.close()
    except Exception as e:
        print('ERROR: .send', e)
        pass
    
    
    return True



def writeARRSD(rtc, DATA, vspi):

    dt = rtc.datetime()
    
    dtx = '%04d-%02d-%02d' % (dt[0], dt[1], dt[2])
    
    try:
        sd = sdcard.SDCard(vspi, machine.Pin(5))
    except Exception as e:
        return False

    

    i = 0
    while True:
        try:
            i = i +1
            if (i > 10):
                break

            os.mount(sd, '/sd')
      
            break
        except OSError as e:
            pass
        except Exception as e:
            return False

    
    try:    
        os.chdir('/sd')
    except Exception as e:
        pass

    #arr
    try:
        f = open('arr_' + dtx + '.csv','a')
        f.write('%04d-%02d-%02d,%02d:%02d:%02d,%d,%d\n' % (dt[0], dt[1], dt[2], dt[4], dt[5], dt[6], DATA['arr_intensity'],DATA['arr_count'] ) )
        f.close()
    except Exception as e:
        print('ERROR: arr', e)
        pass

    
    
    

    return True

def parseCommand(cmd,rtc,rtc2):
    try:
        parts= cmd.split()
            
        if (parts[0] == "t" and len(parts) == 7):
            rtc.datetime([int(parts[1]),int(parts[2]),int(parts[3]),1,int(parts[4]),int(parts[5]),int(parts[6]),0])
           
            dt = rtc.datetime()
            print('%04d-%02d-%02d %02d:%02d:%02d' % (dt[0], dt[1], dt[2], dt[4], dt[5], dt[6]))
            
            rtc2.setDateTime(int(parts[1]),int(parts[2]),int(parts[3]),1,int(parts[4]),int(parts[5]),int(parts[6]))
           
    except Exception as e:
        print(e)    
    
        pass

