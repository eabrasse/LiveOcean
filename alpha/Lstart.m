function [Ldir] = Lstart
% 1/21/2015  Parker MacCready
%
% A function to be invoked at the start of any primary MATLAB code anywhere
% in the LiveOcean folder.  It returns a structure Ldir that has handy
% pathnames, and it adds useful toolboxes to the path.
%
% Typical usage (depending on directory location in LiveOcean/):
%
% addpath('../alpha'); Ldir = Lstart;
%
% it relies on the existence of a text file RUN_INFO.csv
% in which each line has two strings: an item name and its value
% separated by a comma

%% Read environment variables
%
fid = fopen('RUN_INFO.csv','r');
C = textscan(fid,'%s%s','Delimiter',',');
fclose(fid);
items = C{1};
values = C{2};
Ldir = struct();
for ii = 1:length(items)
    Ldir.(items{ii}) = values{ii};
end
Ldir.gtag = [Ldir.gridname,'_',Ldir.tag];

% and get the parent
which_home = getenv('HOME');
switch which_home
    case '/Users/PM5'
        Ldir.parent = '/Users/PM5/Documents/';
    case '/home/parker'
        Ldir.parent = '/data1/parker/';
    otherwise
        disp('Trouble filling out environment variables in Ldir')
end

%% set locations of things
Ldir.home = [Ldir.parent,'LiveOcean/'];
Ldir.out = [Ldir.parent,'LiveOcean_output/'];
Ldir.data = [Ldir.parent,'LiveOcean_data/'];
%
Ldir.res = [Ldir.home,'preamble/make_resources/'];

% Paths to shared code assumed to be available by many programs
addpath([Ldir.home,'shared/mexcdf/mexnc']);
addpath([Ldir.home,'shared/mexcdf/snctools']);
addpath([Ldir.home,'shared/seawater']);
addpath([Ldir.home,'shared/Z_functions']);


