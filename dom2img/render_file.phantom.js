// Dom2Img v. 0.1
// author: paczesiowa@gmail.com
// https://github.com/Paczesiowa/dom2img
//
// This script accepts html as standard input and returns png screenshot as standard output.
// There is absolutely no input error handling.
//
// usage: phantom.js render_file.phantom.js width height top left [cookie_domain cookie_string]
// width, height, top, left are integers (using pixels unit) and are required parameters:
//   * width: virtual viewport's width
//   * height: virtual viewport's height
//   * top: scroll offset from the top of the page
//   * left: scroll offset from the left border of the page
// cookie_domain and cookie_string are optional string parameters
// if cookie_string is present, cookie_domain must be as well
//   * cookie_domain: cookie domain for cookies values from cookie_string
//   * cookie_string: semi-colon separated cookie values using key=val format
//
// example usage:
// phantom.js render_file.phantom.js 1920 1080 1000 0 127.0.0.1 key1=val1;key2=val2

var system = require('system');
var page = require('webpage').create();

var width = system.args[1];
var height = system.args[2];
var top = system.args[3];
var left = system.args[4];
var cookie_domain = system.args[5];
var cookie_string = system.args[6];

var cookies = {};
if (cookie_string !== undefined) {
  var cookie_elems = cookie_string.split(';');
  for (var i = 0; i < cookie_elems.length; i++) {
    var cookie = cookie_elems[i].split('=');
    var cookie_key = cookie.shift();
    var cookie_value = cookie.join('=');
    cookies[cookie_key] = cookie_value;
  }
}
for (var key in cookies) {
  var value = cookies[key];
  phantom.addCookie({name: key,
                     value: value,
                     domain: cookie_domain});
}

var content = system.stdin.read();

page.viewportSize = { width: width, height: height };
page.clipRect = { top: top, left: left, width: width, height: height };

page.content = content;

page.onLoadFinished = function() {
  page.render('/dev/stdout');
  phantom.exit();
};
