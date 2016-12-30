function [PLsizes,means,stds,PLtimes,PLnr] = expRead(filename)
  lines = textscan(fopen(filename),'%s','delimiter', '\n');
  lines = lines{1,1};
  % filter on result output
  %flines = {};
  fk = 1;
  logstr = 'Log wisent';
  for k = 1:length(lines)
    if (~isempty(strfind(lines{k},logstr)))
      flines{fk} = lines{k};
      fk =fk+1;
    end 
  end
  % get numbers of result log
  pk = 1;
  for k = 1:length(flines)
    % IF OCTAVE USE THIS:
   % parts = strsplit(flines{k},{'= ( ',', ','), time = '});
    % IF MATLAB USE THIS:
    parts = strsplit(flines{k},{'= (\t',',\t','), time = '});
    if(length(parts)>3)
        p = parts(2);
      AS(pk) = str2double(p{1});
        p = parts(3);
        PL(pk) = str2double(p{1});
        if(isnan(PL(pk)))
            PL(pk) = 0;
        end

      p = parts(4);
      TM(pk) = str2double(p{1});
      pk=pk+1;
    end
  end
  % collect repetitions experiments
  % create a matrix with each row dedicated to one payload size. 
  % size matrix is: (nr_of_diff_payloads , max(repetitions for each payload) )
  PLsizes(1) = PL(1);   % this holds the different payloads (0 means throttle)
  PLtimes(1,1) = 0;     % the time per experiment, rows are according to payload
  PLnr(1) = 0;          % number of experiments present in the previous matrix, per row/payload
  nr_of_diff_payloads = 1; 
  for k = 1:length(PL)
    new = true;
    for l = 1:nr_of_diff_payloads
      if( PL(k) == PLsizes(l))
        new = false;
        PLnr(l) = PLnr(l)+1;
        PLtimes(l,PLnr(l)) = TM(k);      
        break
      end
    end
    if(new)
      nr_of_diff_payloads =nr_of_diff_payloads + 1;
      PLnr(nr_of_diff_payloads) = 1;
      PLtimes(nr_of_diff_payloads,1) = TM(k);
      PLsizes(nr_of_diff_payloads) = PL(k);
    end
  end

  % get mean and std per payload
  for k = 1:nr_of_diff_payloads
    means(k) = mean( PLtimes(k,1:PLnr(k)) );
    stds(k) = std(( PLtimes(k,1:PLnr( k)) ));
  end

  % sort
  [PLsizes, ind] = sort(PLsizes); % contains the payload sizes
  PLtimes = PLtimes(ind,:); % contains the raw samples sample at position(payloadsize, samplenr)
  PLnr = PLnr(ind); % contains the max valid samplenr per payloadsize
  means = means(ind); % contains the mean per payloadsize
  stds = stds(ind); % contains the std per payloadsize
end 
