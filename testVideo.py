import argparse

import cv2
import numpy as np
import torch
import torchvision.transforms as transforms
from PIL import Image
from torch.autograd import Variable
from torchvision.transforms import ToTensor, ToPILImage
from tqdm import tqdm
import FRVSR

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test Single Video')
    parser.add_argument('--video', type=str, help='test low resolution video name')
    parser.add_argument('--model', type=str, help='generator model epoch name')
    opt = parser.parse_args()

    UPSCALE_FACTOR = 4
    VIDEO_NAME = opt.video
    MODEL_NAME = opt.model

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    model = FRVSR.FRVSR(0, 0, 0).eval()

    model.to(device)

    # for cpu
    # model.load_state_dict(torch.load('epochs/' + MODEL_NAME, map_location=lambda storage, loc: storage))
    model.load_state_dict(torch.load(MODEL_NAME, device))
    model.eval()

    videoCapture = cv2.VideoCapture(VIDEO_NAME)
    fps = videoCapture.get(cv2.CAP_PROP_FPS)
    frame_numbers = videoCapture.get(cv2.CAP_PROP_FRAME_COUNT)
    # frame_numbers = 100
    lr_width = int(videoCapture.get(cv2.CAP_PROP_FRAME_WIDTH))
    lr_height = int(videoCapture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    model.set_param(batch_size=1, width=lr_width, height=lr_height)
    model.init_hidden(device)

    sr_video_size = (int(videoCapture.get(cv2.CAP_PROP_FRAME_WIDTH) * UPSCALE_FACTOR),
                     int(videoCapture.get(cv2.CAP_PROP_FRAME_HEIGHT)) * UPSCALE_FACTOR)

    output_sr_name = 'out_srf_' + str(UPSCALE_FACTOR) + '_' + VIDEO_NAME.split('.')[0] + '.mp4'
    sr_video_writer = cv2.VideoWriter(output_sr_name, cv2.VideoWriter_fourcc('M', 'P', 'E', 'G'), fps, sr_video_size)

    # read frame
    success, frame = videoCapture.read()
    test_bar = tqdm(range(int(frame_numbers)), desc='[processing video and saving result videos]')
    for index in test_bar:
        if success:
            image = Variable(ToTensor()(frame), volatile=True).unsqueeze(0)
            image.to(device)
            # print(f'image shape is {image.shape}')
            # if torch.cuda.is_available():
            #     image = image.cuda()

            hr_out, lr_out = model(image)
            model.init_hidden(device)
            hr_out = hr_out.cpu()
            out_img = hr_out.data[0].numpy()
            out_img *= 255.0
            out_img = (np.uint8(out_img)).transpose((1, 2, 0))
            # save sr video
            sr_video_writer.write(out_img)

            # next frame
            success, frame = videoCapture.read()
    sr_video_writer.release()