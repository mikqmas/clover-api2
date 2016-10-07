#!/usr/bin/env python

# Copyright 2016 Google Inc.
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

# [START imports]
import os
import urllib
import logging
import pdb
import json
import urlparse

from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.ext.webapp import template
from client_secret import *
from google.appengine.api import urlfetch

import jinja2
import webapp2


access_token_str = None
global_code = None
client_id = None
merchant_id = None

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)
# [END imports]

DEFAULT_GUESTBOOK_NAME = 'default_guestbook'


# We set a parent key on the 'Greetings' to ensure that they are all
# in the same entity group. Queries across the single entity group
# will be consistent. However, the write rate should be limited to
# ~1/second.

def guestbook_key(guestbook_name=DEFAULT_GUESTBOOK_NAME):
    """Constructs a Datastore key for a Guestbook entity.

    We use guestbook_name as the key.
    """
    return ndb.Key('Guestbook', guestbook_name)


# [START greeting]
class Author(ndb.Model):
    """Sub model for representing an author."""
    identity = ndb.StringProperty(indexed=False)
    email = ndb.StringProperty(indexed=False)


class Greeting(ndb.Model):
    """A main model for representing an individual Guestbook entry."""
    author = ndb.StructuredProperty(Author)
    content = ndb.StringProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)
# [END greeting]


# [START main_page]
class MainPage(webapp2.RequestHandler):

    def get(self):
        code = self.request.get('code')
        if code:
            global client_id
            global merchant_id
            global access_token_str
            client_id = self.request.get('client_id')
            merchant_id = self.request.get('merchant_id')
            global_code = code

            url = "https://sandbox.dev.clover.com/oauth/token?client_id=" + client_id + "&client_secret=" + CLIENT_SECRET + "&code=" + code

            try:
                result = urlfetch.fetch(url)
                if result.status_code == 200:
                    access_token_str = str(json.loads(result.content)[u'access_token'])
                else:
                    self.response.status_code = result.status_code
            except:
                logging.exception('Caught exception fetching url')

            url = "https://sandbox.dev.clover.com/v3/merchants/{}".format( merchant_id )
            headers = {"Authorization": "Bearer " + access_token_str}
            result = urlfetch.fetch(
                url = url,
                headers = headers)

            rest_api_json = json.loads(result.content)

            url2 = 'https://sandbox.dev.clover.com/v3/merchants/{}/orders'.format( merchant_id )
            headers = {"Authorization": "Bearer " + access_token_str}
            result2 = urlfetch.fetch(
                url = url2,
                headers = headers)



            test1 = json.loads(result2.content)

            # pdb.set_trace()

            url3 = rest_api_json['owner']['href']
            result3 = urlfetch.fetch(
                url = url3,
                headers = headers
            )

            test2 = json.loads(result3.content)

            # pdb.set_trace()
        else:
            self.redirect("https://sandbox.dev.clover.com/oauth/merchants/SJ925JDCKKTJJ?client_id=4WRDFC82ZJ4S6")


        template_values = {
            'data': test2
        }

        data = {'data': test2}

        path = os.path.join(os.path.dirname(__file__), 'home.html')
        self.response.out.write(template.render(path, data))

        # self.response.out.write(json.dumps(test2))




        # template = JINJA_ENVIRONMENT.get_template('home.html')
        # self.response.write(template.render(template_values))

        # guestbook_name = self.request.get('guestbook_name',
        #                                   DEFAULT_GUESTBOOK_NAME)
        # greetings_query = Greeting.query(
        #     ancestor=guestbook_key(guestbook_name)).order(-Greeting.date)
        # greetings = greetings_query.fetch(10)
        #
        # user = users.get_current_user()
        # if user:
        #     url = users.create_logout_url(self.request.uri)
        #     url_linktext = 'Logout'
        # else:
        #     url = users.create_login_url(self.request.uri)
        #     url_linktext = 'Login'
        #
        # template_values = {
        #     'user': user,
        #     'greetings': greetings,
        #     'guestbook_name': urllib.quote_plus(guestbook_name),
        #     'url': url,
        #     'url_linktext': url_linktext,
        # }
        #
        # template = JINJA_ENVIRONMENT.get_template('index.html')
        # self.response.write(template.render(template_values))
# [END main_page]

class MainCustomer(webapp2.RequestHandler):
    def get(self):
        global access_token_str
        global merchant_id

        url = "https://sandbox.dev.clover.com/v3/merchants/{}/customers".format( merchant_id )
        headers = {"Authorization": "Bearer " + access_token_str}

        result = urlfetch.fetch(
            url = url,
            headers = headers
        )

        json_api = json.loads(result.content)

        template_values = {
            'data': json_api
        }

        path = os.path.join(os.path.dirname(__file__), 'customer/index.html')
        self.response.out.write(template.render(path, template_values))

class NewCustomerForm(webapp2.RequestHandler):
    def get(self):
        path = os.path.join(os.path.dirname(__file__), 'customer/new.html')
        self.response.out.write(template.render(path, {}))

class CreateCustomer(webapp2.RequestHandler):
    def post(self):
        path = os.path.join(os.path.dirname(__file__), 'customer/create.html')
        self.response.out.write(template.render(path, {}))


class NewInventoryForm(webapp2.RequestHandler):
    def get(self):
        path = os.path.join(os.path.dirname(__file__), 'new_inventory.html')
        self.response.out.write(template.render(path, {}))


class CreateInventoryItem(webapp2.RequestHandler):
    def post(self):
        global merchant_id
        global client_id
        global access_token_str
        global global_code
        form_data = urlparse.parse_qs(self.request.body)

        url = "https://sandbox.dev.clover.com/v3/merchants/" + merchant_id + "/items"
        headers = {"Authorization": "Bearer " + access_token_str, 'Content-Type': 'application/json'}

        post_data = json.dumps({
            "name": form_data["name"][0],
            "price": form_data["price"][0],
            "sku": form_data["sku"][0],
            "client_id": client_id,
            "client_secret": CLIENT_SECRET,
            "code": global_code
        })

        result = urlfetch.fetch(
            url = url,
            method = urlfetch.POST,
            payload = post_data,
            headers = headers)

        result = json.loads(result.content)

        template_values = {
            'name': result[u'name'],
            'price': result[u'price'],
            'sku': result[u'sku'],
            'id': result[u'id']
        }

        path = os.path.join(os.path.dirname(__file__), 'item_created.html')
        self.response.out.write(template.render(path, template_values))

# [START guestbook]
class Guestbook(webapp2.RequestHandler):

    def post(self):
        # We set the same parent key on the 'Greeting' to ensure each
        # Greeting is in the same entity group. Queries across the
        # single entity group will be consistent. However, the write
        # rate to a single entity group should be limited to
        # ~1/second.
        guestbook_name = self.request.get('guestbook_name',
                                          DEFAULT_GUESTBOOK_NAME)
        greeting = Greeting(parent=guestbook_key(guestbook_name))

        if users.get_current_user():
            greeting.author = Author(
                    identity=users.get_current_user().user_id(),
                    email=users.get_current_user().email())

        greeting.content = self.request.get('content')
        greeting.put()

        query_params = {'guestbook_name': guestbook_name}
        self.redirect('/?' + urllib.urlencode(query_params))
# [END guestbook]


# [START app]
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/customer', MainCustomer),
    ('/customer/new', NewCustomerForm),
    ('/customer/create', CreateCustomer),
    ('/inventory/new', NewInventoryForm),
    ('/inventory/create', CreateInventoryItem)
], debug=True)
# [END app]
