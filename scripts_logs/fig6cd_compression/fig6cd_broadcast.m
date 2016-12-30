clear all
[dists,Smeans, Dmeans,Sstds,Dstds] = expComprRead('wControl_logDecompression.txt');
set(0,'defaultlinelinewidth',1.5)
set(0,'defaulttextfontsize',15);

% plot
figure('Position', [440 378 560/1.8 620/3.8])

SaDmeans = Smeans+Dmeans;
SSmeans = 2527/2277 * Smeans;
SSstds = Sstds* sqrt(2527/2277);
SaDstds = sqrt(Sstds.^2 + Dstds.^2);
% subplot(211)
hold on
box on
errorbar(dists',SaDmeans',SaDstds','-rx','linew', 1.2)
errorbar(dists',SSmeans',SSstds','-bo','linew', 1.2)
xlabel('Distance tag to reader [cm]')
xlim([10 max(dists)+5])
set(gca,'XTick',20:10:60)
set(gca,'XTickLabel',{'20','30','40','50','60'})
set(gca,'YTick',100:100:400)
set(gca,'YTickLabel',{'100','200','300','400'})
% legend({'Compressed';'Uncompressed'}, 'Location', 'north')
legend({'Normal';'Compressed'}, 'Location', 'northwest')
ylabel('Time [s]')
set(gca, 'FontSize', 12, 'LineWidth', 1.2)
set(findobj(gca, 'type', 'line'), 'linew', 1.2)

figure('Position', [440 378 560/1.8 620/3.8])
% subplot(212)
hold on
box on
plot(dists,Smeans*(2527-2277)/2527,'-rx')
plot(dists,Dmeans,'-bo')

xlabel('Distance tag to reader [cm]')
xlim([10 65])
ylim([0 45])
set(gca,'XTick',20:10:60)
set(gca,'XTickLabel',{'20','30','40','50','60'})
set(gca,'YTick',0:10:40)
set(gca,'YTickLabel',{' 0',' 10',' 20',' 30',' 40'})
% legend({'Compressed';'Uncompressed'}, 'Location', 'north')
legend({'Compr. benefit';'Decompr. penalty'}, 'Location', 'northwest')
ylabel('Time [s]')
set(gca, 'FontSize', 12, 'LineWidth', 1.2)
set(findobj(gca, 'type', 'line'), 'linew', 1.2)
% set (gca,'yscale', 'log')
% subplot(122)
% title('speedup')
% plot(dists', (SSmeans-SaDmeans), '-b.')
% xlabel('Distance Reader Tag [cm]')
% ylabel('Decompression speedup [s]')
% dists
% xlim([10 max(dists)+5])
% grid on
