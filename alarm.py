from machine import Pin
import yx5300 as cmd


class Alarm:
    def __init__(self, lcd, mp3_uart):
        
        self.lcd = lcd
        self.awasTimeout =0
        self.awasCount = 0
        self.siagaTimeout = 0
        self.waspadaTimeout= 0
        self.alarmTimeout = 0
        
        self.mp3_uart = mp3_uart
        self.S1_pin = Pin(26, Pin.OUT, value = 0);


    def getStatus(self):
        if (self.alarmTimeout > 0):
            if (self.waspadaTimeout > 0):
                return 1
            else:
                return 2
        else:
            return 0
            
    def timer1Sec(self):

        #print('#INFO', self.alarmTimeout, self.waspadaTimeout, self.siagaTimeout, self.awasTimeout)

        if (self.waspadaTimeout > 0):
            self.waspadaTimeout -= 1

        if (self.siagaTimeout > 0):
            self.siagaTimeout -= 1

        if (self.awasTimeout > 0):
            self.awasTimeout -= 1

        if (self.alarmTimeout > 0):
            self.alarmTimeout -= 1
            if (self.alarmTimeout == 0):
                print("#INFO: ALARM  STOP" )
                self.stop();

        
        
    def waspada(self, force=False):
        
        if (not force and self.waspadaTimeout > 0):
            return
        
        self.S1_pin.value(1)

        self.alarmTimeout = 120;
        self.mp3_uart.write(cmd.set_volume(30))
        
        self.mp3_uart.write(cmd.play_track(2))
        self.waspadaTimeout = 3600
        print("#INFO: WASPADA");
        
        pass
    
    def siaga(self, force=False):
        if (not force and self.siagaTimeout > 0):
            return

    
        self.S1_pin.value(1)

        self.alarmTimeout = 120;
        self.mp3_uart.write(cmd.set_volume(30))
        self.mp3_uart.write(cmd.play_track(1))
        self.siagaTimeout = 3600
        print("#INFO: SIAGA");
        pass
    
    def awas(self, force=False):

        if (not force and self.awasTimeout > 0):
            return 0
        
        print("#INFO: AWAS");
        self.S1_pin.value(1)

        self.mp3_uart.write(cmd.set_volume(30))
        self.mp3_uart.write(cmd.play_track(3))
        self.alarmTimeout = 180;
        self.awasTimeout = 360;
        
        self.awasCount += 1;
        if (self.awasCount > 2):
            self.awasCount = 0
            return 1
        else:
            return 0
    
    def stop(self):
        
        self.S1_pin.value(0)

        self.mp3_uart.write(cmd.stop())
        print("#INFO: STOP");
        pass