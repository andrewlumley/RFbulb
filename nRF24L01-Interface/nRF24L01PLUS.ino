#include <SPI.h>

int CSNpin = 10;
int CEpin = 9;
int IRQpin = 3;

int function; //1 is RX, 0 is TX
bool packet = false;

void setup() {
  RFsetup("RX",33); //initialize nRF24L01+ as RX with the address ending with "33"
  pinMode(13, OUTPUT);
  //Serial.begin(57600);
}

void loop() {
  if (function == 0) { //TX
    delay(1000);
    RFwrite(100);
    delay(100);
    if (packet == true) {
      int data;
      SPIsetup();
      digitalWrite(CSNpin, LOW);
      SPI.transfer(0x61); //R_RX_PAYLOAD read
      data = SPI.transfer(0xff); //read payload
      digitalWrite(CSNpin, HIGH);
      SPI.end();
      delayMicroseconds(20);
      clearSTATUS();
      delayMicroseconds(20);
      packet = false;
      // Do something with STATUS (data)
      //Serial.print("Ack Received: ");
      //Serial.println(data);
    }
    clearSTATUS();
    delayMicroseconds(20);
    clearTX();
  }
  if (function == 1) { //RX
    RFlisten();
    
    if (packet == true) {
      digitalWrite(CEpin, LOW);  
  
      if (digitalRead(13) == HIGH) {
          SPIsetup();
          SPIcommand2(0xa8,0x64); //W_ACK_PAYLOAD write (100)
          SPI.end();
      }
      if (digitalRead(13) == LOW) {
        SPIsetup();
        SPIcommand2(0xa8,0x00); //W_ACK_PAYLOAD write (0)
        SPI.end();   
      }
      
      int data;
      delayMicroseconds(20);
      SPIsetup();
      digitalWrite(CSNpin, LOW);
      SPI.transfer(0x61); //R_RX_PAYLOAD read
      data = SPI.transfer(0xff); //read payload
      digitalWrite(CSNpin, HIGH);
      SPI.end();
      delayMicroseconds(20);
      clearSTATUS();
      delayMicroseconds(20);
      digitalWrite(CEpin, HIGH);
      packet = false;
      Serial.println(data);
      if (data == 0) {
        digitalWrite(13, LOW);
      }
      if (data == 100) {
        digitalWrite(13, HIGH);
      }
    }    
  }
}

void SPIsetup() {
  SPI.begin();
  SPI.setBitOrder(MSBFIRST);
  SPI.setClockDivider(SPI_CLOCK_DIV16);
}

void RFsetup(String mode, byte address) {
  pinMode(CSNpin, OUTPUT);
  pinMode(CEpin, OUTPUT);
  pinMode(IRQpin, INPUT);
  detachInterrupt(1);
  
  digitalWrite(CSNpin, HIGH); //CSN is active low
  digitalWrite(CEpin, LOW); //No RX or TX at this time
  
  SPIsetup();
  SPIcommand2(0x20,0x08); //CONFIG write (power down)
  delayMicroseconds(200);
  
  if (mode == "RX") {
    function = 1;
    attachInterrupt(1, packet_received, FALLING); //Interrupt for received packets
    SPIcommand2(0x20,0x3f); //CONFIG write (power up & RX)
    delayMicroseconds(50);
    SPIcommand6(0x30,address,0xb6,0xb5,0xb4,0xb3); //TX_ADDR write (0xB3B4B5B6__)
    delayMicroseconds(50);
    SPIcommand6(0x2a,address,0xb6,0xb5,0xb4,0xb3); //RX_ADDR_P0 write (0xB3B4B5B6__)
  }
  if (mode == "TX") {
    function = 0;
    attachInterrupt(1, packet_received, FALLING); //Interrupt for received ack packets
    SPIcommand2(0x20,0x3e); //CONFIG write (power up & TX with payload IRQ)
    delayMicroseconds(50);
    SPIcommand2(0x21,0x01); //EN_AA write (enable P0)
    delayMicroseconds(50);
    SPIcommand2(0x24,0x23); //SETUP_RETR write (enable 750us delay)
    delayMicroseconds(50);
    SPIcommand6(0x30,address,0xb6,0xb5,0xb4,0xb3); //TX_ADDR write (0xB3B4B5B6__)
    delayMicroseconds(50);
    SPIcommand6(0x2a,address,0xb6,0xb5,0xb4,0xb3); //RX_ADDR_P0 write (0xB3B4B5B6__)
  }

  delayMicroseconds(50);
  SPIcommand2(0x22,0x01); //EN_RXADDR write (enable P0)
  delayMicroseconds(50);
  SPIcommand2(0x3d,0x06); //FEATURE write (enable EN_ACK_PAYLOAD and EN_DPL) //
  delayMicroseconds(50);
  SPIcommand2(0x3c,0x01); //DYNPD write (enable DPL_P0) //
  delayMicroseconds(50);
  SPIcommand2(0x31,0x01); //RX_PW_P0 write (1 byte RX width)
  delayMicroseconds(50);
  SPIcommand2(0x25,0x32); //RF_CH write (channel 50)
  delayMicroseconds(50);
  SPIcommand2(0x26,0x22); //RFSETUP write (250kbps & -12dBm)
  delayMicroseconds(50); 
  SPIcommand2(0x27,0x7e); //STATUS write (Interrupts Clear)
  SPI.end(); 
}

void RFwrite(byte command) {
  SPIsetup();
  SPIcommand2(0xa0,command); //W_TX_PAYLOAD write (Payload)
  SPI.end();
  digitalWrite(CEpin, HIGH);
  delayMicroseconds(15);
  digitalWrite(CEpin, LOW);
}

void RFlisten() {
  digitalWrite(CEpin, HIGH);
}

void packet_received() {
  packet = true;
}

void readSTATUS() {
  SPIsetup();
  SPIcommand2(0x07,0xff); //STATUS read
  SPI.end();
}

void clearSTATUS() {
  SPIsetup();
  SPIcommand2(0x27,0x7e);
  SPI.end(); 
}

void clearRX() {
  SPIsetup();
  SPIcommand(0xe2);
  SPI.end(); 
}

void clearTX() {
  SPIsetup();
  SPIcommand(0xe1);
  SPI.end(); 
}

void SPIcommand(byte command) {
  digitalWrite(CSNpin, LOW);
  SPI.transfer(command); //command
  digitalWrite(CSNpin, HIGH);
}

void SPIcommand2(byte command, byte value) {
  digitalWrite(CSNpin, LOW);
  SPI.transfer(command); //register write command
  SPI.transfer(value); //register value
  digitalWrite(CSNpin, HIGH);
}

void SPIcommand6(byte command, byte value1, byte value2, byte value3, byte value4, byte value5) {
  digitalWrite(CSNpin, LOW);
  SPI.transfer(command); //register write command
  SPI.transfer(value1); //register value 1
  SPI.transfer(value2); //register value 2
  SPI.transfer(value3); //register value 3
  SPI.transfer(value4); //register value 4
  SPI.transfer(value5); //register value 5
  digitalWrite(CSNpin, HIGH);
}
