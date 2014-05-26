// Dom2Img v. 0.1
// author: paczesiowa@gmail.com
// https://github.com/Paczesiowa/dom2img
//
// This script accepts html as standard input and returns png screenshot as standard output.
// There is absolutely no input error handling.
//
// usage: phantomjs render_file.phantom.js WIDTH HEIGHT TOP LEFT [COOKIE_DOMAIN COOKIE_STRING] [--debug]
// width, height, top, left are integers (using pixels unit) and are required parameters:
//   * WIDTH: virtual viewport's width
//   * HEIGHT: virtual viewport's height
//   * TOP: scroll offset from the top of the page
//   * LEFT: scroll offset from the left border of the page
// COOKIE_DOMAIN and COOKIE_STRING are optional string parameters
// if COOKIE_STRING is present, COOKIE_DOMAIN must be as well
//   * COOKIE_DOMAIN: cookie domain for cookies values from cookie_string
//   * COOKIE_STRING: semicolon separated cookie values using key=val format
// optional flag --debug (as a last parameter) enables interactive debug mode
//
// example usage:
// phantomjs render_file.phantom.js 1920 1080 1000 0 127.0.0.1 key1=val1;key2=val2

var system = require('system');
var page = require('webpage').create();

var width = system.args[1];
var height = system.args[2];
var top = system.args[3];
var left = system.args[4];
var cookie_domain = system.args[5];
var cookie_string = system.args[6];
var debug = system.args[5] === '--debug' || system.args[7] === '--debug';

var cookies = null;
if (cookie_string !== undefined && cookie_string !== '') {
  cookies = {};
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
page.viewportSize = {width: width, height: height};
page.clipRect = {top: top, left: left, width: width, height: height};

if (debug) {
  var start = new Date();
  debugger;
  var stop = new Date();
  if (stop - start < 1000) {
    // execution didn't stop at debugger stmt - first (auto) run
    console.log('\n\n\n');
    console.log('dom2img PhantomJS debug mode enabled.\n');
    console.log('Viewport size: ' + width + 'x' + height);
    console.log('Scroll offsets (left:top): ' + left + ':' + top);
    if (cookies !== null) {
      console.log('Cookie domain: ' + cookie_domain);
      console.log('Cookies:');
      for (var cookie_key in cookies) {
        if (!cookies.hasOwnProperty(cookie_key)) {
          break;
        }
        console.log('  ' + cookie_key + ': ' + cookies[cookie_key]);
      }
    }
    console.log('\nPlease follow the instructions:');
    console.log('1. Open (in a Webkit-based browser) http://127.0.0.1:9000/webkit/inspector/inspector.html?page=1');
    console.log('2. Go to console tab');
    console.log('3. type "__run()" (without quotes) and hit enter');
    console.log('4. Open (in a Webkit-based browser) in another browser tab http://127.0.0.1:9000/webkit/inspector/inspector.html?page=3');
    console.log('5. Go back to the first browser tab and unpause script execution');
    console.log('6. In the second browser tab you can debug your HTML');
  } else {
    // execution paused at the debugger statement - __run() was called in the browser
    page.content = content;
  }
} else {
  page.content = content;

  page.onLoadFinished = function() {
    page.render('/dev/stdout');
    phantom.exit();
  };
}
