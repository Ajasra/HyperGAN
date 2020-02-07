import hyperchamber as hc

from hypergan.losses.base_loss import BaseLoss

class WassersteinLoss(BaseLoss):

    def _forward(self, d_real, d_fake):
        config = self.config

        d_loss = -d_real + d_fake
        g_loss = -d_fake

        if config.kl:
            # https://arxiv.org/abs/1910.09779
            loss_real = tf.reduce_mean(tf.nn.relu(1.-d_real))
            d_fake_norm = tf.reduce_mean(tf.math.exp(d_fake))+1e-8
            d_fake_ratio = (tf.math.exp(d_fake)+1e-8) / d_fake_norm
            loss_fake = d_fake * d_fake_ratio
            loss_fake = tf.reduce_mean(tf.nn.relu(1.+loss_fake))
            d_loss = loss_real + loss_fake
            g_loss = -loss_fake

        return [d_loss, g_loss]
