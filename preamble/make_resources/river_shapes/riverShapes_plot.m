% riverShapes_plot.m  3/14/2014  Parker MacCready
%
% exploratory plots of the river files

clear; close all;
addpath('../../../alpha')
Ldir = Lstart;

rsname = ['riverShapes_',Ldir.gridname,'.mat'];
load(rsname); % loads the structure "rivers" with fields
% lat lon name depth width dir rpos sign max_dist

for ii = 1:length(rivers)
    disp([num2str(ii),' = ',rivers(ii).name, ...
        ' dir = ',num2str(rivers(ii).dir), ...
        ' sign = ',num2str(rivers(ii).sign)]);
end

Z_fig(14);

for ii = 1:length(rivers)
    x = rivers(ii).lon;
    y = rivers(ii).lat;
    xx = rivers(ii).rpos(1);
    yy = rivers(ii).rpos(2);
    plot(x,y,'-r','linewidth',rivers(ii).width);
    if ii==1; hold on; end;
    plot(xx,yy,'pk','markerfacecolor','m','markersize',12)
    dir = rivers(ii).dir; sn = rivers(ii).sign;
    delta = 0.075;
    ha = 'left'; dx = delta;
    if sn == 1; ha = 'right'; dx = -delta; end;
    rname = strrep(rivers(ii).name,'_',' ');
    rname(1) = upper(rname(1));
    text(xx + dx,yy,rname,'color','r', ...
        'horizontalalignment',ha,'fontsize',12);
end
Z_dar;
Z_addcoast([Ldir.data,'coast/pnw_coast_combined.mat']);
axis([-124.75 -121.5 45 49.5]);
title('riverShapes')
xlabel('Longitude (deg)');
ylabel('Latitude (deg)');

set(gcf,'position',[100 100 500 800]);
set(gcf,'PaperPositionMode','auto');
print('-djpeg100',[Ldir.out,'plots/riverShapes.jpg']);
