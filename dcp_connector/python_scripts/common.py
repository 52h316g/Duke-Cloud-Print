
import mimetools
import base64  # used for base64 encoding of files
import ConfigParser  # parses plain text config files
import httplib  # provides some high level HTTP services
import json  # provides high level JSON parsing functions
import logging  # provides general logging facilities
import mimetypes  # provides high level methods for evaluating mime data
import optparse  # parses incoming command line arguments
import os  # OS level functions and interaction
import string  # high level string functions
import sys  # high level system functions
import time  # time keeping functions
import urllib  # high level interface for www data using URLs
import urllib2  # adds functionality for complex URL interaction
from credentials import *

CRLF = '\r\n'
BOUNDARY = mimetools.choose_boundary()

# The following are used for general backend access.
CLOUDPRINT_URL = 'https://www.google.com/cloudprint'

script_dir = os.path.dirname(os.path.realpath(__file__))+'/'
FRONT_END_NAME = 'dcp_register'
os.environ['DJANGO_SETTINGS_MODULE'] = FRONT_END_NAME + '.settings'
sys.path.append(script_dir + '../../' + FRONT_END_NAME)
sys.path.append(script_dir + '../../' + FRONT_END_NAME + '/' + FRONT_END_NAME)

# The following object is used in the sample code, but is not necessary.
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
sh = logging.StreamHandler()
sh.setLevel(logging.DEBUG)
logger.addHandler(sh)
fh = logging.FileHandler(script_dir + "log.txt")
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)


def encodeMultiPart(fields, files, file_type='application/ppd'):
    """Encodes list of parameters and files for HTTP multipart format.

    Args:
      fields: list of tuples containing name and value of parameters.
      files: list of tuples containing param name, filename, and file contents.
      file_type: string if file type different than application/xml.
    Returns:
      A string to be sent as data for the HTTP post request.
    """
    lines = []
    for (key, value) in fields:
        lines.append('--' + BOUNDARY)
        lines.append('Content-Disposition: form-data; name="%s"' % key)
        lines.append('')  # blank line
        lines.append(value)
    for (key, filename, value) in files:
        lines.append('--' + BOUNDARY)
        lines.append(
            'Content-Disposition: form-data; name="%s"; filename="%s"'
            % (key, filename))
        lines.append('Content-Type: %s' % file_type)
        lines.append('')  # blank line
        lines.append(value)
    lines.append('--' + BOUNDARY + '--')
    lines.append('')  # blank line
    return CRLF.join(lines)


def getUrl(url, tokens, data=None, cookies=False, anonymous=False):
    """Get URL, with GET or POST depending data, adds Authorization header.
  Args:
    url: Url to access.
    tokens: dictionary of authentication tokens for specific user.
    data: If a POST request, data to be sent with the request.
    cookies: boolean, True = send authentication tokens in cookie headers.
    anonymous: boolean, True = do not send login credentials.
  Returns:
    String: response to the HTTP request.
  """
    request = urllib2.Request(url)
    # if not anonymous:
    #     if cookies:
    #         logger.debug('Adding authentication credentials to cookie header')
    #         request.add_header('Cookie', 'SID=%s; HSID=%s; SSID=%s' % (
    #             tokens['SID'], tokens['HSID'], tokens['SSID']))
    #     else:  # Don't add Auth headers when using Cookie header with auth tokens.
    #         request.add_header('Authorization', 'OAuth %s' % getAccessToken())
    request.add_header('X-CloudPrint-Proxy', 'api-prober')
    if data:
        request.add_data(data)
        request.add_header('Content-Length', str(len(data)))
        request.add_header('Content-Type', 'multipart/form-data;boundary=%s' % BOUNDARY)

    # In case the gateway is not responding, we'll retry.
    retry_count = 0
    while retry_count < 5:
        try:
            if not anonymous:
                if cookies:
                    logger.debug('Adding authentication credentials to cookie header')
                    request.add_header('Cookie', 'SID=%s; HSID=%s; SSID=%s' % (
                        tokens['SID'], tokens['HSID'], tokens['SSID']))
                else:  # Don't add Auth headers when using Cookie header with auth tokens.
                    request.add_header('Authorization', 'OAuth %s' % getAccessToken())
            result = urllib2.urlopen(request).read()
            return result
        except urllib2.HTTPError, e:
            # We see this error if the site goes down. We need to pause and retry.
            err_msg = 'Error accessing %s\n%s' % (url, e)
            logger.error(err_msg)
            logger.info('Pausing %d seconds', 30)
            time.sleep(30)
            retry_count += 1
            if retry_count == 5:
                return err_msg


def getCookie(cookie_key, cookie_string):
    """Extract the cookie value from a set-cookie string.

    Args:
      cookie_key: string, cookie identifier.
      cookie_string: string, from a set-cookie command.
    Returns:
      string, value of cookie.
    """
    logger.debug('Getting cookie from %s', cookie_string)
    id_string = cookie_key + '='
    cookie_crumbs = cookie_string.split(';')
    for c in cookie_crumbs:
        if id_string in c:
            cookie = c.split(id_string)
            return cookie[1]
    return None


def convertJson(json_str):
    """Convert json string to a python object.

  Args:
    json_str: string, json response.
  Returns:
    dictionary of deserialized json string.
  """
    j = {}
    try:
        j = json.loads(json_str)
        j['json'] = True
    except ValueError, e:
        # This means the format from json_str is probably bad.
        logger.error('Error parsing json string %s\n%s', json_str, e)
        j['json'] = False
        j['error'] = e

    return j


def getKeyValue(line, sep=':'):
    """Return value from a key value pair string.

    Args:
      line: string containing key value pair.
      sep: separator of key and value.
    Returns:
      string: value from key value string.
    """
    s = line.split(sep)
    return stripPunc(s[1])


def stripPunc(s):
    """Strip puncuation from string, except for - sign.

  Args:
    s: string.
  Returns:
    string with puncuation removed.
  """
    for c in string.punctuation:
        if c == '-':  # Could be negative number, so don't remove '-'.
            continue
        else:
            s = s.replace(c, '')
    return s.strip()


def validate(response):
    """Determine if JSON response indicated success."""
    if response.find('"success": true') > 0:
        return True
    else:
        return False


def getMessage(response):
    """Extract the API message from a Cloud Print API json response.

  Args:
    response: json response from API request.
  Returns:
    string: message content in json response.
  """
    lines = response.split('\n')
    for line in lines:
        if '"message":' in line:
            msg = line.split(':')
            return msg[1]

    return None


def readFile(pathname):
    """Read contents of a file and return content.

  Args:
    pathname: string, (path)name of file.
  Returns:
    string: contents of file.
  """
    try:
        f = open(pathname, 'rb')
        try:
            s = f.read()
        except IOError, e:
            logger('Error reading %s\n%s', pathname, e)
        finally:
            f.close()
            return s
    except IOError, e:
        logger.error('Error opening %s\n%s', pathname, e)
        return None


def writeFile(file_name, data):
    """Write contents of data to a file_name.

  Args:
    file_name: string, (path)name of file.
    data: string, contents to write to file.
  Returns:
    boolean: True = success, False = errors.
  """
    status = True

    try:
        f = open(file_name, 'wb')
        try:
            f.write(data)
        except IOError, e:
            logger.error('Error writing %s\n%s', file_name, e)
            status = False
        finally:
            f.close()
    except IOError, e:
        logger.error('Error opening %s\n%s', file_name, e)
        status = False

    return status


def base64Encode(pathname):
    """Convert a file to a base64 encoded file.

  Args:
    pathname: path name of file to base64 encode..
  Returns:
    string, name of base64 encoded file.
  For more info on data urls, see:
    http://en.wikipedia.org/wiki/Data_URI_scheme
  """
    b64_pathname = pathname + '.b64'
    file_type = mimetypes.guess_type(pathname)[0] or 'application/octet-stream'
    data = readFile(pathname)

    # Convert binary data to base64 encoded data.
    header = 'data:%s;base64,' % file_type
    b64data = header + base64.b64encode(data)

    if writeFile(b64_pathname, b64data):
        return b64_pathname
    else:
        return None


def getPrinters(proxy=None):
    """Get a list of all printers, including name, id, and proxy.

  Args:
    proxy: name of proxy to filter by.
  Returns:
    dictionary, keys = printer id, values = printer name, and proxy.
  """
    printers = {}
    values = {}
    tokens = ['"id"', '"name"', '"proxy"']
    for t in tokens:
        values[t] = ''

    if proxy:
        response = getUrl('%s/list?proxy=%s' % (CLOUDPRINT_URL, proxy), tokens)
    else:
        response = getUrl('%s/search' % CLOUDPRINT_URL, tokens)

    sections = response.split('{')
    for printer in sections:
        lines = printer.split(',')
        for line in lines:
            for t in tokens:
                if t in line:
                    values[t] = getKeyValue(line)
        if values['"id"']:
            printers[values['"id"']] = {}
            printers[values['"id"']]['name'] = values['"name"']
            printers[values['"id"']]['proxy'] = values['"proxy"']

    return printers


def registerAnonPrinter(printer):
    """Make a Printer Registration call as anonymous user.

    Args:
      printer: string, name of printer.
    Returns:
      dictionary: this will contain a boolean status and a json string.
    """
    result = {}
    data = encodeMultiPart([('proxy', 'ePrint-GCP-Proxy'), ('printer', printer)],
                           [('capabilities', 'capabilities.ppd', readFile("capabilities.ppd"))])
    response = getUrl('%s/register' % CLOUDPRINT_URL, [], data, anonymous=True)
    return response


def selfRegister():
    """A function to initiate and complete the entire self registration process.

  Returns:
    boolean: True = Success, False = errors.
  """
    pname = 'ePrint-GCP'
    responseUrl = registerAnonPrinter(pname)
    if validate(responseUrl):
        reg = convertJson(responseUrl)
        printer_id = reg['printers'][0]['id']
        if not reg['json']:
            logger.error(reg['error'])
            return False
        else:
            poll_url = '%s%s' % (reg['polling_url'], OAUTH)
            # This is manual step to go and claim your printer.
            print 'Go claim your printer at this url:'
            print 'https://www.google.com/cloudprint/claimprinter.html'
            print 'Use token: %s' % reg['registration_token']
            raw_input("Press Enter to continue once you've claimed your printer...")
            res = getUrl(poll_url, [], anonymous=True)
            if validate(res):
                poll = convertJson(res)
                if not poll['json']:
                    logger.error(poll['error'])
                    return False
                else:
                    logger.info('authorization_code: %s',
                                poll['authorization_code'])
                    logger.info('xmpp_jid: %s',
                                poll['xmpp_jid'])
                    # reg_id = Query(pname)
                    # if reg_id == printer_id:
                    # return True
                    # else:
                    # logger.error("Registered id doesn't match printer id.")
                    # return False
            else:  # poll_url wasn't successful.
                logger.error(getMessage(res))
                return False
    else:  # registerAnonPrinter() was not successful.
        logger.error(getMessage(responseUrl))
        return False


def getOAuth2Tokens(AuthCode):
    """Make a Printer Registration call as anonymous user.

    Args:
      printer: string, name of printer.
    Returns:
      dictionary: this will contain a boolean status and a json string.
    """
    params = {'code': AUTHORIZATION_CODE,
              'client_id': CLIENT_ID,
              'redirect_uri': "oob",
              'client_secret': ClIENT_SECRET,
              'grant_type': "AUTHORIZATION_CODE",
              'scope': "https://www.googleapis.com/auth/cloudprint"
    }
    # data = urllib.unquote_plus(urllib.urlencode(params))
    data = urllib.urlencode(params)
    f = urllib.urlopen(url='https://accounts.google.com/o/oauth2/token', data=data)
    response = f.read()
    if response.find("access_token"):
        tokens = convertJson(response)
        if not tokens['json']:
            logger.error(tokens['error'])
            return False
        else:
            logger.info('refresh_token : %s',
                        tokens['refresh_token'])
            logger.info('access_token : %s',
                        tokens['access_token'])
    else:  # registerAnonPrinter() was not successful.
        logger.error(getMessage(response))
        return False


def getAccessToken(forceNew=False):
    """Make a Printer Registration call as anonymous user.

    Args:
      printer: string, name of printer.
    Returns:
      dictionary: this will contain a boolean status and a json string.
    """

    tokens = convertJson(readFile(script_dir + 'access_token_time.txt'))
    if (forceNew == True) or (tokens['json'] == False) or (time.time() - tokens['time'] > 3000):
    #set expiration time from 3600s to 3000s
        params = {
            'client_id': CLIENT_ID,
            'client_secret': ClIENT_SECRET,
            'grant_type': "refresh_token",
            'refresh_token': REFRESH_TOKEN
        }
        # data = urllib.unquote_plus(urllib.urlencode(params))
        data = urllib.urlencode(params)
        f = urllib.urlopen(url='https://accounts.google.com/o/oauth2/token', data=data)
        response = f.read()
        if response.find("access_token"):
            tokens = convertJson(response)
            if not tokens['json']:
                logger.error(tokens['error'])
                return ""
            else:
                # logger.info('new access_token acquired: %s', tokens['access_token'])
                writeFile(script_dir + 'access_token_time.txt', json.dumps({'access_token': tokens['access_token'], 'time': time.time()},
                                                         sort_keys=True, indent=4, separators=(',', ': ')))
                writeFile(script_dir + 'access_token_only.txt', tokens['access_token'])
                return tokens['access_token']
        else:  # registerAnonPrinter() was not successful.
            logger.error(getMessage(response))
            return ""
    else:
        # print 'access_token:', tokens['access_token']
        return tokens['access_token']


def callAPI(api, params):
    data = urllib.urlencode(params)
    response_json = getUrl(('%s/' + api + '?%s') % (CLOUDPRINT_URL, data), [])
    return convertJson(response_json)
