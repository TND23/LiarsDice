import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import os

class LinearNet(nn.Module):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def forward(self, X):
        pass

    def persist(self, file_name, path):
        if not os.path.exists(path):
            os.mkdirs(path)
        
        f = os.path.join(path, file_name)
        torch.save(self.state_dict(), f)

    