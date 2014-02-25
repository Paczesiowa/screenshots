from subprocess import Popen, PIPE

from flask import Flask, request


app = Flask(__name__)
app.debug = True
app.testing = True


def call_script_get_output(args, stdin):
    proc = Popen(args, stdin=PIPE, stdout=PIPE)
    return proc.communicate(stdin)[0]


@app.route('/protected_static/<path:path>', methods=['GET'])
def protected_static(path):
    if request.cookies.get('lang') == 'LANG_EN':
        return app.send_static_file(path)
    else:
        return '', 404


@app.route('/screenshot', methods=['POST'])
def root():
    post = request.form
    content = post['content']
    height = post['height']
    width = post['width']
    top = post['top']
    left = post['left']
    scale = post['scale']

    prefix = 'http://127.0.0.1:7000'

    # using python
    from dom2img import dom2img
    cookies = dict(request.cookies)  # optional argument
    with open('/tmp/content.html', 'w') as f:
        f.write(content)
    print height, width, top, left, scale, prefix
    return 'ok'
    # screenshot = dom2img(content, height, width, top, left,
    #                      scale, prefix, cookies=cookies)

    # using script
    # cli_args = ['./dom2img.py', height, width, top, left, scale,
    #             prefix, "cookie1=val1;cookie2=val2"]
    # screenshot = call_script_get_output(cli_args, stdin=content)

    # you can save your screenshot
    # with open('/tmp/content.png', 'w') as f:
    #     f.write(screenshot)

    # return it base64 encoded
    from base64 import b64encode
    from flask import jsonify
    result = {'screenshot': b64encode(screenshot)}
    return jsonify(**result)

    return 'ok'


if __name__ == "__main__":
    app.run(threaded=True, port=7000)
