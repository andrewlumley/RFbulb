var request = require("request");
var Service, Characteristic;

var spawn = require('child_process').spawn;
var py = spawn('python', ['/Users/andrewlumley/Desktop/Test2.py']);
var data = [1,33,25];
var dataString = '';

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
	request.get({
		url: 'http://192.168.1.171:3000/status'
	}, function(err, response, body) {
		var status = body == 'true' ? true : false;
		callback(null, status);
	}.bind(this));
}

RFbulbAccessory.prototype.setOn = function(on, callback) {
	var url = on ? "on": "off";
	request.get({
		url: 'http://192.168.1.171:3000/' + url
	}, function(err, response, body) {
		callback(null, on);
	}.bind(this));
}

RFbulbAccessory.prototype.getServices = function() {
	return [this.service];
}

