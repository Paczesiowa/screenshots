// Dom2Img v. 0.1
// author: paczesiowa@gmail.com
// https://github.com/Paczesiowa/dom2img
//
// Library for taking screenshots of currently displayed html
// rendering is done on a backend using PhantomJS
// (see README on github for backend part of this library)
//
// This library needs jQuery.
//
// usage: Dom2Img.screenshot(opts);
// opts can be either an url where the backend handler is installed,
// or a dict with some of these keys:
//   * url - see above - required
//   * callback - jquery.ajax success callback. data param will
//                contain whatever your backend handler returns
//                (see README on github for more info)
//   * error - jquery.ajax error callback
//   * dataType - jquery.ajax dataType param
//   * zoom - number with zoom level. Backend part can use this
//            to resize screenshots. Useful for mobile devices
//            where virtual viewport size can be bigger than
//            actual screen size. If you don't provide this,
//            but you include detect-zoom.js (from
//            https://github.com/tombigel/detect-zoom), Dom2Img
//            will use that. If there's no detect-zoom.js and
//            no zoom param, zoom will default to 1.
//            2 means that the virtual viewport is twice as big
//            as the screen size.
//   * scale - number (int). If you want backend to scale the screenshot
//             (in addition to scaling for zoom level), use this
//             param as a percentage number - 50 means, you'll get
//             a screenshot 50% as big (= two times smaller).
//             If you don't have imagemagick on the backend,
//             this (and zoom) params will be ignored.
//   * params - extra post params
window.Dom2Img = (function() {

  // Grabs doctype from current page
  // TODO: polish
  var get_doctype = function() {
    var doctype = '<!DOCTYPE ' + document.doctype.name;
    doctype += (document.doctype.publicId ? ' PUBLIC "' + document.doctype.publicId + '"' : '');
    doctype += (document.doctype.systemId ? ' "' + document.doctype.systemId + '"' : '') + '>';
    return doctype;
  };

  // get html tag from current page
  // TODO: finish
  var get_html_node = function() {
    return '<html>';
  };

  // get DOM's html of current page
  var dom_html = function() {
    var doctype = get_doctype();
    var html_node = get_html_node();
    var html_inner = document.body.parentNode.innerHTML;
    return doctype + html_node + html_inner + '</html>';
  };

  // get offsets of current view position from left/top of the document
  var get_offsets = function() {
    var get_offset = function(window_offset_prop, doc_elem_scroll_prop) {
      if (window[window_offset_prop] !== undefined) {
        return window[window_offset_prop];
      }
      var doc_elem = document.documentElement;
      if (doc_elem && doc_elem[doc_elem_scroll_prop]) {
        return doc_elem[doc_elem_scroll_prop];
      } else {
        return document.body.scrollTop;
      }
    };

    return {top: get_offset('pageYOffset', 'scrollTop'),
            left: get_offset('pageXOffset', 'scrollLeft')};
  };

  // get current zoom level (useful on mobile devices)
  var get_zoom = function() {
    if (window.detectZoom !== undefined) {
      var zoom_inv = detectZoom.zoom();
      if (zoom_inv === 0) {
        // crapy result from detect-zoom library, fallback to no zoom
        return 1;
      } else {
        return 1 / zoom_inv;
      }
    } else {
      // no detect-zoom.js available, default to no zoom
      return 1;
    }
  };

  // return size of virtual viewport
  var get_viewport_size = function() {
    var docElem = document.documentElement;
    var width = Math.max(docElem['clientWidth'], window['innerWidth']);
    var height = Math.max(docElem['clientHeight'], window['innerHeight']);
    return {width: width, height: height};
  };

  // get desired scale percentage (including zoom)
  var get_scale = function(zoom, scale) {
    if (zoom === undefined) {
      zoom = get_zoom();
    }
    var result = 100 / zoom;
    if (scale !== undefined) {
      result *= scale / 100;
    }
    return Math.round(result);
  };

  var screenshot = function(opts) {
    var url, callback, error_callback, dataType, zoom, scale, extra_params = {};
    if (typeof opts === 'string') {
      url = opts;
      callback = function() {};
      error_callback = callback;
    } else {
      url = opts['url'];
      callback = opts['callback'];
      if (callback === undefined) {
        callback = function() {};
      }
      error_callback = opts['error'];
      if (error_callback === undefined) {
        error_callback = function() {};
      }
      dataType = opts['dataType'];
      zoom = opts['zoom'];
      scale = opts['scale'];
      extra_params = opts['params'];
    }

    var content = dom_html();
    var offsets = get_offsets();
    scale = get_scale(zoom, scale);
    var viewport_size = get_viewport_size();

    var data = {content: content,
                height: viewport_size.height,
                width: viewport_size.width,
                top: offsets.top,
                left: offsets.left,
                scale: scale};

    $.ajax({type: 'POST', url: url, data: $.extend(data, extra_params),
            success: callback, error: error_callback, dataType: dataType});
  };

  return {screenshot: screenshot};
}());
