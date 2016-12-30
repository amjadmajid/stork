%% script to generate Figure 4b, memory exploration

clear all
D = 1:1:100; % data size divided by Cmin
nr_of_accessspecs = zeros(5,length(D));
S = [2 4 8 16 32]; % it for various S
for m = 1:5
    s = S(m); % pick one S
    up = ceil(log(D)./log(s)); % get upper limit for sum for k = 0 to ?

    for k = 1:length(up) % do sum of S^k
        for l = 1:up(k)
            nr_of_accessspecs(m,k)=nr_of_accessspecs(m,k) + ceil(s^(l-1)/min(4.0,32/s));
        end
    end
end

%% plot
figure('Position', [440 378 560/1.6 620/3])
hold on
box on
plot(D*8,nr_of_accessspecs(1,:),'--b') % multiply by Cmin = 8 words to get real data
plot(D*8,nr_of_accessspecs(2,:),'-.r') % multiply by Cmin = 8
plot(D*8,nr_of_accessspecs(3,:),'-k')  % multiply by Cmin = 8
plot(D*8,nr_of_accessspecs(4,:),'g:')  % multiply by Cmin = 8
%plot(DC*8,nr_of_accessspecs(5,:),'-m')
xlabel('Data size [words]')
ylim([0.5 25])
ylabel('# of AccessSpecs   ')
legend({'S=2','S=4','S=8', 'S=16'}, 'Location', 'southeast')
set(gca, 'FontSize', 12, 'LineWidth', 1.5)
set(findobj(gca, 'type', 'line'), 'linew', 1.5)
%set (gca,'yscale', 'log')
%set (gca,'xscale', 'log')