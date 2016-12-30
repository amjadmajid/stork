clear all

figure('Position', [440 378 560/1.8 620/3.8])
%subplot(211)
hold on
box on

for k = 1:5
  [meansn(k),stdsn(k)] = multicastExpRead(['Multicastlog_sniff' num2str(k*10)  'cm_.txt']);
end
for k = 1:5
  [meanoo(k),stdoo(k)] = multicastExpRead(['Multicastlog_ObyO' num2str(k*10) 'cm_.txt']);
end
for k = 1:5
  [meanpl(k),stdpl(k)] = multicastExpRead(['Multicastlog_para' num2str(k*10) 'cm_.txt']);
end

d = 10:10:50;
diff = 0.4;
% d = 1:5;
% diff =0.2;
hold on
% bar([meanoo' meanpl' meansn'] ./[meanoo' meanoo' meanoo'],.9)
% errorbar(d-diff,meanoo./meanoo,stdoo./meanoo,'bo')
% errorbar(d,meanpl./meanoo,stdpl./meanoo,'r*')
% errorbar(d+diff,meansn./meanoo,stdsn./meanoo,'kx')
errorbar(d-diff,meanoo,stdoo,'bo')
errorbar(d,meanpl,stdpl,'r*')
errorbar(d+diff,meansn,stdsn,'kx')
%title('Different reprogramming methods')
legend({'Sqtl.', 'Optn.', 'Bdc.'}, 'Location','northwest')
xlabel('Distance tags to reader [cm]')
ylabel('Time all tags [s]')
xlim([0 55])
ylim([0 500])
% ylim([0 1.6])
set(gca,'XTick',d)
set(gca,'YTick',0:100:500)
set(gca,'XTickLabel',{'10','20','30','40','50'})
set(gca, 'FontSize', 12, 'LineWidth', 1.2)
set(findobj(gca, 'type', 'line'), 'linew', 1.2)
%set (gca,'yscale', 'log')

figure('Position', [440 378 560/1.8 620/3.8])
% subplot(212)
O4 = [27.104 27.074 25.441 24.390 30.765];
O3 = [18.662 17.745 21.817 18.883 20.522];
O2 = [14.390 14.765 13.694 12.581 14.830];
B4 = [14.024 15.438 16.893 17.026 14.309];
B3 = [11.311 11.889 13.916 13.632 13.245];
B2 = [ 8.114  6.709  7.838  7.208  6.672];
S4 = [37.017 30.678 39.364 32.902 28.518];
S3 = [29.631 31.111 30.824 29.996 30.814];
S2 = [19.310 15.634 16.072 19.266 14.692];
OBS =[ 6.197  7.173  7.816  6.629  6.002  ...
       5.974  6.223  5.703  6.926  5.712];
means = [mean(OBS) mean(OBS) mean(OBS);
         mean(S2)  mean(O2)  mean(B2);
         mean(S3)  mean(O3)  mean(B3);
         mean(S4)  mean(O4)  mean(B4)];
stds = [std(OBS) std(OBS) std(OBS);
        std(S2)  std(O2)  std(B2);
        std(S3)  std(O3)  std(B3);
        std(S4)  std(O4)  std(B4)];
    
b = bar(means,1);
hold on
for k = 1: 3
errorbar((1:4)-.5+.25*k,means(:,k),stds(:,k),'k.')
end
b(1).FaceColor = [0 0 1];
b(2).FaceColor = 'r';
b(2).LineStyle = ':';
b(2).LineWidth = 1.3;
b(3).FaceColor = 'w';
legend({'Sqtl.', 'Optn.','Bdc.'},'Orientation','Vertical', 'Location', 'EastOutside')
set(gca,'XTickLabel',{'1','2','3', '4'})
set(gca,'YTick',10:10:40)
ylabel('Time [s]') 
xlabel('Number of tags')


xlim([.5 4.5])
ylim([0 40])
set(gca, 'FontSize', 12, 'LineWidth', 1.2)
set(findobj(gca, 'type', 'line'), 'linew', 1.2)