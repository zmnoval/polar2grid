#!/usr/bin/env python
# encoding: utf-8
"""
Provide information about MODIS product files for a variety of uses.

:author:       Eva Schiffer (evas)
:contact:      evas@ssec.wisc.edu
:organization: Space Science and Engineering Center (SSEC)
:copyright:    Copyright (c) 2012 University of Wisconsin SSEC. All rights reserved.
:date:         Oct 2012
:license:      GNU GPLv3
:revision:     $Id$
"""
__docformat__ = "restructuredtext en"

from polar2grid.core.constants import *

import sys
import re
import logging
from datetime import datetime

LOG = logging.getLogger(__name__)

LATITUDE_GEO_VARIABLE_NAME   = 'Latitude'
LONGITUDE_GEO_VARIABLE_NAME  = 'Longitude'

VISIBLE_CH_1_VARIABLE_NAME   = 'EV_250_Aggr1km_RefSB'
VISIBLE_CH_1_VARIABLE_IDX    = 0
VISIBLE_CH_7_VARIABLE_NAME   = 'EV_500_Aggr1km_RefSB'
VISIBLE_CH_7_VARIABLE_IDX    = 4
VISIBLE_CH_26_VARIABLE_NAME  = 'EV_Band26'
VISIBLE_CH_26_VARIABLE_IDX   = None
INFRARED_CH_20_VARIABLE_NAME = 'EV_1KM_Emissive'
INFRARED_CH_20_VARIABLE_IDX  = 0
INFRARED_CH_27_VARIABLE_NAME = 'EV_1KM_Emissive'
INFRARED_CH_27_VARIABLE_IDX  = 6
INFRARED_CH_31_VARIABLE_NAME = 'EV_1KM_Emissive'
INFRARED_CH_31_VARIABLE_IDX  = 10

CLOUD_MASK_NAME              = 'MODIS_Cloud_Mask'
CLOUD_MASK_IDX               = None
SEA_SURFACE_TEMP_NAME        = 'Sea_Surface_Temperature'
SEA_SURFACE_TEMP_IDX         = None
LAND_SURFACE_TEMP_NAME       = "LST"
LAND_SURFACE_TEMP_IDX        = None

VISIBLE_SCALE_ATTR_NAME      = "reflectance_scales"
VISIBLE_OFFSET_ATTR_NAME     = "reflectance_offsets"
INFRARED_SCALE_ATTR_NAME     = "radiance_scales"
INFRARED_OFFSET_ATTR_NAME    = "radiance_offsets"

GENERIC_SCALE_ATTR_NAME      = "scale_factor"
GENERIC_OFFSET_ATTR_NAME     = "add_offset"

FILL_VALUE_ATTR_NAME         = "_FillValue"
MISSING_VALUE_ATTR_NAME      = "missing_value"

GEO_FILE_SUFFIX              = ".geo.hdf"

# this is true for the 1km data, FUTURE: when we get to other kinds, this will need to be more sophisicated
ROWS_PER_SCAN                = 10

# TODO, this is not right, just a stand in until I get the right answer
CLOUDS_VALUES_TO_CLEAR       = [1, 2]

# a regular expression that will match files containing the visible and infrared bands
VIS_INF_FILE_PATTERN           = r'[at]1\.\d\d\d\d\d\.\d\d\d\d\.1000m\.hdf'
# a regular expression that will match files containing the cloud mask
CLOUD_MASK_FILE_PATTERN        = r'[at]1\.\d\d\d\d\d\.\d\d\d\d\.mask_byte1\.hdf'
# a regular expression that will match files containing sea surface temperature
SEA_SURFACE_TEMP_FILE_PATTERN  = r'[at]1\.\d\d\d\d\d\.\d\d\d\d\.mod28\.hdf'
# a regular expression that will match files containing land surface temperature
LAND_SURFACE_TEMP_FILE_PATTERN = r'[at]1\.\d\d\d\d\d\.\d\d\d\d\.modlst\.hdf'

BANDS_REQUIRED_TO_CALCULATE_FOG_BAND = [(BKIND_IR,  BID_20), (BKIND_IR,  BID_31)]

GEO_FILE_GROUPING = {
                      "geo_nav": [VIS_INF_FILE_PATTERN, CLOUD_MASK_FILE_PATTERN, SEA_SURFACE_TEMP_FILE_PATTERN, LAND_SURFACE_TEMP_FILE_PATTERN]
                    }

# a mapping between regular expressions to match files and their band_kind and band_id contents
FILE_CONTENTS_GUIDE = {
                        VIS_INF_FILE_PATTERN:                       {
                                                                     BKIND_VIS:   [BID_01, BID_07, BID_26],
                                                                     BKIND_IR:    [BID_20, BID_27, BID_31]
                                                                    },
                        CLOUD_MASK_FILE_PATTERN:                    {
                                                                     BKIND_CMASK: [NOT_APPLICABLE]
                                                                    },
                        SEA_SURFACE_TEMP_FILE_PATTERN:              {
                                                                     BKIND_SST:   [NOT_APPLICABLE]
                                                                    },
                        LAND_SURFACE_TEMP_FILE_PATTERN:             {
                                                                     BKIND_LST:   [NOT_APPLICABLE],
                                                                     BKIND_SLST:  [NOT_APPLICABLE]
                                                                    }
                      }

# a mapping between bands and their fill value attribute names
FILL_VALUE_ATTR_NAMES = \
            {
              (BKIND_VIS, BID_01):           FILL_VALUE_ATTR_NAME,
              (BKIND_VIS, BID_07):           FILL_VALUE_ATTR_NAME,
              (BKIND_VIS, BID_26):           FILL_VALUE_ATTR_NAME,
              (BKIND_IR,  BID_20):           FILL_VALUE_ATTR_NAME,
              (BKIND_IR,  BID_27):           FILL_VALUE_ATTR_NAME,
              (BKIND_IR,  BID_31):           FILL_VALUE_ATTR_NAME,
              
              (BKIND_CMASK, NOT_APPLICABLE): FILL_VALUE_ATTR_NAME,
              (BKIND_SST,   NOT_APPLICABLE): FILL_VALUE_ATTR_NAME,
              (BKIND_LST,   NOT_APPLICABLE): MISSING_VALUE_ATTR_NAME,
              (BKIND_SLST,   NOT_APPLICABLE): MISSING_VALUE_ATTR_NAME,
            }

# a mapping between the bands and their data kinds (in the file)
DATA_KINDS = {
              (BKIND_VIS, BID_01): DKIND_REFLECTANCE,
              (BKIND_VIS, BID_07): DKIND_REFLECTANCE,
              (BKIND_VIS, BID_26): DKIND_REFLECTANCE,
              (BKIND_IR,  BID_20): DKIND_RADIANCE,
              (BKIND_IR,  BID_27): DKIND_RADIANCE,
              (BKIND_IR,  BID_31): DKIND_RADIANCE,
              
              (BKIND_CMASK, NOT_APPLICABLE): DKIND_CATEGORY,
              (BKIND_SST,   NOT_APPLICABLE): DKIND_BTEMP,
              (BKIND_LST,   NOT_APPLICABLE): DKIND_BTEMP,
              (BKIND_SLST,  NOT_APPLICABLE): DKIND_BTEMP
             }

# a mapping between the bands and the variable names used in the files to hold them
VAR_NAMES  = {
              (BKIND_VIS, BID_01): VISIBLE_CH_1_VARIABLE_NAME,
              (BKIND_VIS, BID_07): VISIBLE_CH_7_VARIABLE_NAME,
              (BKIND_VIS, BID_26): VISIBLE_CH_26_VARIABLE_NAME,
              (BKIND_IR,  BID_20): INFRARED_CH_20_VARIABLE_NAME,
              (BKIND_IR,  BID_27): INFRARED_CH_27_VARIABLE_NAME,
              (BKIND_IR,  BID_31): INFRARED_CH_31_VARIABLE_NAME,
              
              (BKIND_CMASK, NOT_APPLICABLE): CLOUD_MASK_NAME,
              (BKIND_SST,   NOT_APPLICABLE): SEA_SURFACE_TEMP_NAME,
              (BKIND_LST,   NOT_APPLICABLE): LAND_SURFACE_TEMP_NAME,
              (BKIND_SLST,  NOT_APPLICABLE): LAND_SURFACE_TEMP_NAME,
             }

# a mapping between the bands and any index needed to access the data in the variable (for slicing)
# if no slicing is needed the index will be None
VAR_IDX    = {
              (BKIND_VIS, BID_01): VISIBLE_CH_1_VARIABLE_IDX,
              (BKIND_VIS, BID_07): VISIBLE_CH_7_VARIABLE_IDX,
              (BKIND_VIS, BID_26): VISIBLE_CH_26_VARIABLE_IDX,
              (BKIND_IR,  BID_20): INFRARED_CH_20_VARIABLE_IDX,
              (BKIND_IR,  BID_27): INFRARED_CH_27_VARIABLE_IDX,
              (BKIND_IR,  BID_31): INFRARED_CH_31_VARIABLE_IDX,
              
              (BKIND_CMASK, NOT_APPLICABLE): CLOUD_MASK_IDX,
              (BKIND_SST,   NOT_APPLICABLE): SEA_SURFACE_TEMP_IDX,
              (BKIND_LST,   NOT_APPLICABLE): LAND_SURFACE_TEMP_IDX,
              (BKIND_SLST,  NOT_APPLICABLE): LAND_SURFACE_TEMP_IDX,
        }

# a mapping between bands and the names of their scale and offset attributes
RESCALING_ATTRS = \
             {
              (BKIND_VIS, BID_01): (VISIBLE_SCALE_ATTR_NAME,  VISIBLE_OFFSET_ATTR_NAME),
              (BKIND_VIS, BID_07): (VISIBLE_SCALE_ATTR_NAME,  VISIBLE_OFFSET_ATTR_NAME),
              (BKIND_VIS, BID_26): (VISIBLE_SCALE_ATTR_NAME,  VISIBLE_OFFSET_ATTR_NAME),
              (BKIND_IR,  BID_20): (INFRARED_SCALE_ATTR_NAME, INFRARED_OFFSET_ATTR_NAME),
              (BKIND_IR,  BID_27): (INFRARED_SCALE_ATTR_NAME, INFRARED_OFFSET_ATTR_NAME),
              (BKIND_IR,  BID_31): (INFRARED_SCALE_ATTR_NAME, INFRARED_OFFSET_ATTR_NAME),
              
              (BKIND_CMASK, NOT_APPLICABLE): (GENERIC_SCALE_ATTR_NAME, GENERIC_OFFSET_ATTR_NAME),
              (BKIND_SST,   NOT_APPLICABLE): (GENERIC_SCALE_ATTR_NAME, GENERIC_OFFSET_ATTR_NAME),
              (BKIND_LST,   NOT_APPLICABLE): (GENERIC_SCALE_ATTR_NAME, None),
              (BKIND_SLST,   NOT_APPLICABLE): (GENERIC_SCALE_ATTR_NAME, None),
             }

# whether or not each band should be cloud cleared
IS_CLOUD_CLEARED = \
             {
              (BKIND_VIS, BID_01): False,
              (BKIND_VIS, BID_07): False,
              (BKIND_VIS, BID_26): False,
              (BKIND_IR,  BID_20): False,
              (BKIND_IR,  BID_27): False,
              (BKIND_IR,  BID_31): False,
              
              (BKIND_CMASK, NOT_APPLICABLE): False,
              (BKIND_SST,   NOT_APPLICABLE): True,
              (BKIND_LST,   NOT_APPLICABLE): True,
              (BKIND_SLST,  NOT_APPLICABLE): True,
             }

# whether or not each band should be converted to brightness temperature
SHOULD_CONVERT_TO_BT = \
             {
              (BKIND_VIS, BID_01): False,
              (BKIND_VIS, BID_07): False,
              (BKIND_VIS, BID_26): False,
              (BKIND_IR,  BID_20): True,
              (BKIND_IR,  BID_27): True,
              (BKIND_IR,  BID_31): True,
              
              (BKIND_CMASK, NOT_APPLICABLE): False,
              (BKIND_SST,   NOT_APPLICABLE): False,
              (BKIND_LST,   NOT_APPLICABLE): False,
              (BKIND_SLST,  NOT_APPLICABLE): False
             }

def parse_datetime_from_filename (file_name_string) :
    """parse the given file_name_string and create an appropriate datetime object
    that represents the datetime indicated by the file name; if the file name does
    not represent a pattern that is understood as a MODIS file, None will be returned
    """
    
    datetime_to_return = None
    
    # TODO, there are at least two file name formats to parse here
    
    if (file_name_string.startswith('a1') or file_name_string.startswith('t1')) :
        temp = file_name_string.split('.')
        datetime_to_return = datetime.strptime(temp[1] + temp[2], "%y%j%H%M")
        # TODO, the viirs guidebook is using .replace(tzinfo=UTC, microsecond=***) do I need to do this?
    
    return datetime_to_return

def get_satellite_from_filename (data_file_name_string) :
    """given a file name, figure out which satellite it's from
    if the file does not represent a known MODIS satellite name
    configuration None will be returned
    """
    
    satellite_to_return = None
    
    if   data_file_name_string.find("Aqua")  >= 0 or data_file_name_string.find("a1") == 0 :
        satellite_to_return = SAT_AQUA
    elif data_file_name_string.find("Terra") >= 0 or data_file_name_string.find("t1") == 0 :
        satellite_to_return = SAT_TERRA
    
    return satellite_to_return

def get_equivalent_geolocation_filename (data_file_name_string) :
    """given the name of a MODIS file, figure out the expected
    name for it's equivalent geolocation file; no checks into
    the existence or formatting of the geolocation file are made,
    this is just the name of the theoretical file where we would
    expect to find the geolocation for the given data file; if
    the given file name is not a pattern we understand as a MODIS
    file, None will be returned
    """
    
    filename_to_return = None
    
    # TODO there are going to be other sources of geolocation besides the .geo.hdf file when we get to later products
    
    if re.match(VIS_INF_FILE_PATTERN,           data_file_name_string) is not None :
        filename_to_return = data_file_name_string.split('.1000m.hdf'     )[0] + GEO_FILE_SUFFIX
    if re.match(CLOUD_MASK_FILE_PATTERN,        data_file_name_string) is not None :
        filename_to_return = data_file_name_string.split('.mask_byte1.hdf')[0] + GEO_FILE_SUFFIX
    if re.match(SEA_SURFACE_TEMP_FILE_PATTERN,  data_file_name_string) is not None :
        filename_to_return = data_file_name_string.split('.mod28.hdf'     )[0] + GEO_FILE_SUFFIX
    if re.match(LAND_SURFACE_TEMP_FILE_PATTERN, data_file_name_string) is not None :
        filename_to_return = data_file_name_string.split('.modlst.hdf'    )[0] + GEO_FILE_SUFFIX
    
    return filename_to_return

def main():
    import optparse
    from pprint import pprint
    usage = """
%prog [options] filename1.hdf

"""
    parser = optparse.OptionParser(usage)
    parser.add_option('-v', '--verbose', dest='verbosity', action="count", default=0,
            help='each occurrence increases verbosity 1 level through ERROR-WARNING-INFO-DEBUG')
    parser.add_option('-r', '--no-read', dest='read_hdf', action='store_false', default=True,
            help="don't read or look for the hdf file, only analyze the filename")
    (options, args) = parser.parse_args()
    
    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    logging.basicConfig(level = levels[min(3, options.verbosity)])
    
    LOG.info("Currently no command line tests are set up for this module.")
    
    """
    if not args:
        parser.error( 'must specify 1 filename, try -h or --help.' )
        return -1
    
    for fn in args:
        try:
            finfo = generic_info(fn)
        except:
            LOG.error("Failed to get info from filename '%s'" % fn, exc_info=1)
            continue
    
        if options.read_h5:
            generic_read(fn, finfo)
            pprint(finfo)
            if finfo["data_kind"] == K_RADIANCE:
                data_shape = str(finfo["data"].shape)
                print "Got Radiance with shape %s" % data_shape
            elif finfo["data_kind"] == K_REFLECTANCE:
                data_shape = str(finfo["data"].shape)
                print "Got Reflectance with shape %s" % data_shape
            elif finfo["data_kind"] == K_BTEMP:
                data_shape = str(finfo["data"].shape)
                print "Got Brightness Temperature with shape %s" % data_shape
            else:
                data_shape = "Unknown data type"
                print "Got %s" % data_shape
            mask_shape = str(finfo["mask"].shape)
            print "Mask was created with shape %s" % mask_shape
        else:
            pprint(finfo)
    
    """

if __name__ == '__main__':
    sys.exit(main())
