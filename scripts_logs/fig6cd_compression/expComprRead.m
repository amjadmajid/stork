function [dists,Smeans, Dmeans,Sstds,Dstds] = expComprRead(filename)
  lines = textread(filename,'%s','delimiter', '\n');
  % filter on result output
  %flines = {};
  fk = 1;
  logstr = 'Log wisent';
  for k = 1:length(lines)
    if (~isempty(strfind(lines{k},logstr)))
      flines{fk} = lines(k);
      fk =fk+1;
    end 
  end
  % get numbers of result log
  pk = 1;
  for k = 1:length(flines)
      flines{k}{1};
    parts = strsplit(flines{k}{1},{ '), time = ',', ',',\t','cm'});
    if(length(parts)>3)
        p = parts(3);
      stime(pk) = str2double(p{1});
      p = parts(4);
      dist(pk) = str2double(p{1});
      % now search for the time of decompression on the next line
      flines{k+1}{1};
      parts = strsplit(flines{k+1}{1},{ 'time ',', ','cm'});
      p = parts(2);
      dtime(pk) = str2double(p{1});
      pk=pk+1;
    end
  end

  % collect repetitions experiments
  % create a matrix with each row dedicated to one payload size. 
  % size matrix is: (nr_of_diff_dists , max(repetitions for each payload) )
  dists(1) = dist(1);   % this holds the different payloads (0 means throttle)
  Stimes(1,1) = 0;     % the time per experiment, rows are according to payload
  Dtimes(1,1) = 0;
  SDnr(1) = 0;          % number of experiments present in the previous matrix, per row/payload
  nr_of_diff_dists = 1; 
  for k = 1:length(dist)
    new = true;
    for l = 1:nr_of_diff_dists
      if( dist(k) == dists(l))
        new = false;
        SDnr(l) = SDnr(l)+1;
        Stimes(l,SDnr(l)) = stime(k);   
        Dtimes(l,SDnr(l)) = dtime(k);   
        break
      end
    end
    if(new)
      nr_of_diff_dists =nr_of_diff_dists+1;
      SDnr(nr_of_diff_dists) = 1;
      Stimes(nr_of_diff_dists,1) = stime(k);
      Dtimes(nr_of_diff_dists,1) = dtime(k);
      dists(nr_of_diff_dists) = dist(k);
    end
  end

  % get mean and std per payload
  for k = 1:nr_of_diff_dists
    Smeans(k) = mean( Stimes(k,1:SDnr(k)) );
    Sstds(k) = std(( Stimes(k,1:SDnr(k)) ));
    Dmeans(k) = mean( Dtimes(k,1:SDnr(k)) );
    Dstds(k) = std(( Dtimes(k,1:SDnr(k)) ));
  end

  % sort
  [dists, ind] = sort(dists);
  Stimes = Stimes(ind,:);
  Dtimes = Dtimes(ind,:);
  SDnr = SDnr(ind);
  Smeans = Smeans(ind);
  Sstds = Sstds(ind);
  Dmeans = Dmeans(ind);
  Dstds = Dstds(ind);
end
