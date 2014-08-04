__author__ = 'ljx19_000'
from third_party import json2pb, cloud_device_description_pb2
import mimetools
import base64  # used for base64 encoding of files
import json  # provides high level JSON parsing functions
import logging  # provides general logging facilities
import mimetypes  # provides high level methods for evaluating mime data
import os  # OS level functions and interaction
import string  # high level string functions
import sys  # high level system functions
import time  # time keeping functions
import urllib  # high level interface for www data using URLs
import urllib2  # adds functionality for complex URL interaction

CRLF = '\r\n'
BOUNDARY = mimetools.choose_boundary()

# The following are used for general backend access.
CLOUDPRINT_URL = 'https://www.google.com/cloudprint'
# CLIENT_NAME should be some string identifier for the client you are writing.
CLIENT_NAME = 'Cloud Print API Client'
# The following are used for authentication functions.
FOLLOWUP_HOST = 'www.google.com/cloudprint'
FOLLOWUP_URI = 'select%2Fgaiaauth'
# GAIA_HOST = 'www.google.com'
LOGIN_URI = '/accounts/ServiceLoginAuth'
LOGIN_URL = 'https://www.google.com/accounts/ClientLogin'
SERVICE = 'cloudprint'
OAUTH = '25406697542-8qt4tdhp6sullp546m22m9sc7c41jqfn.apps.googleusercontent.com'
client_id = OAUTH
client_secret = "imoKzZVaNCeZCfRouFEHOKN2"
email = "jixin.liao@gmail.com"
password = "8~eb8cp7ji~8"
authorization_code = "4/iERHdg3DXafVlvjvdo1FpGTEOHCU.ArIL5NhER4IZaDn_6y0ZQNheyblviAI"
# access_token = "ya29.1.AADtN_WWCeKX_5mrAJHxFR23Qu-MhV0rofKPhmWbRPR3PYZUNBBKx4bml_UDe6TBxw"
refresh_token = "1/-cgcp_m-l8w34ksejPzCiE4aExvPesMhqoIMPn3HR2U"
printerid = "4fce4085-4f8a-c233-2dec-5e7ce5044524"

script_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(script_dir)
script_dir = os.path.dirname(os.path.realpath(__file__))+'/'

# The following object is used in the sample code, but is not necessary.
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
sh = logging.StreamHandler()
sh.setLevel(logging.DEBUG)
logger.addHandler(sh)
fh = logging.FileHandler("log.txt")
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)
# All of the calls to getUrl assume you've run something like this:

# tokens = GetAuthTokens("jixin.liao@gmail.com", "8~eb8cp7ji~8")


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
    if not anonymous:
        if cookies:
            logger.debug('Adding authentication credentials to cookie header')
            request.add_header('Cookie', 'SID=%s; HSID=%s; SSID=%s' % (
                tokens['SID'], tokens['HSID'], tokens['SSID']))
        else:  # Don't add Auth headers when using Cookie header with auth tokens.
            request.add_header('Authorization', 'OAuth %s' % getAccessToken())
    request.add_header('X-CloudPrint-Proxy', 'api-prober')
    if data:
        request.add_data(data)
        request.add_header('Content-Length', str(len(data)))
        request.add_header('Content-Type', 'multipart/form-data;boundary=%s' % BOUNDARY)

    # In case the gateway is not responding, we'll retry.
    retry_count = 0
    while retry_count < 5:
        try:
            result = urllib2.urlopen(request).read()
            return result
        except urllib2.HTTPError, e:
            # We see this error if the site goes down. We need to pause and retry.
            err_msg = 'Error accessing %s\n%s' % (url, e)
            logger.error(err_msg)
            logger.info('Pausing %d seconds', 60)
            time.sleep(60)
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
    params = {'code': authorization_code,
              'client_id': client_id,
              'redirect_uri': "oob",
              'client_secret': client_secret,
              'grant_type': "authorization_code",
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
    if (forceNew == True) or (tokens['json'] == False) or (time.time() - tokens['time'] > 3600):
        params = {
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': "refresh_token",
            'refresh_token': refresh_token
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
                logger.info('new access_token acquired: %s', tokens['access_token'])
                writeFile(script_dir + 'access_token_time.txt', json.dumps({'access_token': tokens['access_token'], 'time': time.time()},
                                                         sort_keys=True, indent=4, separators=(',', ': ')))
                writeFile(script_dir + 'access_token_only.txt', tokens['access_token'])
                return tokens['access_token']
        else:  # registerAnonPrinter() was not successful.
            logger.error(getMessage(response))
            return ""
    else:
        print 'access_token:', tokens['access_token']
        return tokens['access_token']


def updatePrinter():
    cdd = cloud_device_description_pb2.CloudDeviceDescription()
    cdd.version = '1.0'
    printer = cdd.printer
    supported_content_type = printer.supported_content_type.add()
    supported_content_type.content_type = "application/pdf"
    optionMono = cdd.printer.color.option.add()
    optionMono.type = cloud_device_description_pb2.Color.STANDARD_MONOCHROME
    optionMono.is_default = True
    optionStandard = cdd.printer.color.option.add()
    optionStandard.type = cloud_device_description_pb2.Color.STANDARD_COLOR

    duplex = printer.duplex
    optionNoDuplex = duplex.option.add()
    optionNoDuplex.type = cloud_device_description_pb2.Duplex.NO_DUPLEX
    optionNoDuplex.is_default = True
    optionLongEdge = duplex.option.add()
    optionLongEdge.type = cloud_device_description_pb2.Duplex.LONG_EDGE
    optionShortEdge = duplex.option.add()
    optionShortEdge.type = cloud_device_description_pb2.Duplex.SHORT_EDGE

    orientation = printer.page_orientation
    optionAuto = orientation.option.add()
    optionAuto.type = cloud_device_description_pb2.PageOrientation.AUTO
    optionAuto.is_default = True
    optionPortrait = orientation.option.add()
    optionPortrait.type = cloud_device_description_pb2.PageOrientation.PORTRAIT
    optionLandscape = orientation.option.add()
    optionLandscape.type = cloud_device_description_pb2.PageOrientation.LANDSCAPE
    printer.copies.default = 1

    cap1 = printer.vendor_capability.add()
    cap1.id = '1'
    cap1.display_name = 'Delay the job for'
    cap1.type = cloud_device_description_pb2.VendorCapability.SELECT
    selectCap = cap1.select_cap
    selectCapOption1 = selectCap.option.add()
    selectCapOption1.value = '1'
    selectCapOption1.display_name = '0 hours'
    selectCapOption1.is_default = True
    selectCapOption2 = selectCap.option.add()
    selectCapOption2.value = '2'
    selectCapOption2.display_name = '12 hours'

    cap2 = printer.vendor_capability.add()
    cap2.id = '2'
    cap2.display_name = 'Alternative netID'
    cap2.type = cloud_device_description_pb2.VendorCapability.TYPED_VALUE
    typedValueCap = cap2.typed_value_cap
    typedValueCap.value_type = cloud_device_description_pb2.TypedValueCapability.STRING
    typedValueCap.default = ''

    json_msg = json2pb.json_encode(cdd)
    print json_msg
    params = {
        'printerid': printerid,
        'uuid': '20140719',
        'manufacturer': 'Jixin Liao',
        'use_cdd': 'true',
        'capabilities': json_msg
    }
    data = urllib.urlencode(params)
    response_json = getUrl('%s/update?%s' % (CLOUDPRINT_URL, data), [])
    response_dict = convertJson(response_json)
    print 'printer update success? '+str(response_dict['success'])+'\nprinter update message: '+response_dict['message']

# selfRegister()
# getOAuth2Tokens(authorization_code)
# getAccessToken()
# printers = getPrinters("ePrint-GCP-Proxy")
updatePrinter()