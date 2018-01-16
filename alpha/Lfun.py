"""
Functions for LiveOcean.
"""

# this bit of magic lets us know where this program lives
# and so allows us to find get_lo_info.sh and lo_info.csv
import os 
alp = os.path.dirname(os.path.realpath(__file__))

def Lstart(gridname='BLANK', tag='BLANK'):
    """
    This is to set environment variables in the LiveOcean system
    using values in the dict "Ldir".  It is similar to Lstart.m in the
    MATLAB code, but it returns a dictionary instead of a structure.

    We use input parameters to allow for different gridnames and tags to
    coexist.
    """
    print(alp)
    
    # put top level information from input into a dict
    Ldir = dict()
    Ldir['gridname'] = gridname
    Ldir['tag'] = tag

    # Build information on the directory structure.
    import os
    which_home = os.environ.get("HOME") # This works even when called by cron.
    if which_home == '/Users/PM5': # mac version
        Ldir['parent'] = '/Users/PM5/Documents/'
        Ldir['roms'] = Ldir['parent'] + 'LiveOcean_roms/'
        Ldir['which_matlab'] = '/Applications/MATLAB_R2015b.app/bin/matlab'
    elif which_home == '/home/parker': # fjord version
        Ldir['parent'] = '/data1/parker/'
        Ldir['roms'] = '/pmr1/parker/LiveOcean_roms/'
        Ldir['which_matlab'] = '/usr/local/bin/matlab'
    elif which_home == '/Users/elizabethbrasseale': #laptop
        Ldir['parent'] = '/Users/elizabethbrasseale/'
        Ldir['roms'] = Ldir['parent'] + 'LiveOcean_ROMS/'
        Ldir['which_matlab'] = '/Applications/MATLAB_R2016b.app/bin/matlab'
    elif which_home == '/home/eab32': #eab32@fjord
        Ldir['parent'] = '/pmr4/eab32/'
        Ldir['roms'] = Ldir['parent'] + 'LiveOcean_ROMS/'
        Ldir['which_matlab'] = '/usr/local/bin/matlab'
    
    import subprocess
    if os.path.isfile(alp + '/user_get_lo_info.sh'): 
        subprocess.call([alp + '/user_get_lo_info.sh'])
    else:
        subprocess.call([alp + '/get_lo_info.sh'])
    Ldir_temp = csv_to_dict(alp + '/lo_info.csv')
    Ldir.update(Ldir_temp)

    # and add a few more things
    Ldir['gtag'] = Ldir['gridname'] + '_' + Ldir['tag']
    Ldir['grid'] = Ldir['data'] + 'grids/' + Ldir['gridname'] + '/'
    Ldir['forecast_days'] = 3
    
    return Ldir

def make_dir(dirname, clean=False):
    # Make a directory if it does not exist.
    # Use clean=True to clobber the existing directory.
    import os
    if clean == True:
        import shutil
        shutil.rmtree(dirname, ignore_errors=True)
        os.mkdir(dirname)
    else:
        try:
            os.mkdir(dirname)
        except OSError:
            pass # assume OSError was raised because directory already exists

def dict_to_csv(dict_name, csv_name, write_mode='w'):
    # Write the contents of a dict to a two-column csv file.
    # The write_mode can be wb (overwrite, binary) or ab (append binary).
    # Binary mode is better across platforms.
    # 2015.11.25 changed to 'w' because it was throwing an error in python 3
    import csv
    with open(csv_name, write_mode) as ff:
        ww = csv.writer(ff)
        for kk in dict_name.keys():
            ww.writerow((kk, dict_name[kk]))

def csv_to_dict(csv_name):
    # Reads two-column csv file into a dict.
    import csv
    dict_name = dict()
    with open(csv_name) as ff:
        for row in csv.reader(ff):
            dict_name[row[0]] = row[1]
    return dict_name

def run_worker(Ldir, worker_type='matlab'):
    # run the worker code using subprocess
    if worker_type == 'matlab':
        # pass arguments to a matlab program
        import subprocess
        func = ("make_forcing_worker(\'" +
            Ldir['gridname'] + "\',\'" +
            Ldir['tag'] + "\',\'" +
            Ldir['date_string'] + "\',\'" +
            Ldir['run_type'] + "\',\'" +
            Ldir['LOogf_f'] + "\')")
        cmd = Ldir['which_matlab']
        run_cmd = [cmd, "-nojvm", "-nodisplay", "-r", func, "&"]        
        proc = subprocess.run(run_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print('\n-main: screen output from worker-')
        print(proc.stdout.decode())
    else:
        print('other worker types not implemented yet')


def datetime_to_modtime(dt):
    # This is where we define how time will be treated
    # in all the model forcing files.
    # NOTE: still need to define time zone (UTC?)

    # INPUT:
    # dt is a single datetime value

    # this returns seconds since 1/1/1970
    from datetime import datetime
    t = (dt - datetime(1970,1,1,0,0)).total_seconds()
    return t

def modtime_to_datetime(t):
    # input seconds since 1/1/1970 (single number)
    from datetime import datetime, timedelta
    dt = datetime(1970,1,1,0,0) + timedelta(seconds=t)
    return dt

def modtime_to_mdate_vec(mt_vec):
    from datetime import datetime, timedelta
    import matplotlib.dates as mdates

    # input numpy vector of seconds since 1/1/1970

    # first make a list of datetimes
    dt_list = []
    for mt in mt_vec:
        dt_list.append(datetime(1970,1,1,0,0) + timedelta(seconds=mt))

    md_vec = mdates.date2num(dt_list)

    return md_vec


