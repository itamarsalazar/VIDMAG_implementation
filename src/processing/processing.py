import os
import cv2
import scipy.signal as signal
import numpy as np
from skimage import color
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
import gui.constants as c


def vidmag_fn(input_fullname, parameters):

    alpha = parameters['alpha']
    lambda_c = parameters['lambda_c']
    fl = parameters['fl']
    fh = parameters['fh']
    samplingRate = parameters['samplingRate']
    chromAttenuation = parameters['chromAttenuation']
    nlevels = parameters['nlevels']

    # Butterworth coefficients
    [low_a, low_b] = signal.butter(1, fl/samplingRate, 'low')
    [high_a, high_b] = signal.butter(1, fh/samplingRate, 'low')

    # output fullname format
    input_filename = os.path.splitext(os.path.basename(input_fullname))[0]
    output_fullname = c.PROCESSED_VIDEO_DIR+input_filename+'-butter-from-'+str(fl)+'-to-'+str(fh)+'Hz'+\
              '-alpha-'+str(alpha)+'-lambda_c-'+str(lambda_c)+\
              '-chromAtn-'+str(chromAttenuation)+'.mp4'

    input_video = cv2.VideoCapture(input_fullname)
    vidHeight = int(input_video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    vidWidth = int(input_video.get(cv2.CAP_PROP_FRAME_WIDTH))
    fr = int(input_video.get(cv2.CAP_PROP_FPS))
    length = int(input_video.get(cv2.CAP_PROP_FRAME_COUNT))

    fourcc = cv2.VideoWriter_fourcc(*'MP4V')
    output_video = cv2.VideoWriter(output_fullname, fourcc, fr, (vidWidth, vidHeight), 1)

    # First frame
    temp_cdata = input_video.read()
    rgbframe = temp_cdata[1].astype('float')/255.0

    # get desired sizes used in all the Laplacian pyramid levels
    dsizes = np.zeros((nlevels+1, 2))
    for k in range(0, nlevels+1):
        dsizes[k, :] = [np.floor(rgbframe.shape[0]/(2**k)), np.floor(rgbframe.shape[1]/(2**k))]
    desired_sizes = tuple(map(tuple, dsizes))
    print(desired_sizes)

    # first frame processing (initial conditions)
    frame = color.rgb2yiq(rgbframe)
    lpyr = buildlpyr(frame, nlevels, desired_sizes)     # creates Laplacian pyramid
    lowpass1 = lpyr
    lowpass2 = lpyr
    pyr_prev = lpyr

    output_frame = color.yiq2rgb(frame)   # yiq color space
    output_frame = output_frame * 255
    output_video.write(output_frame.astype('uint8'))

    # processing remaining frames
    counter = 1
    while input_video.isOpened():
        print("Processing: %.1f%%" % (100*counter/length))

        temp_cdata = input_video.read()
        if not(temp_cdata[0]):
            break

        #from rgb to yiq
        rgbframe = temp_cdata[1].astype('float') / 255
        frame = color.rgb2yiq(rgbframe)

        # Laplacian pyramid (expansion)
        lpyr = buildlpyr(frame, nlevels, desired_sizes)

        # Temporal filter
        lowpass1 = (-high_b[1] * lowpass1 + high_a[0] * lpyr + high_a[1] * pyr_prev) / high_b[0]
        lowpass2 = (-low_b[1] * lowpass2 + low_a[0] * lpyr + low_a[1] * pyr_prev) / low_b[0]
        filtered = lowpass1 - lowpass2
        pyr_prev = lpyr

        # Amplification
        delta = lambda_c/8/(1+alpha)
        exaggeration_factor = 2
        lambda_ = (vidHeight**2 + vidWidth**2)**0.5/3
        filtered[0] = np.zeros_like(filtered[0])
        filtered[-1] = np.zeros_like(filtered[-1])

        for i in range(nlevels-1, 1, -1):
            # equation 14 (paper vidmag, see references)
            currAlpha = lambda_/delta/8 - 1
            currAlpha = currAlpha*exaggeration_factor
            # from figure 6 (paper vidmag, see references)
            if currAlpha > alpha:
                filtered[i] = alpha * filtered[i]
            else:
                filtered[i] = currAlpha * filtered[i]
            lambda_ = lambda_/2

        # Laplacian pyramid (contraction)
        for i in range(nlevels-1):
            aux = cv2.pyrUp(filtered[i], dstsize=(int(desired_sizes[nlevels-2-i][1]), int(desired_sizes[nlevels-2-i][0])))
            pyr_contraida = cv2.add(aux, filtered[i+1])

        # Components chrome attenuation
        pyr_contraida[:, :, 1] = pyr_contraida[:, :, 1] * chromAttenuation
        pyr_contraida[:, :, 2] = pyr_contraida[:, :, 2] * chromAttenuation

        # adding contracted pyramid to current frame
        output_frame = pyr_contraida+frame

        # recovering rgb frame
        output_frame = color.yiq2rgb(output_frame)
        output_frame = np.clip(output_frame, a_min=0, a_max=1)
        output_frame = output_frame * 255

        # saving processed frame to output video
        output_video.write(output_frame.astype('uint8'))
        counter = counter + 1

        ### end of WHILE ####

    # release video
    output_video.release()
    input_video.release()

    return output_fullname


def buildlpyr(frame, nlevels, desired_sizes):
    # Gaussian filter
    gauss_layer = frame.copy()
    gpyr = [gauss_layer]
    for i in range(nlevels):
        gauss_layer = cv2.pyrDown(gauss_layer, dstsize=(int(desired_sizes[i+1][1]), int(desired_sizes[i+1][0])))
        gpyr.append(gauss_layer)

    # Laplacian filter
    lpyr = []
    for i in range(nlevels, 0, -1):
        gaussian_extended = cv2.pyrUp(gpyr[i], dstsize=(int(desired_sizes[i-1][1]), int(desired_sizes[i-1][0])))
        lap_layer = cv2.subtract(gpyr[i - 1], gaussian_extended)
        lpyr.append(lap_layer)

    return np.array(lpyr)


def signal_from_ROI(input_fullname):

    # Open video
    vid = cv2.VideoCapture(input_fullname)

    counter = 0
    frameNumber = 0
    amplified_signal = [0, 0]
    length = int(vid.get(cv2.CAP_PROP_FRAME_COUNT))
    FPS = int(vid.get(cv2.CAP_PROP_FPS))
    print("Frames per second: ", FPS)

    temp_cdata = vid.read()

    # ROI selection
    r = cv2.selectROI(temp_cdata[1])
    row_ini = int(r[1])
    row_fin = int(r[1] + r[3])
    cols_ini = int(r[0])
    cols_fin = int(r[0] + r[2])

    # Shows interactive image
    fig = plt.figure()
    ax = fig.add_subplot(111)
    Ln, = ax.plot(amplified_signal)
    plt.axis([0, 1, 0, 0.1])
    ax.set_xlim([0, length+2])
    plt.ion()
    plt.show()

    # Loop
    while vid.isOpened():
        print("Procesando: %.1f%%" % (100 * counter / length))
        temp_cdata = vid.read()
        if temp_cdata[0]:
            # creates ROI and convert to RGB
            temp_BGR_ROI = temp_cdata[1][row_ini:row_fin, cols_ini:cols_fin, :]
            temp_RGB_ROI = cv2.cvtColor(temp_BGR_ROI, cv2.COLOR_BGR2RGB)
            currentFrame_ROI = temp_RGB_ROI.astype('float') / 255

            # Show ROI in video
            cv2.imshow("ROI", temp_BGR_ROI)

            # Reference frame
            if counter == 2:
                RGB_ini_ROI = currentFrame_ROI

            # Creates signal
            if counter > 2:
                diff_ROI_RGB = currentFrame_ROI-RGB_ini_ROI
                # diff_ROI_RGB = np.clip(diff_ROI_RGB, a_min=0, a_max=1)
                diff_ROI_RGB = np.abs(diff_ROI_RGB)
                diff_ROI_YIQ = color.rgb2yiq(diff_ROI_RGB)
                mean_Y = np.mean(diff_ROI_YIQ[:, :, 0])
                amplified_signal = np.append(amplified_signal, mean_Y)

                # shows peaks every 2 seconds
                buffer_length = np.round(2*FPS)
                if frameNumber % buffer_length == 0:
                    # search and draw peaks
                    peaks, _ = find_peaks(amplified_signal[(len(amplified_signal)-buffer_length):len(amplified_signal)],
                                          height=0)
                    plt.plot(len(amplified_signal) - buffer_length + peaks, amplified_signal[len(amplified_signal) -
                                                                                             buffer_length + peaks], "x")

                # Update amplified signal in figure
                Ln.set_ydata(amplified_signal)
                Ln.set_xdata(range(len(amplified_signal)))
                plt.pause(0.01)

                frameNumber = frameNumber+1
        else:
            break

        counter = counter+1
        ### end of WHILE ####

    # Shows remaining peaks in the signal
    peaks, _ = find_peaks(amplified_signal[(len(amplified_signal) - buffer_length):len(amplified_signal)], height=0)
    plt.plot(len(amplified_signal) - buffer_length + peaks, amplified_signal[len(amplified_signal) - buffer_length +
                                                                             peaks], "x")
    plt.pause(5.0)
    # Release video
    vid.release()


def main():
    input_fullname = "../../data/raw/baby.mp4"
    parameters = {
        'alpha': 10,
        'lambda_c': 16,
        'fl': 0.4,
        'fh': 3,
        'samplingRate': 30,
        'chromAttenuation': 0.1,
        'nlevels': 6,
    }

    vidmag_fn(input_fullname, parameters)

    # input_fullname = "..\\data\\raw\\baby.mp4"
    # input_fullname = "..\\data\\processed\\baby-butter-from-0.4-to-3Hz-alpha-10-lambda_c-16-chromAtn-0.1.mp4"
    # signal_from_ROI(input_fullname)


if __name__ == "__main__":
    main()
