import os
import BaseHTTPServer

#Adapted from walkthrough tutorial of 
#Architecture of Open Source Applications
#Chapter 22 - Greg Wilson

class base_case(object):

    def handle_file(self, handler, full_path):
        try:
            with open(full_path, 'rb') as reader:
                content = reader.read()
            handler.send_content(content)
        except IOError as msg:
            msg = "'{0}' cannot be read: {1}".format(full_path, msg)
            handler.handle_error(msg)

    def index_path(self, handler):
        return os.path.join(handler.full_path, 'index1.html')

    def test(self, handler):
        assert False, 'Not Implement'

    def act(self, handler):
        assert False, 'Not Implement'

class case_cgi_file(object):

    def run_cgi(self, handler):

        cmd = "D:\\\"Program Files (x86)\"\\python2\\python " + handler.full_path
        child_stdin, child_stdout = os.popen2(cmd)
        child_stdin.close()
        data = child_stdout.read()
        child_stdout.close()
        handler.send_content(data)

    def test(self, handler):
        return os.path.isfile(handler.full_path) and \
                handler.full_path.endswith('.py')

    def act(self, handler):
        self.run_cgi(handler)

class case_no_file(object):

    def test(self, handler):
        return not os.path.exists(handler.full_path)

    def act(self, handler):
        raise ServerException("'{0}' not found".format(handler.path))


class case_existing_file(base_case):

    def test(self, handler):
        return os.path.isfile(handler.full_path)

    def act(self, handler):
        self.handle_file(handler, handler.full_path)


class case_always_fail(object):

    def test(self, handler):
        return True

    def act(self, handler):
        raise ServerException("Unknown object '{0}'".format(handler.path))


class case_directory_index_file(base_case):

    def index_path(self, handler):
        return os.path.join(handler.full_path, "index1.html")

    def test(self, handler):
        return os.path.isdir(handler.full_path) and \
                os.path.isfile(self.index_path(handler))

    def act(self, handler):
        self.handle_file(handler, self.index_path(handler))


class case_directory_no_index_file(object):

    Listing_Page = """\
        <html>
        <body>
        <ul>
        {0}
        <ul>
        <body>
        <html>
    """

    def list_dir(self, handler, full_path):
        try:
            entries = os.listdir(full_path)
            bullets = ['<li>{0}<li>'.format(e)
                        for e in entries if not e.startswith('.')]
            page = self.Listing_Page.format('\n'.join(bullets))
            handler.send_content(page)
        except OSError as msg:
            msg = "'{0}' cannot be listed: {1}".format(handler.path, msg)
            handler.handle_error(msg)

    def index_path(self, handler):
        return os.path.join(handler.full_path, "index1.html")

    def test(self, handler):
        return os.path.isdir(handler.full_path) and \
                not os.path.isfile(self.index_path(handler))

    def act(self, handler):
        self.list_dir(handler, handler.full_path)



class RequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    Cases = [case_no_file,
             case_cgi_file,
             case_existing_file,
             case_directory_index_file,
             case_directory_no_index_file,
             case_always_fail]

    Error_Page = """\
        <html>
        <body>
        <h1>Error accessing {path}</h1>
        <p>{msg}</p>
        </body>
        </html>
        """

    Listing_Page = """\
        <html>
        <body>
        <ul>
        {0}
        <ul>
        <body>
        <html>
    """

    def list_dir(self, full_path):
        try:
            entries = os.listdir(full_path)
            bullects = ['<li>{0}<li>'.format(e)
                        for e in entries if not e.startswith('.')]
            page = self.Listing_Page.format('\n'.join(bullects))
            self.send_content(page)
        except OSError as msg:
            msg = "'{0}' cannot be listed: {1}".format(self.path, msg)
            self.handle_error(msg)

    def do_GET(self):

        try:
            self.full_path = os.getcwd() + self.path

            for case in self.Cases:
                handler = case()
                if handler.test(self):
                    handler.act(self)
                    break

        except Exception as msg:
            self.handle_error(msg)

    def handle_error(self, msg):
        errorPage = self.Error_Page.format(path=self.path, msg=msg)
        self.send_content(errorPage, 404)

    def send_content(self, content, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

if __name__ == '__main__':
    serverAddress = ('', 8080)
    server = BaseHTTPServer.HTTPServer(serverAddress, RequestHandler)
    server.serve_forever()
