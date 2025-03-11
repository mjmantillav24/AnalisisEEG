import mne
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
class EEG_CNN(nn.Module):
    def __init__(self, num_classes=4):
        super(EEG_CNN, self).__init__()
        self.conv1 = nn.Conv2d(1, 32, kernel_size=(3, 5), padding=(1, 2))
        self.conv2 = nn.Conv2d(32, 64, kernel_size=(3, 5), padding=(1, 2))
        self.conv3 = nn.Conv2d(64, 128, kernel_size=(3, 5), padding=(1, 2))
        self.pool = nn.MaxPool2d(kernel_size=(2, 2))

        self.flatten_size = 128 * 2 * 62
        self.fc1 = nn.Linear(self.flatten_size, 512)
        self.fc2 = nn.Linear(512, num_classes)

    def forward(self, x):
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = self.pool(F.relu(self.conv3(x)))

        x = torch.flatten(x, start_dim=1)
        x = F.relu(self.fc1(x))
        x = self.fc2(x)
        return x  

def preprocess(path: str):
  channels_to_remove = ['EEG Cz-Ref', 'EEG Pz-Ref', 'ECG EKG', 'Manual']
  data = mne.io.read_raw_edf(path, preload=True)
  channels = data.ch_names
  indices_to_remove = [i for i, ch in enumerate(channels) if ch in channels_to_remove]
  raw_data = data.get_data()
  raw_data = np.array(raw_data)
  while raw_data.shape[0] >19 and len(indices_to_remove)>0:
    raw_data = np.delete(raw_data, indices_to_remove[-1], axis=0)
    indices_to_remove.pop()
  if raw_data.shape[0] >19:
    raw_data = raw_data[:19, :]
  elif raw_data.shape[0] <19:
    raw_data = np.vstack((raw_data, raw_data[:(19-len(raw_data.shape)[0]), :]))
  raw_data = np.array(raw_data)
  num_samples = raw_data.shape[1]
  print(num_samples)
  segment_size = 500
  N = num_samples // segment_size
  segmented_data = raw_data[:, :N * segment_size].reshape(N, 19, 500)
  tensor_data = torch.tensor(segmented_data, dtype=torch.float32)
  return tensor_data

def predecir(modelo, entrada):

    modelo.eval()
    with torch.no_grad(): 
        salida = modelo(entrada)
        prediccion = torch.argmax(salida, dim=1)  
    return prediccion.item()

def iniciar(path: str):
  data=preprocess(path)
  modelo_cargado = torch.load("/content/modelo_completo.pth")#path del modelo
  salida=[]
  for i in range(data.shape[0]):
    salida.append( predecir(modelo_cargado, data[i].unsqueeze(0).unsqueeze(0) ))

  if sum(salida)>0:
    return '"Se detecta epilepsia en EEG'
  else:
    return 'No se detecta epilepsia en EEG'
print(iniciar('/content/p11_Record3.edf'))#path del archivo a analizar