
%rts_no_block = [0.6616057589136319 0.5070379325028123 0.39518621050078284 0.16030459260118418];
rts_no_block = [0.802152784334289	0.643448130951988	0.502755534317758	0.203638892206881];
st_no_block = [rts_no_block(1:3)-rts_no_block(2:4) rts_no_block(4)];

MU=zeros(1,10);
MU([7,8,9,10])=[1/st_no_block(4)    1/st_no_block(3)    1/st_no_block(2)    1/st_no_block(1)];
X0=zeros(1,10);
NT=[inf,inf,inf,inf];

%7.1429    4.5455    2.0000    2.7778 ODE rate
%6.6729    4.4043    1.9732    2.7563 Real rate

np=7;

RTp=zeros(np,4);
Tp=zeros(np,4);
%NC=zeros(np,2);
%Cli=zeros(np,1);

for i=1:np

%Cli(i)=i*5;
NC(i,:)=[inf,24];
[t,y,Ts]=lqnOde([0,0,0,0,0,0,0,0,0,Cli(i)],MU,NT,NC(i,:));

Tp(i,:)=Ts';
RTp(i,:)=[sum(y(end,[1,10]))/Ts(1),...
    sum(y(end,[2,3,9]))/Ts(2),...
    sum(y(end,[4,5,8]))/Ts(3),...
    sum(y(end,[6,7]))/Ts(4)];
end