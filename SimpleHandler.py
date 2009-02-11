#!/usr/bin/env python
# encoding: utf-8

# SimpleHandler.py:  minimal web application framework
# 
# Copyright © 2007--2009 William C. Benton 
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import BaseHTTPServer
import types

from urllib import unquote_plus as unquote
from htmlentitydefs import entitydefs
import encodings.ascii
import encodings.aliases
import encodings.latin_1
import encodings.utf_8

import codecs
import traceback

entityxlatr = dict()
OPTIONS = dict()

for k,v in entitydefs.items():
	entityxlatr[v] = k

def quote_entities(data):
	utfdecode = codecs.getdecoder("utf-8")
	
	def escape(char):
		if entityxlatr.has_key(char):
			return "&" + entityxlatr[char] + ";"
		else:
			return char
	udata = data.decode("utf-8")
	ldata = udata.encode("latin-1")
	return "".join(map(escape, ldata))

def query2dict(q):
	"""Turns a query string (whether a GET string or a list of POST parameters) into a dictionary of parameters"""
	def tuplify_one_param(p):
		if p.find("=") == -1:
			return (p, '')
		else:
			ls = p.split("=")
			return (unquote(ls[0]), unquote(ls[1]))
	if type(q) == types.StringType:
		"""GET query string"""
		parampairs = q.split("&")
	else:
		"""POST query string"""
		parampairs = q
	tuples = map(tuplify_one_param, parampairs)
	ret = dict()
	for k,v in tuples:
		ret[k] = v
	return ret

class Tag(object):
	"""Represents a tag in an HTML document"""
	def __init__(self, kind):
		self.kind = kind
		self.contents = []
		self.up2date = False
		self.repr = ""
		self.nocontents = False
		self.params = dict()
	
	def __getitem__(self, key):
		"""docstring for __getitem__"""
		return self.params[key]
	
	def __setitem__(self, key, val):
		"""docstring for __setitem__"""
		self.up2date = False
		self.params[key] = val
	
	def add(self, o):
		self.up2date = False
		self.contents.append(o)
	
	def nocontents(self):
		self.nocontents = True
	
	def stringize_params(self):
		pls = [' %s="%s"' % (k,v) for k,v in self.params.items()]
		return "".join(pls)
		
	def __str__(self):
		"""docstring for __str__"""
		if self.up2date:
			pass
		else:
			if self.nocontents:
				self.repr = "<%s%s/>" % (self.kind, self.stringize_params())
			else:
				opentag = "<%s%s>" % (self.kind, self.stringize_params())
				elts = map(str, self.contents)
				body = "".join(elts)
				closetag = "</%s>\n" % self.kind
				self.repr = opentag + body + closetag
		self.up2date = True
		return self.repr


class SimpleHandler(BaseHTTPServer.BaseHTTPRequestHandler):
	server_version = "SimpleHandler"
			
	def send_ok(self, other_headers=dict()):
		self.send_response(200)
		self.send_header("Content-type", "text/html")
		for k,v in other_headers.items():
			self.send_header(k, v)
		self.end_headers()
	
	def send_redirect(self, url, other_headers=dict()):
		self.send_response(301)
		self.send_header("Location", url)
		self.send_header("Pragma", "no-cache")
		self.send_header("Content-type", "text/html")
		for k,v in other_headers.items():
			self.send_header(k, v)
		self.end_headers()
	
	def do_GET(self):
		try:
			if self.path == '/':
				self.handle_get_index()
			else:
				args = self.path.split("/")
				command = args[1]
				params = args[2:]
				cmdfunc = getattr(self, "handle_get_%s" % command, self.handle_get_fourohfour)
				cmdfunc(args)
		except Exception, e:
			self.send_error(500, "Problem with server:  %s" % str(e))
			self.wfile.write("<pre>\n")
			traceback.print_exc(file=self.wfile)
			self.wfile.write("</pre>")
	
	def do_POST(self):
		try:
			length = int(self.headers['content-length'])
			postdata = self.rfile.read(length)
			self.query = query2dict(postdata)
			try:
				args = self.path.split("/")
				command = args[1]
				params = args[2:]
				cmdfunc = getattr(self, "handle_post_%s" % command, self.handle_post_debug)
				cmdfunc([], postdata)
			except Exception, e:
				self.send_error(500, "Problem with server:  %s" % str(e))
				self.wfile.write("<pre>\n")
				traceback.print_exc(file=self.wfile)
				self.wfile.write("</pre>")
		except Exception, e:
			self.send_error(500, "Problem with POST data: %s" % str(e))
			self.wfile.write("<pre>\n")
			traceback.print_exc(file=self.wfile)
			self.wfile.write("</pre>")
	
	def handle_post_debug(self, args, postdata=None):
		self.handle_get_debug(args, postdata)
	
	def handle_get_debug(self, args, postdata=None):
		self.send_ok()
		
		self.wfile.write("<html>\n")
		self.wfile.write("<head><title>Hello, world!</title></head>\n")
		self.wfile.write("<body>\n")
		self.wfile.write("<pre>\n")
		
		self.wfile.write("COMMAND:\n")
		self.wfile.write("========\n")
		self.wfile.write(self.command + " " + self.path)
		
		self.wfile.write("\n\nHEADERS:\n")
		self.wfile.write("========\n")
		
		for key in self.headers.keys():
			self.wfile.write(key + " --&gt; " + self.headers[key] + "\n")
		
		if (postdata is not None):
			self.wfile.write("\n\nEXTRA:\n")
			self.wfile.write("======\n")
			postparams = query2dict(postdata)
			for k,v in postparams.items():
				self.wfile.write("%s --&gt; %s\n" % (k,quote_entities(v)))
		
		self.wfile.write("</pre>\n")		
		self.wfile.write("</body>\n")
		self.wfile.write("</html>\n")
		pass
	
	def handle_get_fourohfour(self, args):
		self.handle_get_debug(args, None)
	
	def handle_get_index(self):
		self.handle_get_debug(None, None)
	
	
	def escape_quotes(s):
		return s.replace('"', '\\"')
	

class ExampleSrv(object):
	def __init__(self):
		pass
	
	def run(self):
		srv_port = 8080
		server_address = ('', srv_port)
		daemon = BaseHTTPServer.HTTPServer(server_address, SimpleHandler)
		print "ready to roll"
		daemon.serve_forever()

if __name__ == '__main__':
	v = ExampleSrv()
	v.run()