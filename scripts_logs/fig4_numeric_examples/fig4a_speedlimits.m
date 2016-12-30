%% script for generating figure 4a, speed limits for each protocol

close all
%% time parameters from python model all in milli seconds
tBJW = 867.75475;    % time of a blockwrite command
tW = 797.24725;      % time of a write command
%thc = 1823.9315;     % time of a handshake including command initialization

tempty = 14.68975;   % time of a time of an empty slot
tcollision = 136.49975;% time of a time of a colission
tR = 1132.23225;     % time of a read command
tReqRN = 519.84975;  % time of request RN
% time of hc will be the x parameter
t_shift = 5000;
ths = 1:t_shift; % ths = 497; % absolute minimum time of a handshake,where tari is 6.25 us

%% non time parameters for equation L = {b_\text{da} N}{(Nt_\text{msg} + t_\text{hc} + t_\text{LLRP} + t_\text{RA} +  t_\text{meta} + t_\text{check})^{-1}}
nr_of_tags = 1;
%aloha = nr_of_tags/.368*(.5*(tempty+tcollision))+ (nr_of_tags-1)*ths;
tllrp = 0;
aloha = 0;

%% N defined for each protocol
N_S_MOM = 30*7; 
N_S_SPM = 30*4;
N_W = 16;
N_R = 1;

%% L defined for each protocol
Stork_MOM = 16*N_S_MOM./(tllrp+aloha+ths + 14*tBJW + tBJW*N_S_MOM + tR);
Stork_SPM = 16*N_S_SPM./(tllrp+aloha+ths + 8*tBJW + tBJW*N_S_SPM + 4*tR);
Wisent= 16*N_W./(tllrp+(aloha+ths + (2 + N_W)*tBJW)*2);
R2    = 16*N_R./(tllrp + aloha + ths + tReqRN + N_R*tW);

%% plot
figure('Position', [440 378 560/1.6 620/3])
box on
hold on
h = plot([.497 .497],[0 25],'--','Color',[.6 .6 .6],'LineWidth', .5);
set(get(get(h,'Annotation'),'LegendInformation'),'IconDisplayStyle','off');
plot(ths/1000,[Stork_MOM]*1000,'-b')
plot(ths/1000,[Stork_SPM]*1000,'-.b')
plot(ths/1000,[Wisent]*1000,'--k')
plot(ths/1000,[R2]*1000,'r:')

ylim([0 22])
xlim([0 t_shift/1000])
xlabel('t_{hs}+t_{LLRP} [ms]')
ylabel('Speed limit [kb/s]    ')
legend('Stork (MOM)','Stork (SPM)', 'Wisent', 'R^2')
set(gca, 'FontSize', 12, 'LineWidth', 1.5)
set(findobj(gca, 'type', 'line'), 'linew', 1.5)
set(h,'LineWidth', .5)
text(0.6,2.5,'minimum t','FontSize', 10)
text(1.75,2.5,'_{hs}','FontSize', 10)
annotation('textarrow',[1.25 1]/5+[.03 .03],[1.8 3]/20+[.27 .27],'String','','HeadWidth',5,'HeadLength',5)


