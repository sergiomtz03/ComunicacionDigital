filename = 'data.txt';
fid = fopen(filename, 'w');
for i = 1:100
    randomChars = char(randi([48, 90], 1, 50));
    fprintf(fid, '%s\n', randomChars);
end
fclose(fid);