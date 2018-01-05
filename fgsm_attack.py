#!/usr/bin/env python3

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

import argparse

import chainer
import chainer.functions as F
import cupy
import numpy as np

from attacks import fgsm
from mlp import MLP

N_gen = 5
img_size = (28, 28)

# argument setting
parser = argparse.ArgumentParser()
parser.add_argument('--gpu', '-g', type=int, default=0, help='GPU ID')
parser.add_argument('--unit', '-u', type=int, default=1000,
                    help='Number of units')
parser.add_argument('--model', default='model/mlp_iter_12000',
                    help='path of already trained model')
args = parser.parse_args()

print('Using gpu ' + str(args.gpu))


def visualize(adv_images, prob, img_size, filename):
    n_images = adv_images.shape[0]
    fig = plt.figure(figsize=(n_images, 1.8))
    gs = gridspec.GridSpec(1, n_images, wspace=0.1, hspace=0.1)
    label = np.argmax(prob, axis=1)
    p = np.max(prob, axis=1)
    for i in range(n_images):
        ax = fig.add_subplot(gs[0, i])
        ax.imshow(adv_images[i].reshape(img_size), cmap='gray',
                  interpolation='none')
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_xlabel('{0} ({1:.2f})'.format(label[i], p[i]), fontsize=12)
        image = plt.subplots()
        image.imshow(adv_images[i].reshape(img_size), cmap='gray',
                     interpolation='none')
        image.set_xticks([])
        image.set_yticks([])
        plt.savefig('fgsm_{0}_{1:.2f}.png'.format(label[i], p[i]))

    gs.tight_layout(fig)
    plt.savefig(filename)


def sample(dataset, n_samples):
    images, _ = test_mnist[np.random.choice(len(dataset), n_samples)]
    images = chainer.cuda.to_gpu(images, args.gpu)
    return images

def main():
    # Setup model, dataset
    model = MLP(args.unit, 10)
    chainer.cuda.get_device_from_id(args.gpu).use()
    model.to_gpu()
    xp = chainer.cuda.get_array_module(model)
    chainer.serializers.load_npz(args.model, model)
    _, test_mnist = chainer.datasets.get_mnist()

    # Fast Gradient Sign Method (simple)
    images = sample(test_mnist, N_gen)
    adv_images, adv_filter = fgsm(model, images, eps=0.2)
    prob = F.softmax(model(adv_images), axis=1).data
    visualize(cupy.asnumpy(adv_images), cupy.asnumpy(prob), img_size, 'fgsm.png')
    visualize(cupy.asnumpy(adv_filter), cupy.asnumpy(prob), img_size, 'fgsm_filter.png')

if __name__ == '__main__':
    main()
