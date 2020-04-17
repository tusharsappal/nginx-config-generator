from nginx.nginx import loads, dumps
import unittest

TESTBLOCK_CASE_1 = """
upstream test0 {
    ip_hash;
    server 127.0.0.1:8080;
    keepalive 16;
}
upstream test1{
    server 127.0.0.2:8080;
    keepalive 16;
}
upstream test2
{
    server 127.0.0.3:8080;
    keepalive 16;
}

server {
    listen       80;
    server_name  example.com;

    location = /
    {
        root html;
    }
}
"""

TESTBLOCK_CASE_2 = """
upstream test0 {
    server 1.1.1.1:8080;
    send "some request";
}

upstream test1 {
    server 1.1.1.1:8080;
    send 'some request';
}

server {
    server_name "www.example.com";

    location / {
        root html;
    }
}
"""

TESTBLOCK_CASE_3 = """
upstream test0 {
    server 1.1.1.1:8080;
    check interval=3000 rise=2 fall=3 timeout=3000 type=http;
    check_http_send "GET /alive.html  HTTP/1.0\r\n\r\n";
    check_http_expect_alive http_2xx http_3xx;
}

upstream test1 {
    ip_hash;
    server 2.2.2.2:9000;
    check_http_send 'GET /alive.html  HTTP/1.0\r\n\r\n';
}
"""

TESTBLOCK_CASE_4 = """
upstream xx.com_backend {
    server 10.193.2.2:9061 weight=1 max_fails=2 fail_timeout=30s;
    server 10.193.2.1:9061 weight=1 max_fails=2 fail_timeout=30s;
    session_sticky;
}

server {
    listen 80;

    location / {
        set $xlocation 'test';
        proxy_pass http://xx.com_backend;
    }
}
"""


class TestPythonNginx(unittest.TestCase):

    def test_upstream_count_section(self):
        data = loads(TESTBLOCK_CASE_1)
        self.assertEqual(len(data.filter('Upstream')), 3)

    def test_single_value_keys(self):
        data = loads(TESTBLOCK_CASE_1)
        single_value_key = data.filter('Upstream')[0].keys[0]
        self.assertEqual(single_value_key.name, 'ip_hash')
        self.assertEqual(single_value_key.value, '')

    def test_quoted_key_value(self):
        data = loads(TESTBLOCK_CASE_2)
        out_data = '\n' + dumps(data)
        self.assertEqual(out_data, TESTBLOCK_CASE_2)

    def test_complex_upstream(self):
        inp_data = loads(TESTBLOCK_CASE_3)
        out_data = '\n' + dumps(inp_data)
        self.assertEqual(TESTBLOCK_CASE_3, out_data)

    def test_session_sticky(self):
        inp_data = loads(TESTBLOCK_CASE_4)
        out_data = '\n' + dumps(inp_data)
        self.assertEqual(TESTBLOCK_CASE_4, out_data)


if __name__ == '__main__':
    unittest.main()
