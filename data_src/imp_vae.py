from __future__ import division, absolute_import
from __future__ import print_function, unicode_literals

import numpy as np
from functools import partial



from keras.models import Model
from keras.layers import Dense, Input, Activation, Dropout, Lambda, initializers
import keras.backend as K
from keras.datasets import mnist
from keras import optimizers

class VAE:    
    Default = {'h_encod' : [],
               'h_decod': None,
               'drop':  [],
               'act_f' : 'relu', 
               'optimiz' : 'rmsprop',
               'inp_shape' : None,
               'lr_rate' : 0.01}

    
    def __init__(self, hyper_p = {}):
        
        self.__dict__.update(self.Default, **hyper_p)
        
        if K.backend() != 'tensorflow':
            print('backend is ', K.backend())
            
        self.init_method = initializers.RandomNormal(mean=0.0,
                                                     stddev=0.05,
                                                     seed=None)
        
        # load piplines of 2 conected models
        self.recognition = self.encoder()
        self.generator = self.decoder()

        # define main network inputs
        input =  Input(shape=(self.inp_shape,),
                       dtype = 'float32',
                       name='VAE_input')
        mask_input = Input(shape=(self.inp_shape,),
                           dtype = 'float32',
                           name='mask_input')

        
        self.z_mu, self.z_var = self.recognition(input)
        vae_out = self.generator([self.z_mu, self.z_var])

        ## generate vae_model by conecting recognition_model to generator_model
        self.vae_model = Model(inputs = [input, mask_input], outputs = vae_out, name = 'VAE') 

        
        custom_loss =  partial(self.custom_loss,  mask_input)
        custom_loss.__name__ = "masked_bce"

        

        
        method = getattr(optimizers, self.optimiz)
        self.vae_model.compile(optimizer = method(lr = self.lr_rate),
                               loss = custom_loss)
                               #,metrics=[metrics.mae, metrics.categorical_accuracy])   
       
       
        
        #self.vae_model.summary()

         

    def encoder(self):
        """ recognition model """

        X =  Input(shape=(self.inp_shape,),dtype = 'float32', name='encoder_input')
        inp = X
        
        hlay = self.h_encod
        if len(hlay)>1 :
            for i,layer in enumerate(hlay[:-1]):
                X = Dense(layer, 
                          activation = self.act_f, 
                          use_bias=True,
                          kernel_initializer = self.init_method,
                          bias_initializer = self.init_method,
                          name = 'encoder_{}'.format(i))(X)

                X = Dropout(self.drop[i])(X)            

       
        z_mu =  Dense(hlay[-1],  name = 'z_mu')(X)
        z_var = Dense(hlay[-1],  name = 'z_sigma')(X)

        recognition = Model(inputs = inp,  outputs = [z_mu, z_var], name = 'recognition' )
        #recognition.summary()
        return recognition

  

    

    def decoder(self):
        """ generative model """
        
        dec_layer = []
        if self.h_decod == None :
            hlayer = list(reversed(self.h_encod))
        else:
            hlayer = self.h_decod


        mu_input = Input(shape=( hlayer[0], ),dtype = 'float32', name='mu_input')
        sig_input = Input(shape=( hlayer[0], ),dtype = 'float32', name='sig_input')

        def z(arg):
            z_mu, z_var = arg
            epsilon = K.random_normal(shape = (K.shape(z_mu)[0], hlayer[0] ),
                                      mean = 0.,
                                      stddev = 1.)
            return z_mu + K.exp(z_var / 2) * epsilon
        
        #########################################################################
        ########################################################################
        X =  Lambda(z,  output_shape=( hlayer[0],))([mu_input, sig_input  ])
        
        if len(hlayer) > 1:
            for j,layer in enumerate(hlayer):
                if j == 0: 
                    pass
                elif j == len(hlayer)-1:
                    d = Dense(layer,
                              activation = self.act_f, 
                              use_bias=True,
                              kernel_initializer= self.init_method,
                              bias_initializer = self.init_method,
                              name = 'decoder_{}'.format(j))
                    dec_layer.append(d)
                    X = d(X)
                    X =  Dropout(self.drop[j])(X)

                    # maps onto a bernoulli dist. in data space
                    d = Dense(self.inp_shape, 
                              activation = 'sigmoid', 
                              use_bias=True,
                              kernel_initializer= self.init_method,
                              bias_initializer = self.init_method,
                              name = 'reconstruct_layer')
                    dec_layer.append(d)
                    X = d(X)
                else:

                    d = Dense(layer, 
                              activation = self.act_f, 
                              use_bias=True,
                              kernel_initializer = self.init_method,
                              bias_initializer = self.init_method,
                              name = 'decoder_{}'.format(j))
                    dec_layer.append(d)
                    X = d(X)

                    X = Dropout(self.drop[j])(X)
        else:
            # maps onto a bernoulli dist. in data space
            d = Dense(self.inp_shape, 
                      activation = 'sigmoid', 
                      use_bias=True,
                      kernel_initializer= self.init_method,
                      bias_initializer = self.init_method,
                      name = 'reconstruct_layer')
            dec_layer.append(d)
            X = d(X)
            
            
                
        self.dec_layer = dec_layer

        generator = Model(inputs = [mu_input, sig_input ], outputs = X, name = 'generator' )
        #generator.summary()
        
        return generator


    
    def custom_loss(self, mask, x, x_pred):
        z_var = self.z_var
        z_mu = self.z_mu

        
        metrr = K.binary_crossentropy(x, x_pred) * mask
        expected_recons = K.sum(metrr, axis=-1)
        KL_d =  - 0.5 * K.sum(1 + z_var - K.square(z_mu) - K.exp(z_var), axis=-1)
        return K.mean(expected_recons + KL_d)


