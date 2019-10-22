# Loads an image with the tensorflow input pipeline
import glob
import os
import tensorflow as tf
import hypergan.inputs.resize_image_patch
from tensorflow.python.ops import array_ops
from natsort import natsorted, ns
from hypergan.gan_component import ValidationException, GANComponent

class ImageLoader:
    """
    ImageLoader loads a set of images into a tensorflow input pipeline.
    """

    def __init__(self, batch_size):
        self.batch_size = batch_size

    def tfrecords_create(self, directory, channels=3, width=64, height=64, crop=False, resize=False, sequential=False, random_crop=False):
        filenames = tf.io.gfile.glob(directory+"/*.tfrecord")
        #filenames = [directory]
        filenames = natsorted(filenames)
        print("Found tfrecord files", len(filenames))

        print("[loader] ImageLoader found", len(filenames))
        self.file_count = len(filenames)
        if self.file_count == 0:
            raise ValidationException("No images found in '" + directory + "'")
        filenames = tf.convert_to_tensor(filenames, dtype=tf.string)

        def parse_function(filename):
            def parse_record_tf(record):
                features = tf.parse_single_example(record, features={
                    'image/encoded': tf.io.FixedLenFeature([], tf.string)
                    #'image': tf.FixedLenFeature([], tf.string)
                    })
                #data = tf.decode_raw(features['image'], tf.uint8)
                data = tf.image.decode_jpeg(features['image/encoded'], channels=channels)
                image = tf.image.convert_image_dtype(data, dtype=tf.float32)
                image = tf.cast(data, tf.float32)* (2.0/255)-1.0
                image = tf.reshape(image, [width, height, channels])
                # Image processing for evaluation.
                # Crop the central [height, width] of the image.
                if crop:
                    image = hypergan.inputs.resize_image_patch.resize_image_with_crop_or_pad(image, height, width, dynamic_shape=True)
                elif resize:
                    image = tf.image.resize_images(image, [height, width], 1)

                tf.Tensor.set_shape(image, [height,width,channels])

                return image
            dataset = tf.data.TFRecordDataset(filename, buffer_size=8*1024*1024)
            dataset = dataset.map(parse_record_tf, num_parallel_calls=self.batch_size)

            return dataset
        def set_shape(x):
            x.set_shape(x.get_shape().merge_with(tf.TensorShape([self.batch_size, None, None, None])))
            return x
 
        # Generate a batch of images and labels by building up a queue of examples.
        dataset = tf.data.Dataset.from_tensor_slices(filenames)
        if not sequential:
            print("Shuffling data")
            dataset = dataset.shuffle(self.file_count)
        dataset = dataset.map(parse_function, num_parallel_calls=4)
        dataset = dataset.flat_map(lambda x: x.batch(self.batch_size, drop_remainder=True).repeat().prefetch(1))
        dataset = dataset.repeat().prefetch(1)
        dataset = dataset.map(set_shape)

        self.dataset = dataset
        return dataset


    def tfrecord_create(self, directory, channels=3, width=64, height=64, crop=False, resize=False, sequential=False, random_crop=False):
        #filenames = tf.io.gfile.glob(directory+"/*.tfrecord")
        filenames = [directory]
        filenames = natsorted(filenames)
        print("Found tfrecord files: ", len(filenames))

        print("[loader] ImageLoader found", len(filenames))
        self.file_count = len(filenames)
        if self.file_count == 0:
            raise ValidationException("No images found in '" + directory + "'")
        filenames = tf.convert_to_tensor(filenames, dtype=tf.string)

        def parse_function(filename):
            def parse_record_tf(record):
                features = tf.parse_single_example(record, features={
                    #'image/encoded': tf.FixedLenFeature([], tf.string)
                    'image': tf.io.FixedLenFeature([], tf.string)
                    })
                data = tf.decode_raw(features['image'], tf.uint8)
                #data = tf.image.decode_jpeg(features['image/encoded'], channels=channels)
                image = tf.image.convert_image_dtype(data, dtype=tf.float32)
                image = tf.cast(data, tf.float32)* (2.0/255)-1.0
                image = tf.reshape(image, [width, height, channels])
                # Image processing for evaluation.
                # Crop the central [height, width] of the image.
                if crop:
                    image = hypergan.inputs.resize_image_patch.resize_image_with_crop_or_pad(image, height, width, dynamic_shape=True)
                elif resize:
                    image = tf.image.resize_images(image, [height, width], 1)

                tf.Tensor.set_shape(image, [height,width,channels])

                return image
            dataset = tf.data.TFRecordDataset(filename, buffer_size=8*1024*1024)
            dataset = dataset.map(parse_record_tf, num_parallel_calls=self.batch_size)

            return dataset
        def set_shape(x):
            x.set_shape(x.get_shape().merge_with(tf.TensorShape([self.batch_size, None, None, None])))
            return x
 
        # Generate a batch of images and labels by building up a queue of examples.
        dataset = tf.data.Dataset.from_tensor_slices(filenames)
        if not sequential:
            print("Shuffling data")
            dataset = dataset.shuffle(self.file_count)
        dataset = dataset.map(parse_function, num_parallel_calls=4)
        dataset = dataset.flat_map(lambda x: x.batch(self.batch_size, drop_remainder=True).repeat().prefetch(1))
        dataset = dataset.repeat().prefetch(1)
        dataset = dataset.map(set_shape)

        self.dataset = dataset
        return dataset


    def create(self, directories, channels=3, format='jpg', width=64, height=64, crop=False, resize=False, sequential=False, random_crop=False):
        directory = directories[0]
        if format == 'tfrecord':
            return self.tfrecord_create(directory, channels=channels, width=width, height=height, crop=crop, resize=resize, sequential=sequential, random_crop=random_crop)
        if format == 'tfrecords':
            return self.tfrecords_create(directory, channels=channels, width=width, height=height, crop=crop, resize=resize, sequential=sequential, random_crop=random_crop)
        if format == 'jpg' or format == 'png':
            return self.image_folder_create(directories, channels=channels, width=width, height=height, crop=crop, resize=resize, sequential=sequential, random_crop=random_crop, format=format)

        raise ValidationError("Format not supported.  Only jpg,png,tfrecord,tfrecords are supported")


    def image_folder_create(self, directories, channels=3, format='jpg', width=64, height=64, crop=False, resize=False, sequential=False, random_crop=False):
        self.datasets = []

        print("CREATING WITH", directories)
        if(not isinstance(directories, list)):
            directories = [directories]

        for directory in directories:
            dirs = glob.glob(directory+"/*")
            dirs = [d for d in dirs if os.path.isdir(d)]

            if(len(dirs) == 0):
                dirs = [directory] 

            # Create a queue that produces the filenames to read.
            if(len(dirs) == 1):
                # No subdirectories, use all the images in the passed in path
                filenames = glob.glob(directory+"/*."+format)
                print("GLOB", directory+"/*."+format)
            else:
                filenames = glob.glob(directory+"/**/*."+format)
                print("GLOB", directory+"/**/*."+format)

            filenames = natsorted(filenames)

            print("[loader] ImageLoader found", len(filenames))
            self.file_count = len(filenames)
            if self.file_count == 0:
                raise ValidationException("No images found in '" + directory + "'")
            filenames = tf.convert_to_tensor(filenames, dtype=tf.string)

            def parse_function(filename):
                image_string = tf.read_file(filename)
                if format == 'jpg':
                    image = tf.image.decode_jpeg(image_string, channels=channels)
                elif format == 'png':
                    image = tf.image.decode_png(image_string, channels=channels)
                else:
                    print("[loader] Failed to load format", format)
                image = tf.cast(image, tf.float32)
                # Image processing for evaluation.
                # Crop the central [height, width] of the image.
                if crop:
                    image = hypergan.inputs.resize_image_patch.resize_image_with_crop_or_pad(image, height, width, dynamic_shape=True)
                elif resize:
                    image = tf.image.resize_images(image, [height, width], 1)
                elif random_crop:
                    image = tf.image.random_crop(image, [height, width, channels], 1)

                image = image / 127.5 - 1.
                tf.Tensor.set_shape(image, [height,width,channels])

                return image

            # Generate a batch of images and labels by building up a queue of examples.
            dataset = tf.data.Dataset.from_tensor_slices(filenames)
            if not sequential:
                print("Shuffling data")
                dataset = dataset.shuffle(self.file_count)
            dataset = dataset.map(parse_function, num_parallel_calls=4)
            dataset = dataset.batch(self.batch_size, drop_remainder=True)

            dataset = dataset.repeat()
            dataset = dataset.prefetch(1)

            self.datasets.append(tf.reshape(dataset.make_one_shot_iterator().get_next(), [self.batch_size, height, width, channels]))

        self.xs = self.datasets
        self.xa = self.datasets[0]
        if len(self.datasets) > 1:
            self.xb = self.datasets[1]
        self.x = self.datasets[0]
        return self.xs


    def inputs(self):
        return [self.x,self.x]

    def layer(self, name):
        if name == "x":
            return self.x
        return None
