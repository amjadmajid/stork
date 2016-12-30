O= csvread('decompress.csv', 16, 0);
O = O(:,2:5);
plot((1:1250000)/250000,O)
legend('1','2','3','4')
V = O(:,1);
I = (O(:,2)-O(:,1))/1000;
P = V.*I;
figure
plot ((1:1250000)/250000,P)
xlabel('time [s]')
start = round(0.485*250000);
eind = round(2.048712*250000);
E = sum(P(start:eind)/250000);

disp('Energy used in this trace in mJ:')
disp(E*1000)