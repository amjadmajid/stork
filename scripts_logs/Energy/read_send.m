O = csvread('cleanReprogrammingEnergie.csv', 16, 0);
O = O(:,2:5);

V = O(:,4);
I = (O(:,2)-O(:,1))/1000;

P = V.*I;
figure
plot ((1:1250000)/250000,P)
xlabel('time [s]')
start = 1;
eind = round(4.113*250000);
E = sum(P(start:eind)/250000);

disp('Energy used in this trace in mJ:')
disp(E*1000)