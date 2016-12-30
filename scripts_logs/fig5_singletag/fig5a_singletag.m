%% script to generate the plot for the tag at fixed position given the log files
% experimental steps
% fix a tag programmed with stork bootloader X cm from antenna
% start Wisp control centre in python folder
% reprogram many times with different payloads  (use repeat option)
% save the logfile with the names as below

close all
clear all 
dist = [10,20,30,40,50,60]; 
[PLsizes{1},means{1},stds{1}, all1, all_size1] =expRead('StorkSingle10cm2.txt'); 
[PLsizes{2},means{2},stds{2}, all2, all_size2] =expRead('StorkSingle20cm.txt'); 
[PLsizes{3},means{3},stds{3}, all3, all_size3] =expRead('StorkSingle30cm.txt'); 
[PLsizes{4},means{4},stds{4}, all4, all_size4] =expRead('StorkSingle40cm.txt'); 
[PLsizes{5},means{5},stds{5}, all5, all_size5] =expRead('StorkSingle50cm.txt'); 

%% make 
goodexp = [1,2,3,4,5]; 
k =1:length(PLsizes{goodexp(3)}); 
for k = k
  PL = PLsizes{goodexp(3)}(k); 
  l = goodexp; 
  for l = goodexp
    ind = find(PLsizes{l} == PL); 
    if(sum(ind)>0)
      meantable(k,l) = (means{l}(ind)); 
      stdtable(k,l) = stds{l}(ind);
    else
      meantable(k,l) = 2000; stdtable(k,l) = 0; % time infinit
    end
  end
end

% plot old
close all
figure('Position', [440 378 560 620/3])
hold on
box on
c = {'b*-','r.:','rx-.','rs','ro','ro','r+','r+--','r^-'}; 
for k = [2:3 8 1] % plot a selection
  lim = sum(meantable(k,:)>0);
%   infi = 5-lim;
  errorbar(dist(1:lim)+(k-4)/4.0,meantable(k,1:lim),stdtable(k,1:lim),c{k},'linew', 1.5)
  
end
plot([10 20 30 40 50], [2000 100.63 100.942 201.919 2000], 'vk--')
%plot([10 20 30 40 50],[20 20 20 70 140],'<b')

ylim([3 2000])
xlabel('Distance tag to reader [cm]') 
ylabel('Time [s]') 
set(gca,'YTick',[4,10,40,100,400,2000])
legend({'Stork (1)';'Stork (5)';'Stork (30)';'Stork (T)'; 'Wisent'}, 'Location', 'NorthEastOutside')
set(gca,'YTickLabel',{'4','10','40','100','400','inf'})
set (gca,'yscale', 'log')
% breakInfo = breakyaxis([600 950]);
% set(breakInfo.highAxes,'YTicklabel','Infinity')


xlim([0 55])

set(gca, 'FontSize', 12, 'LineWidth', 1.5)
set(findobj(gca, 'type', 'line'), 'linew', 1.5)

%plot new
% close all
% c = {'k','r','b','g','m','y','r','r','y'}; 
% figure('Position', [440 378 560 620/3])
% hold on 
% m = 5;
% for k = 1:3
%     n = k;
%     x = [all1(n,1:all_size1(n)),all2(n,1:all_size2(n)),all3(n,1:all_size3(n)),all4(n,1:all_size4(n)),all5(n,1:all_size5(n))];
%     g = [ones(1,all_size1(n)),2*ones(1,all_size2(n)),3*ones(1,all_size3(n)),4*ones(1,all_size4(n)),5*ones(1,all_size5(n))];
%     boxplot(x,g,...
%      'Labels', {'10','20','30','40','50'}, 'Whisker', 3, ...
%      'factorseparator', 1, 'PlotStyle' , 'compact','LabelOrientation','horizontal', ...
%     'positions',0.9+1/10.0:1:4.9+1/10.0, 'colors', c{k})
% end
%title('Comparing dynamic and static checkpointing ');
% ylabel('Time [s]')
% xlabel('l [cm]')
% ylim([0 500])
% set(gca, 'FontSize', 12, 'LineWidth', 1.5)
% set(findobj(gca, 'type', 'line'), 'linew', 1.5)

% figure(34) 
% hold on 
% for k = [1:4 6 8]
%   lim = sum(meantable(k,:)>0);
%   errorbar(dist(1:lim)+(k-4)/4.0,meantable(k,1:lim)./meantable(3,1:lim),stdtable(k,1:lim)./meantable(3,1:lim),c{k})
% end
% xlim([0 55]) 
% ylim([0 2]) 
% xlabel('l [cm]') 
% ylabel('t (relative)')
% legend({'Throttle';'1';'5';'10';'20';'30'}, 'Location', 'northwest')


%% moving tag
clear all
[PLsizes{1},means{1},stds{1}, all1, all_size1] = expRead('logmoving20_80.txt');
[PLsizes{2},means{2},stds{2}, all2, all_size2] = expRead('logmoving20_80_M2.txt');
goodexp = [1,2];
k = 1:length(PLsizes{goodexp(1)});
for k = k
 PL = PLsizes{goodexp(1)}(k);
 l = goodexp;
 for l = goodexp
   ind = find(PLsizes{l} == PL);
   if(sum(ind)>0)
     meantable(k,l) = (means{l}(ind));
     stdtable(k,l) = stds{l}(ind);
   else 
     meantable(k,l) = 0;
     stdtable(k,l) = 0;
   end
 end
end
mov = [meantable([3 4 6 8],1)' meantable(8,2) meantable(1,1)];
smov = [stdtable([3 4 6 8],1)' stdtable(8,2) stdtable(1,1)];

% plot old
% % % figure('Position', [440 378 560 620/3])
% % % errorbar([5,10,20,30,40,50],mov,smov,'.')
% % % % legend('method 1', 'method 2')
% % % ax = gca;
% % % set(ax,'FontSize', 8)
% % % set(ax,'XTick',[5,10,20,30,40,50])
% % % set(ax,'XTickLabel',{'5*4  ','  10*4','20*4','30*4','30*7','throttle'})
% % % ylim([0 120])
% % % xlabel('Blockwrite payload [words]')
% % % ylabel('t [s]')
% % % % title('Tag moving between 20 and 80 cm')
% 
% plot new
% figure('Position', [440 378 560 620/3])
% m = 5;
% boxplot([all1(3,1:m)',all1(4,1:m)',all1(6,1:m)',all1(8,1:m)' ,all2(6,1:m)',all1(1,1:m)'],...
%  'Labels', {'5','10','20','30','30(*7)','throttle'}, 'Whisker', 3, ...
%     'factorseparator', 1,'LabelOrientation','horizontal' )
% %title('Comparing dynamic and static checkpointing ');
% ylabel('Time [s]')
% xlabel('Payload [words]')
% set(gca, 'FontSize', 12, 'LineWidth', 1.5)
% set(findobj(gca, 'type', 'line'), 'linew', 1.5)
