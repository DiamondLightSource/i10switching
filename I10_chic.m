%% I10 chicane simulation code
function I10_chic

Kadd = [0, 0, 0, 0, 0];  % Add something to the kickers.
Ksca = [1, 1, 1, 1, 1];  % Alter the kicker waveforms by a scale factor.

% Write this data to our text files.
K = mat2str([Kadd, Ksca]); K = K(2:end-1);
fid = fopen('K.txt', 'w'); fwrite(fid, K); fclose(fid);

% Where is everything physically located in our simulations? [m]
Kpos = [-4, -3, 0, 3, 4];
IDpos = [-1.5, 1.5];
EBPMpos = [-5.5, 5.5];

% Kicker strengths and polarisations
Kstr0 = [1, 1.333, 0.333, 1.333, 1];
Kdir = [+1, -1, +1, -1, +1];

% Do the IDs have any effect on beam trajectory? (Trims correct for this)
IDstr = [0, 0].*1e-1;

% Kicker waveforms.
k12 = 0.5.*(sin(linspace(0, 2.*pi, 101))+1);
k45 = 0.5.*(sin(linspace(0, 2.*pi, 101)+pi)+1);
k12 = k12(2:end);
k45 = k45(2:end);

% Starting vector of Electron beam and FOFB correction (a).
eV0 = [0.5, 0]; % electron velocity vector [forwards, horizontal]
eP0 = [-10, 0]; % electron position vector [forwards, horizontal]
a = 0;          % FOFB correction. 

% Distance to Detector?
d2d = 30;

% Some intial vectors and numbers that will be populated as code runs.
nPhotonPoints = 500;
Pphoton = nan(2, 2);
Pphotoni = nan(nPhotonPoints, 2);
Pdetector = nan;
Pdetectori = nan(nPhotonPoints, 1);
ai = nan(nPhotonPoints, 1);
sT = 1;

% Run forever!
while true
    tic
    
    % Find our where we are in the '10Hz triggering' cycle.
    s = mod(sT,100)+1;
    
    % Read our K values.
    K = textread('K.txt');
    Kadd = K(1:5); Ksca = K(6:10);
    
    % Set our K values.
    Kstr = Kstr0.*[k12(s), k12(s), 1, k45(s), k45(s)].*Ksca + Kadd;
    
    % Reset photon beam parameters.
    IDV = [NaN, NaN; NaN, NaN]; % ID beam [1; 2] vector [vstart, horizontal]
    
    % If we're on the very first iteration, grab E-beam values.
    if sT==1
        eV = eV0;
        eP = eP0;
    end
    
    % Arbitrary timebase for electron trajectory, and set blank trajectory 
    % vector, ePv.
    t = 0:0.1:30;
    ePv = nan(2, length(t));
    
    % For each point in electron trajectory..
    for n=1:length(t)
        % ..set electron position..
        ePv(:, n) = eP;
        
        % ..and find out if we're at any 'special' locations.
        [mK, iK] = min(abs(Kpos - eP(1)));
        [mID, iID] = min(abs(IDpos - eP(1)));
        [mEBPM, iEBPM] = min(abs(EBPMpos(2) - eP(1)));
        
        % If we're at a Kicker magnets, apply kick.
        if mK < 0.01
            eV(1) = eV(1);
            eV(2) = eV(2) + (Kstr(iK).*Kdir(iK));
        end
        
        % If we're at an ID, apply photon beam, and kick if needed.
        if mID < 0.01
            IDV(iID, 1) = eP(2);
            IDV(iID, 2) = eV(2) + 0.5.*IDstr(iID);
            eV(2) = eV(2) + IDstr(iID);
        end
        
        % If we're at the EBPM, take a reading and prepare FOFB adjustment.
        if mEBPM < 0.01
            a = -eP(2).*0.0075 + a;
        end
        
        % Increment position of E-beam.
        eP = eP + eV;

    end
    
    % FOFB correction.
    eP = [eP0(1), -a.*(EBPMpos(1)-eP0(1))./eV(1)];
    eV = [eV0(1), a];
    
    % Use trigger to find photon beam positions at sample.
    Pphoton = repmat(IDV(:,1), [1, 2])+[0, 0; d2d./eV(1).*IDV(:, 2)']';
    if s==26
        Pdetector = Pphoton(2,2);
    elseif s==76
        Pdetector = Pphoton(1,2);
    else
        Pdetector = nan;
    end
    
    % Photon beam path
    Pphotoni = [Pphoton(:, 2)'; Pphotoni(1:end-1, :)];
    Pdetectori = [Pdetector; Pdetectori(1:end-1, :)];
    
    % FOFB corrections.
    ai = [a; ai(1:end-1)];
    
    % Plot graphs.
    if sT==1
        f1 = figure('Position', [50, 500, 600, 500]);
        set(gcf,'toolbar', 'none')
        f2 = figure('Position', [50, 240, 600, 200]);
        set(gcf,'toolbar', 'none')
        f3 = figure('Position', [665, 800, 300, 200]);
        set(gcf,'toolbar', 'none')
        uicontrol('Style', 'pushbutton', 'String', 'Scale +',...
            'Position', [30 50 50 20],'Callback', @Scaleplus);
        uicontrol('Style', 'pushbutton', 'String', 'Scale -',...
            'Position', [30 20 50 20],'Callback', @Scaleminus);
        uicontrol('Style', 'pushbutton', 'String', 'K3 +',...
            'Position', [90 50 50 20],'Callback', @K3plus);
        uicontrol('Style', 'pushbutton', 'String', 'K3 -',...
            'Position', [90 20 50 20],'Callback', @K3minus);
        uicontrol('Style', 'pushbutton', 'String', 'ID1 +',...
            'Position', [150 50 50 20],'Callback', @ID1plus);
        uicontrol('Style', 'pushbutton', 'String', 'ID1 -',...
            'Position', [150 20 50 20],'Callback', @ID1minus);
        uicontrol('Style', 'pushbutton', 'String', 'ID2 +',...
            'Position', [210 50 50 20],'Callback', @ID2plus);
        uicontrol('Style', 'pushbutton', 'String', 'ID2 -',...
            'Position', [210 20 50 20],'Callback', @ID2minus);
        uicontrol('Style', 'pushbutton', 'String', 'Reset !',...
            'Position', [30 80 50 20],'Callback', @reset);
        f4 = figure('Position', [665, 240, 300, 200]);
        set(gcf,'toolbar', 'none')
    end
    
    % Limit for our graphs.
    yL = 25;
    
    % Electron beam trajectory.
    set(0, 'CurrentFigure', f1)
    [xi, yi] = vline(Kpos, 40);
    plot(xi, yi, ':k', 100.*[-1, 1], [0, 0], '-k', ...
        eP(1), eP(2), 'bo', ePv(1, :), ePv(2, :), '-b', ...
        EBPMpos, [0, 0], 'kx', ...
        IDpos(1)+[0, d2d], Pphoton(1,:), 'o-r', ...
        IDpos(2)+[0, d2d], Pphoton(2,:), 'o-r', ...
        'LineWidth', 2)
    xlabel('Longitudinal position [m]')
    ylabel('Transverse position [microns]')
    ylim(yL.*[-1, 1])
    xlim([-6, 12])
    title('Electron beam trajectory through I10 straight')
    
    % Photon beam at sample point.
    set(0, 'CurrentFigure', f2)
    plot(Pphoton(:, 2)', [0, 0], 'r.', ...
        Pdetector, 0, 'ro', ...
        Pphotoni, repmat([1:nPhotonPoints]', [1, 2]), 'r:', ...
        Pdetectori, [1:nPhotonPoints]', 'ro', ...
        'LineWidth', 2)
    ylim([-0.1.*nPhotonPoints, nPhotonPoints])
    xlim(yL.*[-1, 1])
    set(gca, 'YTick', [])
    xlabel('Transverse position [microns]')
    title(sprintf('Beam position at sample point, %.0fm from ID straight', d2d))

    % FOFB workings.
    set(0, 'CurrentFigure', f4)
    plot(1000.*ai, [1:nPhotonPoints]', 'g')
    ylim([-0.1.*nPhotonPoints, nPhotonPoints])
    xlim(100.*[-1, 1])
    set(gca, 'YTick', [])
    xlabel('FOFB corrections [nrad]')
    
    % Draw our graphs!
    drawnow
    
    % Increment our time, sT, and pause if needed.
    sT = sT+1;
    pause(0.04-toc)
    
end

end

%% GUI Buttons
% Scale buttons:
function Scaleplus(~,~)
K = textread('K.txt');
Kadd = K(1:5); Ksca = K(6:10);

Ksca = Ksca + [1, 1, 0, 1, 1].*1e-1;

K = mat2str([Kadd, Ksca]); K = K(2:end-1);
fid = fopen('K.txt', 'w'); fwrite(fid, K); fclose(fid);
end

function Scaleminus(~,~)
K = textread('K.txt');
Kadd = K(1:5); Ksca = K(6:10);

Ksca = Ksca - [1, 1, 0, 1, 1].*1e-1;

K = mat2str([Kadd, Ksca]); K = K(2:end-1);
fid = fopen('K.txt', 'w'); fwrite(fid, K); fclose(fid);
end

% K3 buttons:
function K3plus(~,~)
K = textread('K.txt');
Kadd = K(1:5); Ksca = K(6:10);
 
Kadd = Kadd + [0, 0, 0.5, 0, 0].*1e-1;

K = mat2str([Kadd, Ksca]); K = K(2:end-1);
fid = fopen('K.txt', 'w'); fwrite(fid, K); fclose(fid);
end

function K3minus(~,~)
K = textread('K.txt');
Kadd = K(1:5); Ksca = K(6:10);

Kadd = Kadd - [0, 0, 0.5, 0, 0].*1e-1;

K = mat2str([Kadd, Ksca]); K = K(2:end-1);
fid = fopen('K.txt', 'w'); fwrite(fid, K); fclose(fid);
end

% ID 1 and 2 buttons:
function ID1plus(~,~)
K = textread('K.txt');
Kadd = K(1:5); Ksca = K(6:10);

Kadd = Kadd - [1.7, 2, 0.45, 0, 0].*1e-1;

K = mat2str([Kadd, Ksca]); K = K(2:end-1);
fid = fopen('K.txt', 'w'); fwrite(fid, K); fclose(fid);
end

function ID1minus(~,~)
K = textread('K.txt');
Kadd = K(1:5); Ksca = K(6:10);

Kadd = Kadd + [1.7, 2, 0.45, 0, 0].*1e-1;

K = mat2str([Kadd, Ksca]); K = K(2:end-1);
fid = fopen('K.txt', 'w'); fwrite(fid, K); fclose(fid);
end

function ID2plus(~,~)
K = textread('K.txt');
Kadd = K(1:5); Ksca = K(6:10);

Kadd = Kadd + [0, 0, 0.45, 2, 1.7].*1e-1;

K = mat2str([Kadd, Ksca]); K = K(2:end-1);
fid = fopen('K.txt', 'w'); fwrite(fid, K); fclose(fid);
end

function ID2minus
K = textread('K.txt');
Kadd = K(1:5); Ksca = K(6:10);

Kadd = Kadd - [0, 0, 0.45, 2, 1.7].*1e-1;

K = mat2str([Kadd, Ksca]); K = K(2:end-1);
fid = fopen('K.txt', 'w'); fwrite(fid, K); fclose(fid);
end

% Reset the demo!
function reset(~,~)
K = textread('K.txt');
Kadd = K(1:5); Ksca = K(6:10);

Kadd = [0, 0, 0, 0, 0];  % Add something to the kickers.
Ksca = [1, 1, 1, 1, 1];  % Alter the kicker waveforms by a scale factor.

K = mat2str([Kadd, Ksca]); K = K(2:end-1);
fid = fopen('K.txt', 'w'); fwrite(fid, K); fclose(fid);
end

% Vline function, required for plotting!
function [xi,yi] = vline(x, height)
xi = nan(length(x).*3, 1);
for n=1:length(xi)
    xi(n) = x(ceil(n./3));
end
yi = repmat([-height height nan],[1 length(x)]);
end
