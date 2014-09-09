__author__ = 'Jixin Liao'

from third_party import json2pb, cloud_device_description_pb2
import os
import sys
script_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(script_dir)
from common import *


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

    copies = printer.copies
    copies.default = 1
    copies.max = 999

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

    page_range = printer.page_range
    defaultRange = page_range.default.add()
    defaultRange.start = 1

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
        'printerid': PRINTER_ID,
        'uuid': '20140719',
        'manufacturer': 'Jixin Liao',
        'use_cdd': 'true',
        'capabilities': json_msg
    }
    response = callAPI('update', params)
    print 'printer update success? ' + str(response['success']) + '\nprinter update message: ' + response[
        'message']


updatePrinter()