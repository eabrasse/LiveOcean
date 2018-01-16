"""
This code automatically populates a pandas dataframe with information about
the status of LiveOcean.  For each forecast day, what forcing files have been
created?  Has the day run successfully? Etc.
"""

# setup
import os
import sys
import argparse
import pandas as pd
from datetime import datetime

alp = os.path.abspath('../alpha')
if alp not in sys.path:
    sys.path.append(alp)
import Lfun

# get command line arguments, if any
parser = argparse.ArgumentParser()
# optional arguments
parser.add_argument("-g", "--gridname", type=str, default='cascadia1')
parser.add_argument("-t", "--tag", type=str, default='base')
parser.add_argument("-x", "--ex_name", type=str, default='lobio5')
parser.add_argument("-nd", "--num_days", type=int, default=10)
args = parser.parse_args()

Ldir = Lfun.Lstart(args.gridname, args.tag)
Ldir['gtagex'] = Ldir['gtag'] + '_' + args.ex_name

print(60*'*')
print(10*'=' + ' Info on ' + Ldir['gtagex'])
print(10*'=' + ' Most recent ' + str(args.num_days) + ' days')
print(60*'*')

# which forecast days exist in the forcing directory
f_dir0 = Ldir['LOo'] + Ldir['gtag'] + '/'
f_list = []
for item in os.listdir(f_dir0):
    if item[0] == 'f' and len(item) == 11:
        f_list.append(item)
f_list.sort()
# limit to the most recent ndays
f_list = f_list[-args.num_days:]

# list of properties to inspect
clist = ['tide', 'riv', 'atm', 'ocn1', 'dot_in', 'his', 'tracks_m', 'carbon', 'low_pass', 'ubc', 'surface', 'azu1']

# initialize the DataFrame
f_df = pd.DataFrame(index=f_list, columns=clist)

# for some things we will look for the existence of specific files as a test of completion
force_dict = {'atm': ['lwrad_down.nc', 'Pair.nc', 'Qair.nc', 'rain.nc',
                      'swrad.nc', 'Tair.nc', 'Uwind.nc', 'Vwind.nc'],
              'ocn1': ['ocean_bry.nc', 'ocean_clm.nc', 'ocean_ini.nc'],
              'riv': ['rivers.nc'],
              'tide': ['tides.nc']}
if 'bio' in args.ex_name:
    force_dict['ocn1'] = ['ocean_bry_bio.nc', 'ocean_clm_bio.nc', 'ocean_ini_bio.nc']
    force_dict['riv'] = ['rivers_bio.nc']
    
# populate the DataFrame with forcing results
for f_string in f_list:
    for which_force in force_dict.keys():
        force_dir = f_dir0 + f_string + '/' + which_force + '/'        
        if which_force in ['atm', 'ocn', 'ocn1']:
            #  in these cases looks for specific time info
            try:
                time_format = '%Y.%m.%d %H:%M:%S'
                ps = Lfun.csv_to_dict(force_dir + 'Info/process_status.csv')
                dt0 = datetime.strptime(ps['start_time'], time_format)
                dt1 = datetime.strptime(ps['end_time'], time_format)
                vdt0 = datetime.strptime(ps['var_start_time'], time_format)
                vdt1 = datetime.strptime(ps['var_end_time'], time_format)
                f_df.loc[f_string, which_force] = str((vdt1-vdt0).days) + 'd'
            except:
                pass
        else:
            # otherwise just look to see that the nc file(s) are there
            try:
                lll = os.listdir(force_dir)
                nc_list = force_dict[which_force]
                if set(nc_list).issubset(set(lll)):
                    f_df.loc[f_string, which_force] = 'YES'
            except:
                pass
                
# for other things look in the Info
for f_string in f_list:
    for which_force in ['tracks_m', 'carbon', 'low_pass', 'ubc', 'surface']:
        force_dir = f_dir0 + f_string + '/' + which_force + '/'
        try:
            ps = Lfun.csv_to_dict(force_dir + 'Info/process_status.csv')
            if ps['result'] == 'success':
                f_df.loc[f_string, which_force] = 'YES'
            else:
                f_df.loc[f_string, which_force] = 'no'
        except:
            pass

# Then look for forecasts have been run successfully
r_dir0 = Ldir['roms'] + 'output/' + Ldir['gtagex'] + '/'
try:
    for f_string in f_list:
        r_dir = r_dir0 + f_string
        if os.path.isdir(r_dir):
            fl = os.listdir(r_dir)
            if 'liveocean.in' in fl:
                f_df.loc[f_string, 'dot_in'] = 'YES'
            flh = [x for x in fl if 'ocean_his' in x]
            flh.sort()
            # get the number of the last history file
            f_df.loc[f_string, 'his'] = str(int(flh[-1][-7:-3]))
except:
    pass

# what has been pushed to Azure
azu_list = ['ocean_surface.nc', 'low_passed_UBC.nc', 'movie.mp4', 'plot_0070.png']
from azure.storage.blob import BlockBlobService
azu_dict = Lfun.csv_to_dict(Ldir['data'] + 'accounts/azure_pm_2015.05.25.csv')
account = azu_dict['account']
key = azu_dict['key']
blob_service = BlockBlobService(account_name=account, account_key=key)
for f_string in f_list:
    ff_string = f_string.replace('.','')
    containername = ff_string
    try:
        blobs = blob_service.list_blobs(containername)
        azu_count = 0
        for blob in blobs:
            if blob.name in azu_list:
                azu_count += 1
        f_df.loc[f_string, 'azu1'] = str(azu_count) + '/' + str(len(azu_list))
    except:
        pass
        
# mark missing things
f_df[f_df.isnull()] = '--'
# make sure that the dates are in order
f_df = f_df.sort_index()
# print to the screen
print(f_df)
