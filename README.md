# User Guide

After miniconda/anaconda installation you need to install [**Keras**](https://keras.io/) package. To be able to save models the latest keras version is needed:
```bash
pip install --upgrade --no-deps keras
```
The enviroment yaml file has been defined in data directory.

```bash
conda env create -f data/vae_env.yml
source activate env_vae
```



## Note

To be able to have interactive 3D plots in this notebook, matplotlib backend has been changed. To transfer this notebook to publication ready quality one can change the matplotlib setting and define nested subplot.
