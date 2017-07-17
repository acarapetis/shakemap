import os.path
import io
import sys

# third party libraries
import numpy as np
from configobj import ConfigObj
from validate import Validator, ValidateError

def get_data_path():
    homedir = os.path.dirname(os.path.abspath(__file__)) #where is this script?
    datadir = os.path.join(homedir,'..','data')
    return datadir

def get_config_paths():
    config_file = os.path.join(os.path.expanduser('~'),'.shakemap','profiles.conf')
    config = ConfigObj(config_file)
    profile_name = config['profile']
    profile = config['profiles'][profile_name]
    install = profile['install_path']
    data = profile['data_path']
    return (install,data)

def get_custom_validator():
    fdict = {
        'file_type': file_type,
        'directory_type': directory_type,
        'annotatedfloat_type': annotatedfloat_type,
        'weight_list': weight_list,
        'extent_list': extent_list,
    }
    validator = Validator(fdict)
    return validator

def config_error(config, results):
    for (section_list, key, _) in flatten_errors(config, results):
        if key is not None:
            print('The "%s" key in the section "%s" failed validation' % 
                    (key, ', '.join(section_list)))
            sys.exit(1)
        else:
            print('The following section was missing:%s ' % 
                    ', '.join(section_list))

def annotatedfloat_type(value):
    try:
        out = float(value)
    except:
        try:
            if value.endswith('c'):
                out = float(value.replace('c', '')) / 3600.0
            elif value.endswith('m'):
                out = float(value.replace('m', '')) / 60.0
            elif value.endswith('d'):
                out = float(value.replace('d', ''))
            else:
                raise ValidateError(value)
        except:
            raise ValidateError(value)
    return out

def weight_list(value, min):

    if isinstance(value, str) and value == 'None':
        return []
    if not isinstance(value, list):
        if value.startswith('[') and value.endswith(']'):
            value = value.replace('[', '')
            value = value.replace(']', '')
        if not value:
            value = []
        else:
            value = [value]
    if len(value) < int(min):
        print("list must contain at least %d entr%s" %
              (minimum, "ies" if int(minimum) != 1 else "y"))
        raise ValidateError()
    try:
        out = [float(a) for a in value]
    except:
        print("%s is not a list of floats" % value)
        raise ValidateError()
    np_out = np.array(out)
    if np.any(np_out < 0):
        print("all list values must be >= 0: %s" % value)
        raise ValidateError()
    if len(out) > 0 and np.sum(np_out) != 1:
        print("weights must sum to 1.0: %s" % value)
        raise ValidateError()

    return out

def extent_list(value):

    if isinstance(value, str) and (value == 'None' or value == '[]'):
        return []
    if not isinstance(value, list):
        print("'%s' is not a list of 4 coordinates" % value)
        raise ValidateError()
    if len(value) != 4:
        print("extent list must contain 4 entries")
        raise ValidateError()
    try:
        out = [float(a) for a in value]
    except:
        print("%s is not a list of 4 floats" % value)
        raise ValidateError()
    if out[0] < -360.0 or out[0] > 360.0 or \
       out[2] < -360.0 or out[2] > 360.0 or \
       out[1] < -90.0 or out[1] > 90.0 or \
       out[3] < -90.0 or out[3] > 90.0:
        print("Invalid extent: ", value, 
              " : -360 <= longitude <= 360, -90 <= latitude <= 90")
        raise ValidateError()

    return out

def file_type(value):
    if not value or value == 'None':
        return ''
    if not os.path.isfile(value):
        print("file '%s' is not a valid file" % value)
        raise ValidateError(value)
    return value

def directory_type(value):
    if not os.path.isdir(value):
        raise ValidateError(value)
    return value
