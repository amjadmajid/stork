function [mean1,std1] = multicastExpRead(filename)
  lines = textscan(fopen(filename),'%s','delimiter', '\n');
  lines = lines{1,1};
  % filter on result output
  fk = 1;
  logstr = 'FINISH';
  for k = 1:length(lines)
    if (~isempty(strfind(lines{k},logstr)))
      flines{fk} = lines(k);
      fk =fk +1;
    end 
  end
  % get numbers of result log
  pk = 1;
  for k = 1:length(flines)
    parts = strsplit(flines{k}{1},{']',' FINISH '});
    if(length(parts)>2)
        p = parts(2);
      TM(pk) = str2double(p{1});
      pk=pk+1;
    end
  end

  % get mean and std 
    mean1 = mean( TM(4:4:pk ));
    std1 = std( TM(4:4:pk));
end
