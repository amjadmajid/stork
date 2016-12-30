% stork vs wisent

s1 = [13.598 17.802 22.518 18.707 12.84 15.249 14.448 14.578 14.22 11.891 10.873 9.275 9.901 14.381];
w1 = [80.656 80.56 76.567 76.786 76.839 77.321 83.685 80.217 84.150 80.119 90.727];

s2 = [ 7.964   7.662  5.920   7.841  7.834  4.634   4.895   4.635  5.993  5.231];
w2 = [83.217 108.904 97.825 101.664 83.299 98.529 106.083 109.187 94.271 90.581];

s3 = [ 6.705  7.139   5.476  4.77   5.739  7.843  5.264   5.234  8.299];
w3 = [90.470 94.277 108.954 94.319 90.532 90.529 90.514 106.141 89.780];

means = [mean(s1) mean(w1);mean(s2) mean(w2);mean(s3) mean(w3)];
stds = [std(s1) std(w1);std(s2) std(w2);std(s3) std(w3)];
figure('Position', [440 378 560/3.2 620/3])
b = bar(means,1);
hold on
errorbar((1:3)-.15,means(:,1),stds(:,1),'k.')
errorbar((1:3)+.15,means(:,2),stds(:,2),'k.')
b(1).FaceColor = [0 0 1];
b(2).FaceColor = 'w';
legend({'S', 'W'},'Orientation','Horizontal', 'Location', 'NorthOutside')
set(gca,'XTickLabel',{'L','C','R'})
ylabel('Time [s]') 
xlabel('Position')


xlim([.5 3.5])
ylim([0 120])
set(gca, 'FontSize', 12, 'LineWidth', 1.5)
set(findobj(gca, 'type', 'line'), 'linew', 1.5)