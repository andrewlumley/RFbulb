var Service, Characteristic;

var data = [10,10,10];
var dataString = '';

var RFstatus = true;

module.exports = function(homebridge) {
	Service = homebridge.hap.Service;
	Characteristic = homebridge.hap.Characteristic;

	homebridge.registerAccessory("homebridge-RFbulb", "RFbulb", RFbulbAccessory);
}

function RFbulbAccessory(log, config) {
	this.log = log;
	this.config = config;
	this.name = config["name"];
	this.address = config["address"];

	this.service = new Service.Lightbulb(this.name);
	this.service
		.getCharacteristic(Characteristic.On)
		.on('get', this.getOn.bind(this))
		.on('set', this.setOn.bind(this));
}

RFbulbAccessory.prototype.getOn = function(callback) {
	callback(null, RFstatus);
}

RFbulbAccessory.prototype.setOn = function(on, callback) {
	var state = on ? "on": "off";
	var spawn = require('child_process').spawn;
	var py = spawn('python', ['/home/pi/Desktop/RFbulb/nRF24L01PLUS.py']);
	if (state == "on") {
		this.log("Setting " + this.name + " to " + state) // Temp
		data = [1,parseInt(this.address, 10),100];
		dataString = '';
		py.stdout.on('data', function(data) {
			dataString += data.toString();
		});
		py.stdout.on('end', function() {
			console.log(dataString);
		});
		py.stdin.write(JSON.stringify(data));
		py.stdin.end();
		RFstatus = true;
		this.log(this.name + " set to " + state)
	}
	if (state == "off") {
		this.log("Setting " + this.name + " to " + state) // Temp
		data = [1,parseInt(this.address, 10),0];
		dataString = '';
		py.stdout.on('data', function(data) {
			dataString += data.toString();
		});
		py.stdout.on('end', function() {
			console.log(dataString);
		});
		py.stdin.write(JSON.stringify(data));
		py.stdin.end();
		RFstatus = false;
		this.log(this.name + " set to " + state)
	}
	callback(null);
}

RFbulbAccessory.prototype.getServices = function() {
	return [this.service];
}
