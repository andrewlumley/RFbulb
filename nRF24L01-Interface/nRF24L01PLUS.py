import sys, json
import spidev, time, RPi.GPIO as GPIO

CSNpin = 17
CEpin = 27
IRQpin = 22

function = 0 #1 is RX, 0 is TX
packet = False

spi = spidev.SpiDev()

def SPIsetup():
    spi.open(0,1) #open spi port 0, device (CS) 1
    spi.max_speed_hz = 976000 #set SPI speed of 976 kHz
    spi.mode = 0b00 #set SPI mode 0

def SPIcommand(command):
    GPIO.output(CSNpin,GPIO.LOW) #Write 0 (LOW) to the CSN pin
    spi.writebytes([command])
    GPIO.output(CSNpin,GPIO.HIGH) #Write 1 (HIGH) to the CSN pin

def SPIcommand2(command,value):
    GPIO.output(CSNpin,GPIO.LOW) #Write 0 (LOW) to the CSN pin
    spi.writebytes([command,value])
    GPIO.output(CSNpin,GPIO.HIGH) #Write 1 (HIGH) to the CSN pin

def SPIcommand6(command,value1,value2,value3,value4,value5):
    GPIO.output(CSNpin,GPIO.LOW) #Write 0 (LOW) to the CSN pin
    spi.writebytes([command,value1,value2,value3,value4,value5])
    GPIO.output(CSNpin,GPIO.HIGH) #Write 1 (HIGH) to the CSN pin

def RFwrite(command):
    SPIsetup()
    SPIcommand2(0xa0,command) #W_TX_PAYLOAD write (Payload)
    spi.close()
    GPIO.output(CEpin,GPIO.HIGH)
    time.sleep(20.0/1000000.0)
    GPIO.output(CEpin,GPIO.LOW)

def readSTATUS():
    SPIsetup()
    SPIcommand2(0x07,0xff) #STATUS read
    spi.close()

def clearSTATUS():
    SPIsetup()
    SPIcommand2(0x27,0x7e)
    spi.close()

def clearTX():
    SPIsetup()
    SPIcommand(0xe1)
    spi.close()

def packet_received(channel):
    global packet
    packet = True
    
def RFsetup(mode,address):
    GPIO.setmode(GPIO.BCM) # Broadcom pin-numbering scheme
    GPIO.setup(CSNpin,GPIO.OUT) #Set CSN pin to 1 (OUTPUT)
    GPIO.setup(CEpin,GPIO.OUT) #Set CE pin to 1 (OUTPUT)
    GPIO.setup(IRQpin,GPIO.IN) #Set IRQ pin to 0 (INPUT)

    GPIO.output(CSNpin,GPIO.HIGH) #CSN is active low
    GPIO.output(CEpin,GPIO.LOW) #No RX or TX at this time

    SPIsetup()
    SPIcommand2(0x20,0x08); #CONFIG write (power down)
    time.sleep(200.0/1000000.0)

    if mode == "RX":
        function = 1
        GPIO.add_event_detect(IRQpin, GPIO.FALLING, callback=packet_received)
        SPIcommand2(0x20,0x3f) #CONFIG write (power up & RX)
        time.sleep(30.0/1000000.0)
        SPIcommand6(0x30,address,0xb6,0xb5,0xb4,0xb3) #TX_ADDR write (0xB3B4B5B6__)
        time.sleep(30.0/1000000.0)
        SPIcommand6(0x2a,address,0xb6,0xb5,0xb4,0xb3) #RX_ADDR_P0 write (0xB3B4B5B6__)

    if mode == "TX":
        function = 0
        GPIO.add_event_detect(IRQpin, GPIO.FALLING, callback=packet_received)
        SPIcommand2(0x20,0x3e) #CONFIG write (power up & TX with payload IRQ)
        time.sleep(30.0/1000000.0)
        SPIcommand2(0x21,0x01) #EN_AA write (enable P0)
        time.sleep(30.0/1000000.0)
        SPIcommand2(0x24,0x23) #SETUP_RETR write (enable 750us delay)
        time.sleep(30.0/1000000.0)
        SPIcommand6(0x30,address,0xb6,0xb5,0xb4,0xb3) #TX_ADDR write (0xB3B4B5B6__)
        time.sleep(30.0/1000000.0)
        SPIcommand6(0x2a,address,0xb6,0xb5,0xb4,0xb3) #RX_ADDR_P0 write (0xB3B4B5B6__)

    time.sleep(30.0/1000000.0)
    SPIcommand2(0x22,0x01) #EN_RXADDR write (enable P0)
    time.sleep(30.0/1000000.0)
    SPIcommand2(0x3d,0x06) #FEATURE write (enable EN_ACK_PAYLOAD and EN_DPL)
    time.sleep(30.0/1000000.0)
    SPIcommand2(0x3c,0x01) #DYNPD write (enable DPL_P0)
    time.sleep(30.0/1000000.0)
    SPIcommand2(0x31,0x01) #RX_PW_P0 write (1 byte RX width)
    time.sleep(30.0/1000000.0)
    SPIcommand2(0x25,0x32) #RF_CH write (channel 50)
    time.sleep(30.0/1000000.0)
    SPIcommand2(0x26,0x22) #RFSETUP write (250kbps & -12dBm)
    time.sleep(30.0/1000000.0) 
    SPIcommand2(0x27,0x7e) #STATUS write (Interrupts Clear)
    time.sleep(30.0/1000000.0) 
    SPIcommand(0xe1) #FLUSH_TX
    time.sleep(30.0/1000000.0) 
    SPIcommand(0xe2) #FLUSH_RX
    spi.close()

def main(): #Main funciton called by Node.JS class
    global packet
    lines = sys.stdin.readlines()
    lines = json.loads(lines[0])

    try:
        if (lines[0] == 0): # RX
            RFsetup("RX",lines[1]) #setup nRF24L01+ as RX
            print("Package Received Successfuly")
            
        if (lines[0] == 1): # TX
            RFsetup("TX",lines[1]) #setup nRF24L01+ as TX
            time.sleep(30.0/1000000.0)
            RFwrite(lines[2]) #transmit data packet
            time.sleep(1.0/10.0)
            if (packet == True):
                SPIsetup()
                GPIO.output(CSNpin,GPIO.LOW) #Write 0 (LOW) to the CSN pin
                spi.writebytes([0x61])
                data = int(spi.readbytes(1)[0])
                GPIO.output(CSNpin,GPIO.HIGH) #Write 1 (HIGH) to the CSN pin
                spi.close()
                time.sleep(30.0/1000000.0)
                clearSTATUS()
                packet = False
                print("Package Transmitted Successfuly")
            else:
                clearSTATUS()
                time.sleep(30.0/1000000.0)
                clearTX()
                print("There was a transmission error")
           
        if (lines[0] == 10): # STATUS
            RFsetup("TX",lines[1]) #setup nRF24L01+ as TX
            time.sleep(30.0/1000000.0)
            RFwrite(0xff) #transmit STATUS packet
            time.sleep(1.0/10.0)
            if (packet == True):
                SPIsetup()
                GPIO.output(CSNpin,GPIO.LOW) #Write 0 (LOW) to the CSN pin
                spi.writebytes([0x61])
                data = int(spi.readbytes(1)[0])
                GPIO.output(CSNpin,GPIO.HIGH) #Write 1 (HIGH) to the CSN pin
                spi.close()
                time.sleep(30.0/1000000.0)
                clearSTATUS()
                packet = False
                print(data)
            else:
                clearSTATUS()
                time.sleep(30.0/1000000.0)
                clearTX()
                print("There was an error in determining the state")
    finally:
        GPIO.cleanup()

#start process
if __name__ == '__main__':
    main()
