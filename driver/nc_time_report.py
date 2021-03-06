"""
This looks at time properties of all the NetCDF forcing files generated by
forcing code.
"""

# get command line arguments
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("-g", "--gridname", type=str, default='cascadia1')
parser.add_argument("-t", "--tag", type=str, default='base')
parser.add_argument("-d", "--date_string", type=str, default='2015.04.15')
args = parser.parse_args()

# setup
from datetime import datetime
import os; import sys
alp = os.path.abspath('../alpha')
if alp not in sys.path:
    sys.path.append(alp)
import Lfun
Ldir = Lfun.Lstart(args.gridname, args.tag)

yr = args.date_string[:4]
mo = args.date_string[5:7]
dy = args.date_string[-2:]


f_dt = datetime(int(yr),int(mo),int(dy)) # NOTE: should make this an input argument

t00 = Lfun.datetime_to_modtime(f_dt)
date_string = f_dt.strftime('%Y.%m.%d')
f_string = 'f' + date_string

print('\n' + 30*'>' + ' ' + 30*'<')
print('>> reference time for ' + f_string + ', sec since 1/1/1970 <<')
print('>>>>>>>>> t00 = ' + str(t00) + ' <<<<<<<<<<<<<<<<<<<<<\n')
print('** first and last forcing variable times, relative to the start of the day **')

frc_list = ['atm', 'ocn', 'riv', 'tide']

for frc in frc_list:
    print('\n%s %10s %s' % (20*'*', frc.upper(), 20*'*'))
    odir = Ldir['LOo'] + Ldir['gtag'] +'/' + f_string +'/' + frc + '/'
    try:
        odl = os.listdir(odir)
        for nn in odl:
            if '.nc' in nn:
                print('\n%s %10s %s' % (20*'=', nn, 20*'='))
                import netCDF4 as nc    
                ds = nc.Dataset(odir + nn)
                for vv in ds.variables:
                    if 'time' in vv:
                        t = ds.variables[vv][:]
                        # get first and last time relative to t00
                        # (assumes t and t00 are in the same units)
                        td0 = t[0] - t00
                        td1 = t[-1] - t00
                        try:
                            uu = ds.variables[vv].units
                            if uu == 'seconds':
                                uuu = 'days'
                        except:
                            uuu = 'MISSING'
                        print(' %20s: %2d to %2d %s' % (vv, td0/86400., td1/86400., uuu))
                ds.close()
    except FileNotFoundError:
        pass