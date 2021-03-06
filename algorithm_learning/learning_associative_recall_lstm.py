# -*- coding: utf-8 -*-
"""An implementation of learning associative recall algorithm_learning with LSTM.
Input sequence length: "2 ~ 6 items: (2*(3+1) ~ 6*(3+1))."
Input dimension: "6+2", Item 3*6 bits
Output sequence length: "3" one item .
Output dimension: equal to input dimension.
"""

from __future__ import print_function
from keras.models import Sequential
from keras.layers import Activation, TimeDistributed, Dense, recurrent
import numpy as np
# from six.moves import range
# from keras.layers import RepeatVector
# from keras.engine.training import slice_X
# from keras.callbacks import Callback       # Add by Steven Robot
from keras.callbacks import ModelCheckpoint  # Add by Steven Robot
from keras.utils.visualize_util import plot  # Add by Steven Robot
from keras.optimizers import Adam            # Add by Steven Robot
from util import LossHistory                 # Add by Steven Robot
from keras.callbacks import LambdaCallback   # Add by Steven Robot
import dataset                               # Add by Steven Robot
import time                                  # Add by Steven Robot
import os                                    # Add by Steven Robot
import sys                                   # Add by Steven Robot
import matplotlib.pyplot as plt
import visualization


# Parameters for the model to train copying algorithm_learning
# TRAINING_SIZE = 1024000
TRAINING_SIZE = 10240
# TRAINING_SIZE = 128000
# TRAINING_SIZE = 1280
INPUT_DIMENSION_SIZE = 6
ITEM_SIZE = 3
MAX_EPISODE_SIZE = 6
MAX_INPUT_LENGTH = (ITEM_SIZE+1) * (MAX_EPISODE_SIZE+2)


# Try replacing SimpleRNN, GRU, or LSTM
# RNN = recurrent.SimpleRNN
# RNN = recurrent.GRU
RNN = recurrent.LSTM
HIDDEN_SIZE = 256
LAYERS = 2
# LAYERS = MAX_REPEAT_TIMES
BATCH_SIZE = 1024
# BATCH_SIZE = 128

folder_name = time.strftime('experiment_results/recall_lstm/%Y-%m-%d-%H-%M-%S/')
# os.makedirs(folder_name)
FOLDER = folder_name
if not os.path.isdir(FOLDER):
    os.makedirs(FOLDER)
    print("create folder: %s" % FOLDER)

start_time = time.time()
sys_stdout = sys.stdout
log_file = '%s/recall.log' % (folder_name)
sys.stdout = open(log_file, 'a')

print()
print(time.strftime('%Y-%m-%d %H:%M:%S'))
print('Generating data sets...')
train_X, train_Y = dataset.generate_associative_recall_data_set(
        INPUT_DIMENSION_SIZE, ITEM_SIZE, MAX_EPISODE_SIZE, TRAINING_SIZE)
valid_X, valid_Y = dataset.generate_associative_recall_data_set(
        INPUT_DIMENSION_SIZE, ITEM_SIZE, MAX_EPISODE_SIZE, TRAINING_SIZE/5)

matrix_list = []
matrix_list.append(train_X[0].transpose())
matrix_list.append(train_Y[0].transpose())
matrix_list.append(train_Y[0].transpose())
name_list = []
name_list.append("Input")
name_list.append("Target")
name_list.append("Predict")
show_matrix = visualization.PlotDynamicalMatrix(matrix_list, name_list)
random_index = np.random.randint(1, 128, 20)
for i in range(20):
    matrix_list_update = []
    matrix_list_update.append(train_X[random_index[i]].transpose())
    matrix_list_update.append(train_Y[random_index[i]].transpose())
    matrix_list_update.append(train_Y[random_index[i]].transpose())
    show_matrix.update(matrix_list_update, name_list)
    show_matrix.save(FOLDER+"associative_recall_data_training_%2d.png" % i)

print()
print(time.strftime('%Y-%m-%d %H:%M:%S'))
print('Build model...')
model = Sequential()
# "Encode" the input sequence using an RNN, producing an output of HIDDEN_SIZE
# note: in a situation where your input sequences have a variable length,
# use input_shape=(None, nb_feature).
model.add(RNN(
    HIDDEN_SIZE,
    input_shape=(MAX_INPUT_LENGTH, INPUT_DIMENSION_SIZE+2),
    init='glorot_uniform',
    inner_init='orthogonal',
    activation='tanh',
    return_sequences=True,
    # activation='hard_sigmoid',
    # activation='sigmoid',
    W_regularizer=None,
    U_regularizer=None,
    b_regularizer=None,
    dropout_W=0.0,
    dropout_U=0.0))

# For the decoder's input, we repeat the encoded input for each time step
# model.add(RepeatVector(MAX_INPUT_LENGTH))
# The decoder RNN could be multiple layers stacked or a single layer
for _ in range(LAYERS):
    model.add(RNN(HIDDEN_SIZE, return_sequences=True))

# For each of step of the output sequence, decide which character should be chosen
model.add(TimeDistributed(Dense(INPUT_DIMENSION_SIZE+2)))
# model.add(Activation('softmax'))
# model.add(Activation('hard_sigmoid'))
model.add(Activation('sigmoid'))

# initialize the optimizer
lr = 0.0001
beta_1 = 0.9
beta_2 = 0.999
epsilon = 1e-8
ADAM_ = Adam(lr=lr, beta_1=beta_1, beta_2=beta_2, epsilon=epsilon)

# compile the model
model.compile(loss='binary_crossentropy',
              # loss='mse',
              # optimizer='adam',
              optimizer=ADAM_,
              metrics=['accuracy'])

# show the information of the model
print()
print(time.strftime('%Y-%m-%d %H:%M:%S'))
print("Model architecture")
plot(model, show_shapes=True, to_file=FOLDER+"lstm_associative_recall.png")
print("Model summary")
print(model.summary())
print("Model parameter count")
print(model.count_params())

# begain training
print()
print(time.strftime('%Y-%m-%d %H:%M:%S'))
print("Training...")
# Train the model each generation and show predictions against the
# validation dataset
losses = []
acces = []
for iteration in range(1, 3):
    print()
    print('-' * 78)
    print(time.strftime('%Y-%m-%d %H:%M:%S'))
    print('Iteration', iteration)
    history = LossHistory()
    plot_loss_callback = LambdaCallback(
        on_epoch_end=lambda epoch, logs:
        plt.plot(np.arange((epoch, 1)), logs['loss']))
    check_pointer = ModelCheckpoint(
        filepath=FOLDER+"associative_recall_model_weights.hdf5",
        verbose=1, save_best_only=True)
    model.fit(train_X,
              train_Y,
              batch_size=BATCH_SIZE,
              # nb_epoch=30,
              nb_epoch=10,
              callbacks=[check_pointer, history, plot_loss_callback],  #, plot_loss_callback
              validation_data=(valid_X, valid_Y))
    # print(len(history.losses))
    # print(history.losses)
    # print(len(history.acces))
    # print(history.acces)
    losses.append(history.losses)
    acces.append(history.acces)

    ###
    # Select 20 samples from the validation set at random so we can
    # visualize errors
    for i in range(20):
        ind = np.random.randint(0, len(valid_X))
        inputs, outputs = valid_X[np.array([ind])], \
                                  valid_Y[np.array([ind])]
        predicts = model.predict(inputs, verbose=0)
        matrix_list_update = []
        matrix_list_update.append(inputs[0].transpose())
        matrix_list_update.append(outputs[0].transpose())
        matrix_list_update.append(predicts[0].transpose())
        show_matrix.update(matrix_list_update,
                           name_list)
        show_matrix.save(FOLDER+"associative_data_predict_%2d_%2d.png" % (iteration, i))

show_matrix.close()
# end of training

# print loss and accuracy
print("\nlosses")
print(len(losses))
print(len(losses[0]))
# print(losses.shape)
sample_num = 1
for los in losses:
    for lo in los:
        if sample_num % 100 == 1:
            print("(%d, %f)" % (sample_num, lo))
        sample_num = sample_num + 1
# print(losses)

print("********************************************")
print("\naccess")
print(len(acces))
print(len(acces[0]))
# print(acces.shape)
sample_num = 1
for acc in acces:
    for ac in acc:
        if sample_num % 100 == 1:
            print("(%d, %f)" % (sample_num, ac))
        sample_num = sample_num + 1
# print(acces)

# print loss and accuracy
print("\nlosses")
print(len(losses))
print(len(losses[0]))
# print(losses.shape)
sample_num = 1
for los in losses:
    for lo in los:
        print("(%d, %f)" % (sample_num, lo))
        sample_num = sample_num + 1
# print(losses)

print("********************************************")
print("\naccess")
print(len(acces))
print(len(acces[0]))
# print(acces.shape)
sample_num = 1
for acc in acces:
    for ac in acc:
        print("(%d, %f)" % (sample_num, ac))
        sample_num = sample_num + 1
# print(acces)

print ("task took %.3fs" % (float(time.time()) - start_time))
sys.stdout.close()
sys.stdout = sys_stdout
