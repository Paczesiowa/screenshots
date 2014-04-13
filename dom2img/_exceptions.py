class Dom2ImgError(Exception):
    pass


class PhantomJSFailure(Dom2ImgError):

    def __init__(self, return_code, stderr=None):
        self.return_code = return_code
        self.stderr = stderr

    def __str__(self):
        result = u'PhantomJS failed with status ' + str(self.return_code)
        if self.stderr:
            result += u', and stderr output:\n' + self.stderr
        return result


class PhantomJSTimeout(Dom2ImgError):

    def __init__(self, timeout):
        self.timeout = timeout

    def __str__(self):
        return u'PhantomJS process has been killed, ' + \
            u'because it took longer than ' + str(self.timeout) + \
            u' seconds to finish'
