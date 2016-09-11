var request = require("request");
var Service, Characteristic;

var spawn = require('child_process').spawn;
var py = spawn('python', ['/Users/andrewlumley/Desktop/Test2.py']);
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
	if (state == "on") {
		data = [1,33,100];
		dataString = '';
		py.stdout.on('data', function(data) {
			dataString += data.toString();
		});
		py.stdout.on('end', function() {
			this.log(dataString);
		});
		py.stdin.write(JSON.stringify(data));
		py.stdin.end();
		RFstatus = true;
	}
	if (state == "off") {
		data = [1,33,0];
		dataString = '';
		py.stdout.on('data', function(data) {
			dataString += data.toString();
		});
		py.stdout.on('end', function() {
			this.log(dataString);
		});
		py.stdin.write(JSON.stringify(data));
		py.stdin.end();
		RFstatus = false;
	}
	callback(null);
}

RFbulbAccessory.prototype.getServices = function() {
	return [this.service];
}
