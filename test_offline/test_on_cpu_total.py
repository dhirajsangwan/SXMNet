import torch
import torchvision.transforms as transforms

import json

import sys
sys.path.append('../')

from tqdm import tqdm
from baseline import My_Counting_Net_Insight_Gated
from folder import MyFolder

import os

os.environ["CUDA_VISIBLE_DEVICES"] = '2'


object_categories = ['battery', 'bottle', 'firecracker', 'grenade', 'gun', 'hammer', 'knife', 'scissors']

model_path = '224_resnet50.ckpt'

test_set_path = '/data0/hby/datasets/Top_View_Xray/total_test_imgs'

result_save_path = 'test.json'


def prepare_data(test_set_path):
    normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                     std=[0.229, 0.224, 0.225])
    test_transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        normalize,
        ])
    test_folder = MyFolder(test_set_path, transform=test_transform)
    test_loader = torch.utils.data.DataLoader(
        test_folder,
        batch_size=64, shuffle=False,
        num_workers=4, pin_memory=True)
    return test_loader


def eval_model(test_loader, model):
    model.eval()
    pred_list = []
    target_list = []
    info_dicts = list()

    with torch.no_grad():
        for batch_idx, (data, target, path) in tqdm(enumerate(test_loader), desc='Testing'):

            if torch.cuda.is_available():
                data = data.cuda()
                target = target.cuda()
            logit = model(data)

            pred = torch.sigmoid(logit)

            for i in range(data.shape[0]):
                info_dict = dict()
                info_dict['img_name'] = path[i].split('/')[-1]
                info_dict['label'] = target[i].tolist()
                info_dict['pred'] = pred[i].cpu().numpy().tolist()
                info_dicts.append(info_dict)

    with open(result_save_path, 'w') as f:
        json.dump(info_dicts, f)


def main():
    print('--- start evalute ---')

    # Training data config
    test_loader = prepare_data(test_set_path)

    # Init model
    model = My_Counting_Net_Insight_Gated(num_classes=len(object_categories), backbone='resnet101')
    if torch.cuda.is_available():
        model = model.cuda()
    checkpoint = torch.load(model_path, map_location='cpu')
    model.load_state_dict(checkpoint['state_dict'])

    # Save wrong cases
    eval_model(test_loader, model)


if __name__ == "__main__":
    main()
