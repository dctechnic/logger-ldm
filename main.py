import machine
import time 
import os
from machine_i2c_lcd import I2cLcd
from ds3231 import DS3231

from machine import Pin, ADC, UART, WDT, ADCBlock
import sdcard
import struct
from uModBusSerial import uModBusSerial
from machine import WDT
import errno 
import json
import sys
import select

wdt = WDT(timeout=60000)  # enable it with a timeout of 2s
#                                                         12345678901234567890
WELCOME_TEXT = 'ONLINE MONITORING v4\nwww.irfomous.com\n\nLDM MONITORING'

DATA = {'SD': True}
DATAS = []

ROUTER_pin = Pin(25, Pin.OUT, value = 0)
S1_pin = Pin(26, Pin.OUT, value = 1)
S2_pin = Pin(27, Pin.OUT, value = 1)
S3_pin = Pin(14, Pin.OUT, value = 1)

ADC1 = ADC(Pin(36))
ADC2 = ADC(Pin(39))


S1_pin.value(1)
S2_pin.value(1)
S3_pin.value(1)

def updateLCD():
    if (lcd == 0):
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
        lcd.putstr('LDM1: %08.1f mm' % (DATA.get('LDM1',-1)))
    except:
        pass

    try:
        lcd.move_to(0,2)
        lcd.putstr('LDM2: %08.1f mm' % (DATA.get('LDM2',-1)))
    except:
        pass

  
    try:
        lcd.move_to(0,3)
        lcd.putstr('%.02fV %.02f^C' % (DATA.get('volt',-10)/100,DATA.get('rtc_temp',-1)))
    except:
        pass

  

def writeSD():


    dt = rtc.datetime()
    
    dtx = '%04d-%02d-%02d' % (dt[0], dt[1], dt[2])
    
    try:
        sd = sdcard.SDCard(vspi, machine.Pin(5))
    except Exception as e:
        print('1',e)
        DATA['SD'] = False
        return
    

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
            DATA['SD'] = False
            print('2',e)
            return
 
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

    #awlr
    try:
        f = open('ldm_' + dtx + '.csv','a')
        f.write('%04d-%02d-%02d,%02d:%02d:%02d,%.1f,%.1f\n' % (dt[0], dt[1], dt[2], dt[4], dt[5], dt[6], DATA['LDM1'], DATA['LDM2'] ) )
        f.close()
    except Exception as e:
        print('ERROR: ', e)
        pass
    
    
    DATA['SD'] = True

    return 0


def to_float(r1,r2):
    a = r1.to_bytes(2,'big')
    b = r2.to_bytes(2,'big')
    out = struct.unpack('!f', a + b)
    return out[0] 

def to_int32(r1,r2):
    a = r1.to_bytes(2,'big')
    b = r2.to_bytes(2,'big')
    out = struct.unpack('!i', a + b)
    return out[0]

def DAQ_SYS():
    adb2 = ADCBlock(1,bits=12)
    volt = adb2.connect(2).read_uv();
    volt = (volt / 10000) * 20;
    DATA['volt'] = volt;
    
    try:
        t = i2c.readfrom_mem(0x68, 0x11, 2)
        i = t[0] << 8 | t[1]
        input_value = i >> 6
        mask = 2 ** (10 - 1)
        temp = -(input_value & mask) + (input_value & ~mask)
        DATA['rtc_temp'] = temp * 0.25
    except:
        pass


def DAQ1():

    # LDM 1
    slave_id = 8
    try:
        resp = mb.read_holding_registers(slave_id,0,2)
        
        temp = to_int32(resp[0],resp[1]) / 10
        if (temp < 0):
            raise Exception("Invalid DATA")

        DATA['LDM1'] = to_int32(resp[0],resp[1]) / 10

        dt = rtc.datetime()
        DATA['LDM1_t'] =  '%04d-%02d-%02d %02d:%02d:%02d' % (dt[0], dt[1], dt[2], dt[4], dt[5], dt[6])
        print(json.dumps(DATA))
        S1_pin.value(0)
    except Exception as e:
        DATA['LDM1'] = -1
        print('#ERROR LDM1')
        pass


    return
    
def DAQ2():

    slave_id = 1
    try:
        resp = mb.read_holding_registers(slave_id,0,4)
        
        temp = to_float(resp[1],resp[2]) * 1000;
        
        if (temp > 9000000):
            raise Exception("Invalid DATA")
    
        DATA['LDM2'] = temp
        dt = rtc.datetime()
        DATA['LDM2_t'] =  '%04d-%02d-%02d %02d:%02d:%02d' % (dt[0], dt[1], dt[2], dt[4], dt[5], dt[6])
        print(json.dumps(DATA))
        S2_pin.value(0)
        
    except Exception as e:
        print(e)
        DATA['LDM2'] = -1
        print('#ERROR LDM2')
        pass



    return
    
    
def onRouter():
    ROUTER_pin.value(0)
    return

def offRouter():
    ROUTER_pin.value(1)
    return


def timer1Sec():
    
    dt = rtc.datetime()
    
    try:
        updateLCD()
    except:
        pass
    

    if (dt[6] % 10 ==  0):
        if (S2_pin.value() == 1):
            DAQ2()
        elif (S1_pin.value() == 1):
            DAQ1()
        
    

    if (dt[6] == 0):
        DATA['t'] =  '%04d-%02d-%02d %02d:%02d:%02d' % (dt[0], dt[1], dt[2], dt[4], dt[5], dt[6])    
        DAQ_SYS();
        m = dt[5] % 10
        if (m == 0 or m == 5):
            try:
                print('LDM1 ON')
                DATA.pop('LDM1_t')
            except:
                pass
            
            S2_pin.value(0)
            S1_pin.value(1)
        elif (m == 4 or m == 9):
            try:
                print('LDM2 ON')
                DATA.pop('LDM2_t')
            except:
                pass
            
            S1_pin.value(0)
            S2_pin.value(1)
        else:
            S1_pin.value(0)
            S2_pin.value(0)
            
        print(json.dumps(DATA))
        writeSD()

    
    # reset router tiap jam 0 0 0
    # 
    if (dt[6] == 0 and dt[5] == 0):
        offRouter()
        time.sleep(5)
        onRouter()


def parseCommand(cmd):
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


# Start Init

i2c = machine.I2C(0,sda=machine.Pin(21),scl=machine.Pin(22))
try:
    lcd = I2cLcd(i2c, 0x27, 4, 20)
    lcd.clear()
    lcd.putstr(WELCOME_TEXT)
    time.sleep(2)
    lcd.clear()
    lcd.backlight_off()
except:
    print('NO LCD')
    lcd = 0
    pass


rtc = machine.RTC()

try:
    rtc2 = DS3231(i2c, 0x68)

    rtc.datetime((2000 + rtc2.getYear(), rtc2.getMonth(), rtc2.getDay(),rtc2.getDayOfWeek,rtc2.getHour(), rtc2.getMinutes(), rtc2.getSeconds(),0))

except Exception as e:
    
    print('#ERROR RTC:', e)
    pass




monthNames = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

vspi = machine.SPI(2)

try:
    sd = sdcard.SDCard(vspi, machine.Pin(5))
except Exception as e:
    print(e)
    DATA['SD'] = False
    pass
    

mb = uModBusSerial(2,pins=(17,16))

buff = bytearray()

lastTick =time.ticks_ms()

lastTick2 =time.ticks_ms()

try:
    updateLCD()
except:
    pass
# Main LOOP

DAQ_SYS();
DAQ1()
DAQ2()

while True:
    wdt.feed()

    now = time.ticks_ms()
    if (time.ticks_diff( now,lastTick) > 1000):
        lastTick = now
        timer1Sec()

    while sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
        ch = sys.stdin.read(1)
        buff.extend(ch)
       
        pos = bytes(buff).find(b'\n')
        if (pos > -1):
            cmd = bytes(buff).decode('utf-8').strip()
            if (cmd):
                parseCommand(cmd)
            buff = bytearray()
                
            
      


# NOTES

# SET EC ADDR:  mb.write_single_register(1,0x14,2);
# SET PH ADDR:  mb.write_single_register(1,0x19,3);
# SET TEMP_RIKA ADDR:

